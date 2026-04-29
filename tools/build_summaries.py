#!/usr/bin/env python3
"""Generate multi-length structured summaries for archive articles.

Usage:
    python3 tools/build_summaries.py --dry-run --limit 5 --provider mock
    python3 tools/build_summaries.py --dry-run --slug XYZ --provider mock
    python3 tools/build_summaries.py --write-review-files --limit 5 --provider anthropic --model claude-sonnet-4-20250514 --allow-network
    python3 tools/build_summaries.py --apply-approved --slug XYZ
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

WORD_TARGETS = {
    "short": (40, 60),
    "medium": (170, 230),
    "long": (430, 570),
}


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
def _build_argparser():
    parser = argparse.ArgumentParser(description="Generate article summaries.")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Preview without writes or network calls (default).")
    parser.add_argument("--write-review-files", action="store_true",
                        help="Generate and write review files.")
    parser.add_argument("--apply-approved", action="store_true",
                        help="Apply approved review files to metadata.")
    parser.add_argument("--provider", type=str, default="mock",
                        choices=["mock", "anthropic", "openai", "manual"],
                        help="Generation backend.")
    parser.add_argument("--model", type=str, default=None,
                        help="Specific model name.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Process at most N articles.")
    parser.add_argument("--slug", type=str, default=None,
                        help="Target a single article by slug.")
    parser.add_argument("--summaries-dir", type=str, default="summaries",
                        help="Output directory for review files.")
    parser.add_argument("--allow-network", action="store_true",
                        help="Required for real LLM calls.")
    parser.add_argument("--allow-partial", action="store_true",
                        help="Allow applying review files missing some lengths.")
    return parser


# ---------------------------------------------------------------------------
# Index loading
# ---------------------------------------------------------------------------
def _load_index():
    if not INDEX_PATH.exists():
        print(f"[summaries] index.json not found at {INDEX_PATH}", file=sys.stderr)
        sys.exit(1)
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


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


# ---------------------------------------------------------------------------
# Word counting
# ---------------------------------------------------------------------------
def _word_count(text):
    return len(text.split())


def _validate_word_counts(summaries):
    """Return list of validation errors."""
    errors = []
    for key, (low, high) in WORD_TARGETS.items():
        text = summaries.get(key, "")
        if not text:
            continue
        wc = _word_count(text)
        if wc < low or wc > high:
            errors.append(f"{key}: {wc} words (expected {low}-{high})")
    return errors


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------
def _build_prompt(article_text):
    return (
        "Summarize the following article in three lengths.\n"
        "Use ONLY the provided article text. Do not invent facts, numbers, citations, or quotes.\n"
        "Preserve the author's voice and nuance.\n\n"
        "Article:\n"
        "---\n"
        f"{article_text}\n"
        "---\n\n"
        "Produce exactly:\n"
        "1. SHORT (40-60 words): single paragraph, suitable for ChatGPT-style quote cards\n"
        "2. MEDIUM (170-230 words): structured synthesis, suitable for Claude-style summaries\n"
        "3. LONG (430-570 words): comprehensive overview, suitable for Perplexity-style research briefs\n\n"
        "No markdown links. No invented statistics. No external references.\n"
    )


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------
def _provider_mock(article_text, model=None):
    """Deterministic synthetic summaries for testing. No API key needed."""
    words = article_text.split()[:20]
    snippet = " ".join(words) if words else "This article discusses important AI strategy topics."
    return {
        "short": f"{snippet} A concise overview of key AI strategy insights for European SMEs.",
        "medium": f"{snippet} This article explores the strategic implications of artificial intelligence adoption for European small and medium enterprises. It examines practical frameworks for governance, risk management, and operational integration while maintaining competitive advantage in regulated markets.",
        "long": f"{snippet} This comprehensive analysis examines how European SMEs can strategically adopt artificial intelligence while navigating regulatory requirements including the EU AI Act. The article covers governance frameworks, risk assessment methodologies, operational integration strategies, and competitive positioning. It emphasizes practical implementation steps, organizational readiness, and the importance of human oversight in automated systems. Key themes include data sovereignty, ethical AI deployment, and measurable business outcomes.",
    }


def _provider_manual(article_text, model=None):
    print("[summaries] Manual provider: paste or pipe summaries in review-file format.", file=sys.stderr)
    sys.exit(1)


def _provider_anthropic(article_text, model=None):
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("[summaries] ERROR: ANTHROPIC_API_KEY required for anthropic provider.", file=sys.stderr)
        sys.exit(1)
    print("[summaries] anthropic provider is a stub. Install the anthropic SDK and implement _provider_anthropic.", file=sys.stderr)
    sys.exit(1)


def _provider_openai(article_text, model=None):
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("[summaries] ERROR: OPENAI_API_KEY required for openai provider.", file=sys.stderr)
        sys.exit(1)
    print("[summaries] openai provider is a stub. Install the openai SDK and implement _provider_openai.", file=sys.stderr)
    sys.exit(1)


PROVIDERS = {
    "mock": _provider_mock,
    "manual": _provider_manual,
    "anthropic": _provider_anthropic,
    "openai": _provider_openai,
}


# ---------------------------------------------------------------------------
# Review file I/O
# ---------------------------------------------------------------------------
def _build_review_path(summaries_dir, slug):
    return summaries_dir / f"{slug}.review.md"


def _write_review_file(review_path, article, summaries, provider, model):
    today = str(date.today())
    lines = [
        f"# Summary Review — {article['title']}\n",
        f"Article folder: {article.get('folder', '')}",
        f"Canonical URL: {article.get('canonical_url', '')}",
        f"Generated at: {today}",
        f"Model: {provider}" + (f" ({model})" if model else ""),
        "",
        "## 50-word summary",
        "",
        summaries.get("short", ""),
        "",
        "## 200-word summary",
        "",
        summaries.get("medium", ""),
        "",
        "## 500-word summary",
        "",
        summaries.get("long", ""),
        "",
        "## Review status",
        "",
        "Status: draft",
        "Reviewer:",
        "Reviewed at:",
        "",
        "## Notes",
        "",
    ]
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[summaries] Wrote review file: {review_path}")


def _parse_review_file(review_path):
    """Parse a review file and return dict with short/medium/long and status."""
    if not review_path.exists():
        return None
    text = review_path.read_text(encoding="utf-8")
    sections = {}
    current = None
    lines = []

    status_re = re.compile(r"^Status:\s*(\S+)", re.IGNORECASE)
    status = "draft"
    for line in text.splitlines():
        m = status_re.match(line)
        if m:
            status = m.group(1).lower()

    # Simple section parser
    for line in text.splitlines():
        if line.startswith("## 50-word summary"):
            current = "short"
            lines = []
        elif line.startswith("## 200-word summary"):
            if current:
                sections[current] = "\n".join(lines).strip()
            current = "medium"
            lines = []
        elif line.startswith("## 500-word summary"):
            if current:
                sections[current] = "\n".join(lines).strip()
            current = "long"
            lines = []
        elif line.startswith("## Review status"):
            if current:
                sections[current] = "\n".join(lines).strip()
            current = None
        elif current and not line.startswith("##"):
            lines.append(line)

    if current and current not in sections:
        sections[current] = "\n".join(lines).strip()

    return {
        "short": sections.get("short", ""),
        "medium": sections.get("medium", ""),
        "long": sections.get("long", ""),
        "status": status,
    }


# ---------------------------------------------------------------------------
# Metadata application
# ---------------------------------------------------------------------------
def _apply_review_to_metadata(folder, review_data, allow_partial=False):
    meta_path = ARTICLES_DIR / folder / "metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"metadata.json not found: {meta_path}")

    if review_data["status"] != "approved":
        raise ValueError("Review status is not 'approved'")

    required = ["short", "medium", "long"]
    missing = [k for k in required if not review_data.get(k)]
    if missing and not allow_partial:
        raise ValueError(f"Review file missing required sections: {missing}")

    data = json.loads(meta_path.read_text(encoding="utf-8"))

    # Only update summary fields
    if review_data.get("short"):
        data["summary_short"] = review_data["short"]
    if review_data.get("medium"):
        data["summary_medium"] = review_data["medium"]
    if review_data.get("long"):
        data["summary_long"] = review_data["long"]
    data["summary_reviewed_at"] = str(date.today())

    from _atomic_io import atomic_write_json
    atomic_write_json(meta_path, data)
    print(f"[summaries] Applied approved summaries to {meta_path}")


# ---------------------------------------------------------------------------
# Main commands
# ---------------------------------------------------------------------------
def _cmd_generate(args, articles):
    summaries_dir = REPO_ROOT / args.summaries_dir
    provider_fn = PROVIDERS.get(args.provider)
    if not provider_fn:
        print(f"[summaries] Unknown provider: {args.provider}", file=sys.stderr)
        sys.exit(1)

    # Network safety check
    if args.provider != "mock" and args.provider != "manual":
        if args.dry_run:
            print(f"[summaries] Dry-run with {args.provider} provider: no network calls made.")
        elif not args.allow_network:
            print(
                f"[summaries] ERROR: Provider '{args.provider}' requires --allow-network for live calls.",
                file=sys.stderr,
            )
            sys.exit(1)

    processed = 0
    for article in articles:
        slug = article.get("slug", article.get("folder", ""))
        folder = article.get("folder", "")
        body = _read_article_body(folder)
        if not body:
            print(f"[summaries] SKIP {slug}: no article body")
            continue

        prompt = _build_prompt(body)

        if args.dry_run:
            print(f"[summaries] DRY-RUN {slug}")
            print(f"[summaries] Prompt preview ({len(prompt)} chars)")
            continue

        summaries = provider_fn(body, model=args.model)
        errors = _validate_word_counts(summaries)
        if errors:
            print(f"[summaries] WARN {slug}: word count validation failed: {errors}")

        review_path = _build_review_path(summaries_dir, slug)
        _write_review_file(review_path, article, summaries, args.provider, args.model)
        processed += 1

    print(f"[summaries] Processed: {processed}")


def _cmd_apply(args, articles):
    summaries_dir = REPO_ROOT / args.summaries_dir
    applied = 0
    skipped = 0
    for article in articles:
        slug = article.get("slug", article.get("folder", ""))
        folder = article.get("folder", "")
        review_path = _build_review_path(summaries_dir, slug)
        if not review_path.exists():
            continue

        review_data = _parse_review_file(review_path)
        if not review_data:
            continue

        if review_data["status"] != "approved":
            print(f"[summaries] SKIP {slug}: status is '{review_data['status']}' (not approved)")
            skipped += 1
            continue

        try:
            _apply_review_to_metadata(folder, review_data, allow_partial=args.allow_partial)
            applied += 1
        except Exception as e:
            print(f"[summaries] ERROR {slug}: {e}", file=sys.stderr)
            skipped += 1

    print(f"[summaries] Applied: {applied}, Skipped: {skipped}")


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

    if args.limit is not None:
        candidates = candidates[:args.limit]

    if not candidates:
        print("[summaries] No candidate articles found.")
        return 0

    if args.apply_approved:
        _cmd_apply(args, candidates)
    else:
        _cmd_generate(args, candidates)

    return 0


if __name__ == "__main__":
    sys.exit(main())
