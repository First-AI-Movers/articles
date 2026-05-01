#!/usr/bin/env python3
"""Generate translation review files and apply approved translations.

Mirrors the E35 summaries workflow: draft review files -> human review or AI QA ->
approved -> article.<lang>.md sidecars. Supports both human-reviewed and AI-QA-approved translations.

Usage:
    python3 tools/translate_articles.py --dry-run --slug XYZ --lang es --provider mock
    python3 tools/translate_articles.py --write-review-files --slug XYZ --lang es --provider mock
    python3 tools/translate_articles.py --write-review-files --slug XYZ --provider deepl --allow-network
    python3 tools/translate_articles.py --apply-approved --slug XYZ --lang es
"""

import argparse
import json
import os
import re
import sys
from datetime import date
import time
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = REPO_ROOT / "articles"
INDEX_PATH = REPO_ROOT / "index.json"
GLOSSARY_PATH = REPO_ROOT / "tools" / "translation_glossary.json"

SITE_BASE = "https://articles.firstaimovers.com"
DEFAULT_LANGS = ["es", "fr", "de", "nl", "pt"]

LANG_NAMES = {
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "nl": "Dutch",
    "pt": "Portuguese",
}


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
def _build_argparser():
    parser = argparse.ArgumentParser(description="Generate article translations.")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Preview without writes or network calls (default).")
    parser.add_argument("--write-review-files", action="store_true",
                        help="Generate and write review files.")
    parser.add_argument("--apply-approved", action="store_true",
                        help="Apply approved review files to create article.<lang>.md.")
    parser.add_argument("--provider", type=str, default="mock",
                        choices=["mock", "manual", "deepl"],
                        help="Translation backend.")
    parser.add_argument("--slug", type=str, default=None,
                        help="Target a single article by slug.")
    parser.add_argument("--lang", type=str, default=",".join(DEFAULT_LANGS),
                        help="Comma-separated language codes (default: es,fr,de,nl,pt).")
    parser.add_argument("--allow-network", action="store_true",
                        help="Required for real DeepL calls.")
    parser.add_argument("--translations-dir", type=str, default="translations/reviews",
                        help="Output directory for review files.")
    parser.add_argument("--glossary", type=str, default=str(GLOSSARY_PATH),
                        help="Path to glossary JSON.")
    parser.add_argument("--quota-safety-margin", type=int, default=5000,
                        help="Safety margin in chars before refusing translation (default: 5000).")
    parser.add_argument("--ignore-quota-safety-margin", action="store_true",
                        help="Ignore the safety margin (hard quota limit still enforced).")
    return parser


