#!/usr/bin/env python3
"""Generate translation review files and apply approved translations.

Mirrors the E35 summaries workflow: draft review files -> human review ->
approved -> article.<lang>.md sidecars.

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
from pathlib import Path

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


def _provider_deepl(article_text, lang, model=None):
    api_key = os.environ.get("DEEPL_API_KEY", "").strip()
    if not api_key:
        print("[translate] ERROR: DEEPL_API_KEY required for deepl provider.", file=sys.stderr)
        sys.exit(1)
    print("[translate] deepl provider is a stub. Install the deepl SDK and implement _provider_deepl.", file=sys.stderr)
    sys.exit(1)


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
    translated_title = _extract_title_from_body(body) or f"[MOCK {lang.upper()}] {title}"
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
        "Reviewer:",
        "Reviewed at:",
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

    status_re = re.compile(r"^Status:\s*(\S+)", re.IGNORECASE)
    reviewer_re = re.compile(r"^Reviewer:\s*(.*)$", re.MULTILINE)
    reviewed_at_re = re.compile(r"^Reviewed at:\s*(.*)$", re.MULTILINE)
    title_re = re.compile(r"^-\s*\*\*Translated title:\*\*\s*(.*)$", re.MULTILINE)

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
    }


# ---------------------------------------------------------------------------
# Translations.json sidecar
# ---------------------------------------------------------------------------
def _build_translations_json(review_data, provider, source_chars):
    return {
        "status": "published" if review_data["status"] == "approved" else "draft",
        "title": review_data.get("translated_title", ""),
        "reviewed_at": review_data.get("reviewed_at", ""),
        "reviewer": review_data.get("reviewer", ""),
        "model": provider,
        "source_chars": source_chars,
    }


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
        if args.dry_run:
            print(f"[translate] Dry-run with {args.provider} provider: no network calls made.")
        elif not args.allow_network:
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

    total_source_chars = 0
    processed = 0

    for article in articles:
        slug = article.get("slug", article.get("folder", ""))
        folder = article.get("folder", "")
        body = _read_article_body(folder)
        if not body:
            print(f"[translate] SKIP {slug}: no article body")
            continue

        source_chars = _char_count(body)
        total_source_chars += source_chars * len(langs)

        for lang in langs:
            prompt = _build_prompt(body, lang, glossary)

            if args.dry_run:
                print(f"[translate] DRY-RUN {slug} -> {lang} ({source_chars} chars)")
                continue

            translated = provider_fn(body, lang=lang)
            review_path = _build_review_path(translations_dir, slug, lang)
            _write_review_file(review_path, article, translated, args.provider, None, lang, glossary, source_chars)
            processed += 1

    if args.dry_run:
        _print_budget_report(len(articles) * len(langs), total_source_chars)
    else:
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
                _apply_review_to_article(folder, lang, review_data, "mock", source_chars)
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
