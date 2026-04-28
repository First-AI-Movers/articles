#!/usr/bin/env python3
"""Scrub third-party presigned URLs from article content.

Beehiiv and some other platforms inject <audio> blocks with S3 presigned URLs
that contain AWS credential material. These URLs expire and should not be
committed to the archive. This tool removes or replaces them idempotently.

Usage:
    python3 tools/scrub_presigned_urls.py --dry-run
    python3 tools/scrub_presigned_urls.py
"""

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = REPO_ROOT / "articles"

# Pattern: Beehiiv <audio> blocks with S3 presigned URLs.
# Matches the full <audio>...</audio> tag when the src contains
# X-Amz-Signature (indicating a presigned URL).
_BEEHIIV_AUDIO_RE = re.compile(
    r'<audio[^>]*\bid="beehiiv-audio-tts-id"[^>]*>.*?<source[^>]*src="[^"]*X-Amz-Signature[^"]*"[^>]*/>.*?</audio>',
    re.IGNORECASE | re.DOTALL,
)

# Fallback: any <audio> block containing X-Amz-Signature in its src.
_GENERIC_AUDIO_RE = re.compile(
    r'<audio[^>]*>.*?<source[^>]*src="[^"]*X-Amz-Signature[^"]*"[^>]*/>.*?</audio>',
    re.IGNORECASE | re.DOTALL,
)

REPLACEMENT = "<!-- Audio embed removed: third-party presigned URL expired -->"


def _find_article_dirs():
    """Yield all article directories under ARTICLES_DIR."""
    if not ARTICLES_DIR.exists():
        return
    for path in ARTICLES_DIR.iterdir():
        if path.is_dir() and (path / "article.md").exists():
            yield path


def _scrub_file(md_path: Path, dry_run: bool) -> bool:
    """Scrub a single article.md. Return True if changes were made."""
    text = md_path.read_text(encoding="utf-8")
    original = text

    # Try the specific Beehiiv pattern first, then generic fallback.
    text = _BEEHIIV_AUDIO_RE.sub(REPLACEMENT, text)
    if text == original:
        text = _GENERIC_AUDIO_RE.sub(REPLACEMENT, text)

    changed = text != original
    if changed and not dry_run:
        md_path.write_text(text, encoding="utf-8")
    return changed


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Scrub third-party presigned URLs from article content"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without writing files",
    )
    args = parser.parse_args(argv)

    affected = []
    for article_dir in sorted(_find_article_dirs()):
        md_path = article_dir / "article.md"
        changed = _scrub_file(md_path, args.dry_run)
        if changed:
            affected.append(md_path)

    mode = "(dry-run)" if args.dry_run else ""
    print(f"Scrubbed {len(affected)} article(s) {mode}")
    for p in affected:
        try:
            rel = p.relative_to(REPO_ROOT)
        except ValueError:
            rel = p.name
        print(f"  {rel}")

    return 0 if len(affected) == 0 else 1 if args.dry_run else 0


if __name__ == "__main__":
    sys.exit(main())