# ---------------------------------------------------------------------------
# Index loading
# ---------------------------------------------------------------------------
def _load_index():
    if not INDEX_PATH.exists():
        print(f"[translate] index.json not found at {INDEX_PATH}", file=sys.stderr)
        sys.exit(1)
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Glossary loading
# ---------------------------------------------------------------------------
def _load_glossary(path: Path):
    if not path.exists():
        print(f"[translate] Glossary not found: {path}", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Article reading
# ---------------------------------------------------------------------------
def _read_article_body(folder):
    md_path = ARTICLES_DIR / folder / "article.md"
    if not md_path.exists():
        return ""
    text = md_path.read_text(encoding="utf-8", errors="replace")
    # Strip front matter
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            text = parts[2]
    return text.lstrip()


def _char_count(text):
    return len(text)


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------
def _build_prompt(article_text, lang, glossary_terms):
    lang_name = LANG_NAMES.get(lang, lang)
    glossary_section = ""
    if glossary_terms:
        glossary_section = "\nMandatory terminology (use these exact translations):\n"
        for term, translation in glossary_terms.items():
            glossary_section += f"  - {term} -> {translation}\n"

    return (
        f"Translate the following article into {lang_name} ({lang}).\n"
        f"Preserve all Markdown formatting including headings, lists, bold, and links.{glossary_section}"
        "\nDo not invent facts, numbers, citations, or quotes that are not in the source.\n"
        "Do not add or remove sections.\n"
        "Translate the title as the first line, prefixed with '# '.\n\n"
        "Article:\n---\n"
        f"{article_text}\n"
        "---\n"
    )


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------
def _provider_mock(article_text, lang, model=None):
    """Deterministic synthetic translation for testing. No API key needed."""
    lang_name = LANG_NAMES.get(lang, lang)
    words = article_text.split()[:30]
    snippet = " ".join(words) if words else "This article discusses important AI strategy topics."
    # Generate a mock title and body that clearly signals it's not a real translation
    title = f"[MOCK {lang.upper()}] {lang_name} translation placeholder"
    body = (
        f"# {title}\n\n"
        f"> **MOCK TRANSLATION** — This is a synthetic placeholder for workflow testing.\n\n"
        f"{snippet}\n\n"
        f"This mock translation in {lang_name} is generated deterministically for testing the "
        f"translation workflow. It does not represent an actual translation and should not be "
        f"used as editorial content.\n\n"
        f"## Mock Section\n\n"
        f"Placeholder text in {lang_name} for workflow validation.\n"
    )
    return body


def _provider_manual(article_text, lang, model=None):
    print("[translate] Manual provider: paste translation in review-file format.", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# DeepL quota and usage helpers
# ---------------------------------------------------------------------------
def fetch_deepl_usage(api_key: str, api_base: str) -> dict:
    """Call DeepL /v2/usage and return {character_count, character_limit}."""
    url = f"{api_base}/usage"
    headers = {"Authorization": f"DeepL-Auth-Key {api_key}"}
    try:
        resp = requests.get(url, headers=headers, timeout=30)
    except requests.RequestException as e:
        print(f"[translate] ERROR: Failed to fetch DeepL usage: {e}", file=sys.stderr)
        sys.exit(1)

    if resp.status_code != 200:
        print(f"[translate] ERROR: DeepL usage API returned {resp.status_code}", file=sys.stderr)
        sys.exit(1)

    try:
        data = resp.json()
    except json.JSONDecodeError as e:
        print(f"[translate] ERROR: DeepL usage response is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    return {
        "character_count": data.get("character_count", 0),
        "character_limit": data.get("character_limit", 0),
    }


def _check_deepl_quota(api_key: str, projected_chars: int, safety_margin: int, ignore_margin: bool) -> dict:
    """Fetch usage and abort if remaining quota is insufficient.

    Returns usage dict if sufficient. Exits with message if not.
    """
    usage = fetch_deepl_usage(api_key, DEEPL_API_BASE)
    limit = usage["character_limit"]
    used = usage["character_count"]
    remaining = limit - used
    effective_margin = 0 if ignore_margin else safety_margin
    required = projected_chars + effective_margin

    if remaining < required:
        print(
            f"[translate] ERROR: Insufficient DeepL quota: "
            f"projected {projected_chars:,} chars + margin {effective_margin:,} = {required:,} chars required, "
            f"remaining {remaining:,} chars.",
            file=sys.stderr,
        )
        sys.exit(1)

    return usage


def _chunk_text_for_deepl(text: str, max_bytes: int = None) -> list:
    if max_bytes is None:
        max_bytes = DEEPL_CHUNK_TARGET_BYTES
    """Split text into chunks that stay under max_bytes when UTF-8 encoded.

    Splits on paragraph boundaries (blank lines) to preserve Markdown structure.
    Falls back to sentence boundaries if a single paragraph is too large.
    Never splits inside code fences.
    """
    chunks = []
    current_lines = []
    current_bytes = 0
    in_fence = False
    fence_type = None

    def _flush():
        nonlocal current_lines, current_bytes
        if current_lines:
            chunks.append("\n".join(current_lines))
            current_lines = []
            current_bytes = 0

    lines = text.splitlines()
    for line in lines:
        # Track code fences
        fence_match = re.match(r"^(```+|~~~+)", line)
        if fence_match:
            if not in_fence:
                in_fence = True
                fence_type = fence_match.group(1)
            elif line.startswith(fence_type):
                in_fence = False
                fence_type = None

        line_bytes = len(line.encode("utf-8"))
        newline_bytes = 1  # for the newline we add when joining

        # If adding this line would exceed the limit, flush first
        if not in_fence and current_bytes + line_bytes + newline_bytes > max_bytes and current_lines:
            _flush()

        current_lines.append(line)
        current_bytes += line_bytes + newline_bytes

        # If we're at a paragraph boundary and have content, consider flushing
        if not in_fence and line.strip() == "" and current_bytes > max_bytes * 0.5:
            _flush()

    _flush()

    # Safety: if any single chunk is still too large, split by sentences
    safe_chunks = []
    for chunk in chunks:
        chunk_bytes = len(chunk.encode("utf-8"))
        if chunk_bytes > max_bytes:
            sentences = re.split(r'(?<=[.!?])\s+', chunk)
            sub_chunk = ""
            sub_bytes = 0
            for sentence in sentences:
                s_bytes = len(sentence.encode("utf-8")) + 1
                if sub_bytes + s_bytes > max_bytes and sub_chunk:
                    safe_chunks.append(sub_chunk.strip())
                    sub_chunk = sentence
                    sub_bytes = s_bytes
                else:
                    sub_chunk += " " + sentence if sub_chunk else sentence
                    sub_bytes += s_bytes
            if sub_chunk:
                safe_chunks.append(sub_chunk.strip())
            # If sentence splitting didn't help (no sentence delimiters), split by words
            if len(safe_chunks) == 1 and len(safe_chunks[0].encode("utf-8")) > max_bytes:
                words = chunk.split()
                word_chunk = ""
                word_bytes = 0
                safe_chunks = []
                for word in words:
                    w_bytes = len(word.encode("utf-8")) + 1
                    if word_bytes + w_bytes > max_bytes and word_chunk:
                        safe_chunks.append(word_chunk.strip())
                        word_chunk = word
                        word_bytes = w_bytes
                    else:
                        word_chunk += " " + word if word_chunk else word
                        word_bytes += w_bytes
                if word_chunk:
                    safe_chunks.append(word_chunk.strip())
        else:
            safe_chunks.append(chunk)

    # Final safety: verify no chunk exceeds max_bytes
    for i, chunk in enumerate(safe_chunks):
        if len(chunk.encode("utf-8")) > DEEPL_MAX_BYTES:
            print(
                f"[translate] ERROR: Chunk {i} exceeds {DEEPL_MAX_BYTES} bytes even after splitting. "
                "Text cannot be safely chunked for DeepL.",
                file=sys.stderr,
            )
            sys.exit(1)

    return safe_chunks


DEEPL_API_BASE = "https://api-free.deepl.com/v2"
DEEPL_MAX_BYTES = 131_072  # 128 KiB DeepL Free request limit

DEEPL_LANG_MAP = {
    "es": "ES",
    "fr": "FR",
    "de": "DE",
    "nl": "NL",
    "pt": "PT-PT",
}

DEEPL_MAX_RETRIES = 3
DEEPL_RETRY_BACKOFF_BASE = 1.0  # seconds
DEEPL_CHUNK_TARGET_BYTES = 110_000  # Leave margin under 128 KiB for form encoding overhead


def _provider_deepl(article_text, lang, model=None):
    """Call DeepL API Free to translate article text. Uses requests.

    Handles chunking, retries, and graceful error handling.
    """
    api_key = os.environ.get("DEEPL_API_KEY", "").strip()
    if not api_key:
        print("[translate] ERROR: DEEPL_API_KEY required for deepl provider.", file=sys.stderr)
        sys.exit(1)

    target_lang = DEEPL_LANG_MAP.get(lang)
    if not target_lang:
        print(f"[translate] ERROR: Unsupported language '{lang}' for DeepL.", file=sys.stderr)
        sys.exit(1)

    # Chunk text if needed
    text_bytes = article_text.encode("utf-8")
    if len(text_bytes) > DEEPL_MAX_BYTES:
        chunks = _chunk_text_for_deepl(article_text)
    else:
        chunks = [article_text]

    url = f"{DEEPL_API_BASE}/translate"
    headers = {"Authorization": f"DeepL-Auth-Key {api_key}"}
    translated_parts = []

    for chunk in chunks:
        data = {
            "text": chunk,
            "target_lang": target_lang,
            "source_lang": "EN",
            "tag_handling": "xml",
        }

        last_error = None
        for attempt in range(DEEPL_MAX_RETRIES + 1):
            try:
                resp = requests.post(url, headers=headers, data=data, timeout=120)
            except requests.RequestException as e:
                last_error = f"DeepL network failure: {e}"
                if attempt < DEEPL_MAX_RETRIES:
                    backoff = DEEPL_RETRY_BACKOFF_BASE * (2 ** attempt)
                    print(f"[translate] WARN: {last_error}. Retrying in {backoff}s...", file=sys.stderr)
                    time.sleep(backoff)
                    continue
                print(f"[translate] ERROR: {last_error}", file=sys.stderr)
                sys.exit(1)

            if resp.status_code == 200:
                pass  # success, handled below
            elif resp.status_code in (401, 403):
                print(f"[translate] ERROR: DeepL authentication failed ({resp.status_code}). Check DEEPL_API_KEY.", file=sys.stderr)
                sys.exit(1)
            elif resp.status_code == 456:
                print(f"[translate] ERROR: DeepL quota exceeded ({resp.status_code}). No more characters available.", file=sys.stderr)
                sys.exit(1)
            elif resp.status_code == 429:
                last_error = f"DeepL rate limit ({resp.status_code})"
                if attempt < DEEPL_MAX_RETRIES:
                    backoff = DEEPL_RETRY_BACKOFF_BASE * (2 ** attempt)
                    print(f"[translate] WARN: {last_error}. Retrying in {backoff}s...", file=sys.stderr)
                    time.sleep(backoff)
                    continue
                print(f"[translate] ERROR: {last_error}. Max retries exceeded.", file=sys.stderr)
                sys.exit(1)
            elif 500 <= resp.status_code < 600:
                last_error = f"DeepL server error ({resp.status_code})"
                if attempt < DEEPL_MAX_RETRIES:
                    backoff = DEEPL_RETRY_BACKOFF_BASE * (2 ** attempt)
                    print(f"[translate] WARN: {last_error}. Retrying in {backoff}s...", file=sys.stderr)
                    time.sleep(backoff)
                    continue
                print(f"[translate] ERROR: {last_error}. Max retries exceeded.", file=sys.stderr)
                sys.exit(1)
            else:
                print(f"[translate] ERROR: DeepL returned {resp.status_code}: {resp.text[:500]}", file=sys.stderr)
                sys.exit(1)

            try:
                payload = resp.json()
            except json.JSONDecodeError as e:
                print(f"[translate] ERROR: DeepL response is not valid JSON: {e}", file=sys.stderr)
                sys.exit(1)

            translations = payload.get("translations", [])
            if not translations:
                print("[translate] ERROR: DeepL response contains no translations.", file=sys.stderr)
                sys.exit(1)

            translated_text = translations[0].get("text", "")
            if not translated_text:
                print("[translate] ERROR: DeepL returned empty translation.", file=sys.stderr)
                sys.exit(1)

            translated_parts.append(translated_text)
            break  # success, move to next chunk

    return "\n\n".join(translated_parts)


PROVIDERS = {
    "mock": _provider_mock,
    "manual": _provider_manual,
    "deepl": _provider_deepl,
}


# ---------------------------------------------------------------------------
# Review file I/O
# ---------------------------------------------------------------------------
def _build_review_path(translations_dir, slug, lang):
    return translations_dir / f"{slug}.{lang}.review.md"


def _extract_title_from_body(body: str) -> str:
    """Extract H1 title from translated markdown body."""
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _build_glossary_table(glossary, lang):
    """Build terminology check table for review file."""
    lines = ["| Term | Expected | Found |", "|---|---|---|"]
    for term, translations in glossary.items():
        expected = translations.get(lang, "")
        lines.append(f"| {term} | {expected} | [ ] |")
    return "\n".join(lines)


def _write_review_file(review_path, article, body, provider, model, lang, glossary, source_chars):
    today = str(date.today())
    slug = article.get("slug", "")
    canonical_url = f"{SITE_BASE}/{lang}/articles/{slug}/" if slug else ""
    source_url = article.get("canonical_url", "")
    title = article.get("title", "")
    extracted = _extract_title_from_body(body)
    if extracted:
        translated_title = extracted
    elif provider == "mock":
        translated_title = f"[MOCK {lang.upper()}] {title}"
    else:
        translated_title = f"[DeepL draft — review needed] {title}"
    glossary_table = _build_glossary_table(glossary, lang)

    lines = [
        f"# Translation Review — {title}\n",
        f"- **Slug:** {slug}",
        f"- **Language:** {lang}",
        f"- **Target language name:** {LANG_NAMES.get(lang, lang)}",
        f"- **Original title:** {title}",
        f"- **Translated title:** {translated_title}",
        f"- **Source URL:** {source_url}",
        f"- **Canonical URL:** {canonical_url}",
        f"- **Model:** {provider}" + (f" ({model})" if model else ""),
        f"- **Source chars:** {source_chars}",
        f"- **Generated at:** {today}",
        "",
        "## Terminology check",
        "",
        glossary_table,
        "",
        "## Translated body",
        "",
        body,
        "",
        "## Review status",
        "",
        "Status: draft",
        "Approval method: human",
        "Reviewer:",
        "Reviewed at:",
        "Quality checked at:",
        "Quality check model:",
        "",
        "## Reviewer notes",
        "",
    ]
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[translate] Wrote review file: {review_path}")


def _parse_review_file(review_path):
    """Parse a review file and return dict with body, title, and status."""
    if not review_path.exists():
        return None
    text = review_path.read_text(encoding="utf-8")

    status_re = re.compile(r"^Status:[ \t]*(\S+)", re.IGNORECASE)
    reviewer_re = re.compile(r"^Reviewer:[ \t]*([^\n]*)$", re.MULTILINE)
    reviewed_at_re = re.compile(r"^Reviewed at:[ \t]*([^\n]*)$", re.MULTILINE)
    title_re = re.compile(r"^-\s*\*\*Translated title:\*\*\s*([^\n]*)$", re.MULTILINE)
    model_re = re.compile(r"^-\s*\*\*Model:\*\*\s*([^\n]*)$", re.MULTILINE)
    approval_method_re = re.compile(r"^Approval method:[ \t]*([^\n]*)$", re.MULTILINE)
    quality_checked_at_re = re.compile(r"^Quality checked at:[ \t]*([^\n]*)$", re.MULTILINE)
    quality_check_model_re = re.compile(r"^Quality check model:[ \t]*([^\n]*)$", re.MULTILINE)

    status = "draft"
    for line in text.splitlines():
        m = status_re.match(line)
        if m:
            status = m.group(1).lower()

    reviewer = ""
    m = reviewer_re.search(text)
    if m:
        reviewer = m.group(1).strip()

    reviewed_at = ""
    m = reviewed_at_re.search(text)
    if m:
        reviewed_at = m.group(1).strip()

    translated_title = ""
    m = title_re.search(text)
    if m:
        translated_title = m.group(1).strip()

    model = ""
    m = model_re.search(text)
    if m:
        model = m.group(1).strip()

    approval_method = ""
    m = approval_method_re.search(text)
    if m:
        approval_method = m.group(1).strip().lower()

    quality_checked_at = ""
    m = quality_checked_at_re.search(text)
    if m:
        quality_checked_at = m.group(1).strip()

    quality_check_model = ""
    m = quality_check_model_re.search(text)
    if m:
        quality_check_model = m.group(1).strip()

    # Extract body between "## Translated body" and "## Review status"
    body = ""
    in_body = False
    for line in text.splitlines():
        if line.startswith("## Translated body"):
            in_body = True
            continue
        if line.startswith("## Review status"):
            break
        if in_body:
            body += line + "\n"
    body = body.strip()

    return {
        "body": body,
        "status": status,
        "reviewer": reviewer,
        "reviewed_at": reviewed_at,
        "translated_title": translated_title,
        "model": model,
        "approval_method": approval_method,
        "quality_checked_at": quality_checked_at,
        "quality_check_model": quality_check_model,
    }


# ---------------------------------------------------------------------------
# Translations.json sidecar
# ---------------------------------------------------------------------------
def _build_translations_json(review_data, provider, source_chars):
    entry = {
        "status": "published" if review_data["status"] == "approved" else "draft",
        "title": review_data.get("translated_title", ""),
        "model": provider,
        "source_chars": source_chars,
    }
    approval_method = review_data.get("approval_method", "")
    if approval_method == "ai_qa":
        entry["approval_method"] = "ai_qa"
        entry["ai_generated"] = True
        entry["quality_checked_at"] = review_data.get("quality_checked_at", "")
        entry["quality_check_model"] = review_data.get("quality_check_model", "")
    else:
        entry["reviewed_at"] = review_data.get("reviewed_at", "")
        entry["reviewer"] = review_data.get("reviewer", "")
    return entry


def _apply_review_to_article(folder, lang, review_data, provider, source_chars):
    """Create article.<lang>.md and update translations.json from approved review."""
    if review_data["status"] != "approved":
        raise ValueError("Review status is not 'approved'")

    if not review_data.get("body"):
        raise ValueError("Review file has no translated body")

    article_dir = ARTICLES_DIR / folder
    article_lang_path = article_dir / f"article.{lang}.md"
    translations_json_path = article_dir / "translations.json"

    # Write article.<lang>.md
    from _atomic_io import atomic_write_text
    atomic_write_text(article_lang_path, review_data["body"])
    print(f"[translate] Wrote {article_lang_path}")

    # Read or create translations.json
    translations = {}
    if translations_json_path.exists():
        translations = json.loads(translations_json_path.read_text(encoding="utf-8"))

    translations[lang] = _build_translations_json(review_data, provider, source_chars)

    from _atomic_io import atomic_write_json
    atomic_write_json(translations_json_path, translations)
    print(f"[translate] Updated {translations_json_path}")


# ---------------------------------------------------------------------------
# Budget report
# ---------------------------------------------------------------------------
def _print_budget_report(processed, total_source_chars):
    """Print character budget summary."""
    budget = 500_000  # DeepL Free monthly limit
    used = total_source_chars
    remaining = budget - used
    pct = (used / budget) * 100
    print(f"[translate] Budget report:")
    print(f"[translate]   Articles processed: {processed}")
    print(f"[translate]   Source chars used:  {used:,}")
    print(f"[translate]   Monthly budget:     {budget:,}")
    print(f"[translate]   Remaining:          {remaining:,}")
    print(f"[translate]   Used:               {pct:.1f}%")


# ---------------------------------------------------------------------------
# Main commands
# ---------------------------------------------------------------------------
def _cmd_generate(args, articles):
    translations_dir = REPO_ROOT / args.translations_dir
    provider_fn = PROVIDERS.get(args.provider)
    if not provider_fn:
        print(f"[translate] Unknown provider: {args.provider}", file=sys.stderr)
        sys.exit(1)

    glossary = _load_glossary(Path(args.glossary))

    # Network safety check
    if args.provider not in ("mock", "manual"):
        if not args.allow_network:
            if args.dry_run:
                print(f"[translate] Dry-run with {args.provider} provider: no network calls made.")
            else:
                print(
                    f"[translate] ERROR: Provider '{args.provider}' requires --allow-network for live calls.",
                    file=sys.stderr,
                )
                sys.exit(1)

    langs = [l.strip() for l in args.lang.split(",") if l.strip()]
    for l in langs:
        if l not in LANG_NAMES:
            print(f"[translate] ERROR: Invalid language code: '{l}'", file=sys.stderr)
            sys.exit(1)

    # Compute projected character budget
    total_source_chars = 0
    for article in articles:
        folder = article.get("folder", "")
        body = _read_article_body(folder)
        if body:
            total_source_chars += _char_count(body) * len(langs)

    # DeepL quota check
    if args.provider == "deepl" and not args.dry_run:
        api_key = os.environ.get("DEEPL_API_KEY", "").strip()
        if not api_key:
            print("[translate] ERROR: DEEPL_API_KEY required for deepl provider.", file=sys.stderr)
            sys.exit(1)

        if args.allow_network:
            try:
                usage = _check_deepl_quota(
                    api_key,
                    total_source_chars,
                    args.quota_safety_margin,
                    args.ignore_quota_safety_margin,
                )
                print(f"[translate] DeepL usage: {usage['character_count']:,} / {usage['character_limit']:,} chars used")
                print(f"[translate] DeepL remaining: {usage['character_limit'] - usage['character_count']:,} chars")
                print(f"[translate] Projected chars: {total_source_chars:,}")
                print(f"[translate] Safety margin: {0 if args.ignore_quota_safety_margin else args.quota_safety_margin:,} chars")
            except SystemExit:
                raise
    elif args.provider == "deepl" and args.dry_run:
        print(f"[translate] Projected chars: {total_source_chars:,}")
        print(f"[translate] Safety margin: {0 if args.ignore_quota_safety_margin else args.quota_safety_margin:,} chars")
        if args.allow_network:
            api_key = os.environ.get("DEEPL_API_KEY", "").strip()
            if api_key:
                try:
                    usage = _check_deepl_quota(
                        api_key,
                        total_source_chars,
                        args.quota_safety_margin,
                        args.ignore_quota_safety_margin,
                    )
                    print(f"[translate] DeepL usage: {usage['character_count']:,} / {usage['character_limit']:,} chars used")
                    print(f"[translate] DeepL remaining: {usage['character_limit'] - usage['character_count']:,} chars")
                    print("[translate] Quota check: PASSED (dry-run)")
                except SystemExit:
                    raise
            else:
                print("[translate] DeepL usage check skipped (DEEPL_API_KEY not set)")
        else:
            print("[translate] DeepL usage check skipped (no --allow-network)")

    if args.dry_run:
        _print_budget_report(len(articles) * len(langs), total_source_chars)
        return

    processed = 0
    for article in articles:
        slug = article.get("slug", article.get("folder", ""))
        folder = article.get("folder", "")
        body = _read_article_body(folder)
        if not body:
            print(f"[translate] SKIP {slug}: no article body")
            continue

        source_chars = _char_count(body)

        for lang in langs:
            translated = provider_fn(body, lang=lang)
            review_path = _build_review_path(translations_dir, slug, lang)
            _write_review_file(review_path, article, translated, args.provider, None, lang, glossary, source_chars)
            processed += 1

    _print_budget_report(processed, total_source_chars)


def _cmd_apply(args, articles):
    translations_dir = REPO_ROOT / args.translations_dir
    langs = [l.strip() for l in args.lang.split(",") if l.strip()]
    for l in langs:
        if l not in LANG_NAMES:
            print(f"[translate] ERROR: Invalid language code: '{l}'", file=sys.stderr)
            sys.exit(1)

    applied = 0
    skipped = 0

    for article in articles:
        slug = article.get("slug", article.get("folder", ""))
        folder = article.get("folder", "")
        body = _read_article_body(folder)
        source_chars = _char_count(body) if body else 0

        for lang in langs:
            review_path = _build_review_path(translations_dir, slug, lang)
            if not review_path.exists():
                continue

            review_data = _parse_review_file(review_path)
            if not review_data:
                continue

            if review_data["status"] != "approved":
                print(f"[translate] SKIP {slug}.{lang}: status is '{review_data['status']}' (not approved)")
                skipped += 1
                continue

            try:
                provider_name = review_data.get("model", "mock") or "mock"
                _apply_review_to_article(folder, lang, review_data, provider_name, source_chars)
                applied += 1
            except Exception as e:
                print(f"[translate] ERROR {slug}.{lang}: {e}", file=sys.stderr)
                skipped += 1

    print(f"[translate] Applied: {applied}, Skipped: {skipped}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main(argv=None):
    parser = _build_argparser()
    args = parser.parse_args(argv)

    if args.write_review_files:
        args.dry_run = False

    index = _load_index()
    all_articles = index.get("articles", [])

    # Filter candidates
    candidates = []
    for a in all_articles:
        if args.slug:
            if a.get("slug") == args.slug or a.get("folder") == args.slug:
                candidates.append(a)
                break
        else:
            candidates.append(a)

    if not candidates:
        print("[translate] No candidate articles found.")
        return 0

    if args.apply_approved:
        _cmd_apply(args, candidates)
    else:
        _cmd_generate(args, candidates)

    return 0


if __name__ == "__main__":
    sys.exit(main())
