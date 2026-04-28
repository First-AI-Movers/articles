#!/usr/bin/env python3
"""Ingest a single article from an external JSON payload into the archive.

Validates the payload against tools/article_schema.json, then writes
articles/YYYY-MM-DD-slug/article.md and metadata.json.

Usage:
    python3 tools/ingest_article.py --payload-file payload.json --dry-run
    python3 tools/ingest_article.py --payload-file payload.json --write
    cat payload.json | python3 tools/ingest_article.py --dry-run
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = REPO_ROOT / "articles"
SCHEMA_PATH = Path(__file__).resolve().parent / "article_schema.json"


def _get_articles_dir(args_articles_dir=None):
    if args_articles_dir:
        return Path(args_articles_dir).resolve()
    return ARTICLES_DIR

ALLOWED_STATUSES = {"published", "ready", "approved"}


def _yaml_quote(value):
    """Serialize a string as a YAML scalar using JSON double-quoted string rules."""
    return json.dumps(str(value), ensure_ascii=False)


def _load_schema():
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _normalize_date(value):
    """Normalize date values to YYYY-MM-DD."""
    if value is None:
        return None
    s = str(value).strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s
    m = re.match(r"^(\d{4}-\d{2}-\d{2})T", s)
    if m:
        return m.group(1)
    return None


def _build_folder_name(published_date, slug):
    safe_slug = re.sub(r"[^a-z0-9-]", "", slug.lower())
    return f"{published_date}-{safe_slug}"


def _folder_exists(folder, articles_dir):
    return (articles_dir / folder).exists()


def _title_exists(title, articles_dir):
    if not articles_dir.exists():
        return False
    target = title.strip().casefold()
    for p in articles_dir.iterdir():
        if not p.is_dir():
            continue
        meta = p / "metadata.json"
        if not meta.exists():
            continue
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
            if data.get("title", "").strip().casefold() == target:
                return True
        except Exception:
            continue
    return False


def _validate_payload(payload, schema):
    """Return (errors, warnings) tuples."""
    errors = []
    warnings = []
    required = set(schema.get("required", []))
    props = schema.get("properties", {})

    for key in required:
        if not payload.get(key):
            errors.append(f"Missing required field: {key}")

    for key, value in payload.items():
        prop = props.get(key, {})
        ptype = prop.get("type")
        if ptype == "string" and not isinstance(value, str):
            errors.append(f"Field {key} must be a string")
        elif ptype == "integer" and not isinstance(value, int):
            errors.append(f"Field {key} must be an integer")
        elif ptype == "array" and not isinstance(value, list):
            errors.append(f"Field {key} must be a list")

    slug = payload.get("slug", "")
    if slug and not re.match(r"^[a-z0-9-]+$", slug):
        errors.append(f"Slug '{slug}' must be lowercase alphanumeric with hyphens only")

    date = payload.get("published_date", "")
    if date and not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        errors.append(f"Published date '{date}' must be YYYY-MM-DD")

    status = payload.get("status", "").lower()
    if status and status not in ALLOWED_STATUSES:
        warnings.append(f"Status '{status}' is not in allowed set {ALLOWED_STATUSES}; record will be skipped")

    return errors, warnings


def _write_article(payload, dry_run, articles_dir):
    """Write article.md and metadata.json for a validated payload.

    Returns (folder_name, created_bool).
    """
    published_date = payload["published_date"]
    slug = payload["slug"]
    folder = _build_folder_name(published_date, slug)
    article_dir = articles_dir / folder

    if _folder_exists(folder, articles_dir):
        return folder, False

    title = payload["title"]
    if _title_exists(title, articles_dir):
        return folder, False

    if dry_run:
        return folder, True

    article_dir.mkdir(parents=True, exist_ok=True)

    front_matter = {
        "title": title,
        "author": payload.get("author", "Dr. Hernani Costa"),
        "author_url": payload.get("author_url", "https://drhernanicosta.com"),
        "author_linkedin": "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/",
        "publication": payload.get("company", "First AI Movers"),
        "publication_url": payload.get("company_url", "https://firstaimovers.com"),
        "canonical_url": payload["canonical_url"],
        "published_date": published_date,
        "license": payload.get("license", "CC BY 4.0"),
    }
    fm_lines = ["---"]
    for k, v in front_matter.items():
        fm_lines.append(f"{k}: {_yaml_quote(v)}")
    fm_lines.append("---")
    article_body = payload.get("article_markdown", "")
    md_content = "\n".join(fm_lines) + "\n\n" + article_body.lstrip("\n")

    (article_dir / "article.md").write_text(md_content, encoding="utf-8")

    metadata = {
        "id": None,
        "title": title,
        "slug": slug,
        "folder": folder,
        "published_date": published_date,
        "author": payload.get("author", "Dr. Hernani Costa"),
        "author_url": payload.get("author_url", "https://drhernanicosta.com"),
        "company": payload.get("company", "First AI Movers"),
        "company_url": payload.get("company_url", "https://firstaimovers.com"),
        "canonical_url": payload["canonical_url"],
        "tags": payload.get("tags", []),
        "word_count": payload.get("word_count"),
        "read_time_minutes": payload.get("read_time_minutes"),
        "funnel_stage": payload.get("funnel_stage"),
        "first_ai_movers_services": payload.get("first_ai_movers_services", []),
        "status": payload.get("status", "published"),
        "topics": [],
    }
    metadata = {k: v for k, v in metadata.items() if v is not None}
    text = json.dumps(metadata, indent=2, ensure_ascii=False)
    if not text.endswith("\n"):
        text += "\n"
    (article_dir / "metadata.json").write_text(text, encoding="utf-8")

    return folder, True


def main(argv=None):
    parser = argparse.ArgumentParser(description="Ingest an article from an external JSON payload")
    parser.add_argument("--payload-file", type=Path,
                        help="Path to JSON payload file (default: read from stdin)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run in dry-run mode (default)")
    parser.add_argument("--write", action="store_true",
                        help="Write new article folder (default is dry-run)")
    parser.add_argument("--articles-dir",
                        help="Override the articles directory (for testing)")
    args = parser.parse_args(argv)

    if args.dry_run and args.write:
        parser.error("--dry-run and --write are mutually exclusive")

    dry_run = not args.write

    # Read payload
    if args.payload_file:
        raw = args.payload_file.read_text(encoding="utf-8")
    else:
        raw = sys.stdin.read()

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in payload: {exc}")

    # Normalize date if needed
    if "published_date" in payload:
        normalized = _normalize_date(payload["published_date"])
        if normalized:
            payload["published_date"] = normalized

    # Validate
    schema = _load_schema()
    errors, warnings = _validate_payload(payload, schema)

    if warnings:
        for w in warnings:
            print(f"[warning] {w}", file=sys.stderr)

    if errors:
        for e in errors:
            print(f"[error] {e}", file=sys.stderr)
        raise SystemExit("Payload validation failed")

    # Write
    articles_dir = _get_articles_dir(args.articles_dir)
    folder, created = _write_article(payload, dry_run, articles_dir)

    if created:
        mode = "would create" if dry_run else "created"
        print(f"[{mode}] {folder}/article.md + metadata.json")
    else:
        print(f"[skip] {folder}/ already exists or duplicate title")

    return 0


if __name__ == "__main__":
    sys.exit(main())
