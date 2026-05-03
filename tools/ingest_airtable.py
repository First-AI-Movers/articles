#!/usr/bin/env python3
"""Ingest articles from Airtable into the archive.

Fetches records from an Airtable base, validates them against the article
schema, and writes new article folders (article.md + metadata.json).

Environment variables:
    AIRTABLE_PAT          — Personal Access Token (required)
    AIRTABLE_BASE_ID      — Base ID (required)
    AIRTABLE_TABLE_NAME   — Table name or ID (required)
    AIRTABLE_VIEW_NAME    — Optional view name or ID

Usage:
    python3 tools/ingest_airtable.py --dry-run
    python3 tools/ingest_airtable.py --write
    python3 tools/ingest_airtable.py --write --since-hours 72
    python3 tools/ingest_airtable.py --write --record-id recXXXXXXXXXXXXXX
    python3 tools/ingest_airtable.py --dry-run --limit 5
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = REPO_ROOT / "articles"
SCHEMA_PATH = Path(__file__).resolve().parent / "article_schema.json"

# ---------------------------------------------------------------------------
# Configurable field mapping: Airtable field name → article payload key.
# Edit this mapping if your Airtable base uses different field names.
# ---------------------------------------------------------------------------
AIRTABLE_FIELD_MAP = {
    "title": "Title",
    "slug": "slug",
    "published_date": "Pub Date",
    "canonical_url": "GUID",
    "article_markdown": "Content HTML",
    "author": "Author",
    "author_url": "Author URL",
    "company": "Company",
    "company_url": "Company URL",
    "tags": "tags",
    "funnel_stage": "Funnel Stage",
    "first_ai_movers_services": "First AI Movers Services",
    # The live "Pubs/beehiiv" base does not have a literal "Status" field;
    # editorial state is tracked in "FAIM Status" (singleSelect: Ready, Posted, ...).
    # Allowed-status logic remains case-insensitive against ALLOWED_STATUSES below.
    "status": "FAIM Status",
    "word_count": "Word Count",
    "read_time_minutes": "Read Time",
    "license": "License",
}

# Status values that are allowed for ingestion.
ALLOWED_STATUSES = {"published", "ready", "approved"}

AIRTABLE_API_URL = "https://api.airtable.com/v0"


def _yaml_quote(value):
    """Serialize a string as a YAML scalar using JSON double-quoted string rules.

    JSON double-quoted strings are valid YAML 1.2 scalars and safely escape
    quotes, backslashes, newlines, and other control characters.
    """
    return json.dumps(str(value), ensure_ascii=False)


def _load_schema():
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _env_required(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required env var: {name}")
    return value


def _to_list(value):
    """Coerce Airtable linked-record / multi-select / comma-string to list."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return []


def _to_int(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _to_str(value):
    if value is None:
        return None
    return str(value).strip()


def _normalize_date(value):
    """Normalize Airtable date values to YYYY-MM-DD.

    Accepts bare dates (2026-04-25) and ISO timestamps
    (2026-04-25T00:00:00.000Z or 2026-04-25T00:00:00Z).
    Returns YYYY-MM-DD string or None if unparseable.
    """
    if value is None:
        return None
    s = str(value).strip()
    # Already a bare date
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s
    # ISO timestamp with or without milliseconds
    m = re.match(r"^(\d{4}-\d{2}-\d{2})T", s)
    if m:
        return m.group(1)
    return None


def _normalize_article_body(value):
    """Normalize article body from Airtable.

    Preserves Markdown as-is. Preserves HTML inside Markdown (Markdown allows
    raw HTML). Normalizes line endings and strips whitespace.
    # TODO: Add HTML-to-Markdown conversion after dry-run confirms Content HTML format.
    """
    if value is None:
        return ""
    text = str(value)
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.strip()


def _slug_from_canonical_url(url):
    """Extract a slug from the final path segment of a canonical URL.

    Returns a normalized slug (lowercase, a-z/0-9/hyphens only, no leading/trailing
    hyphens, collapsed duplicates) or None if no valid segment exists.
    """
    if not url:
        return None
    try:
        from urllib.parse import urlparse
        parsed = urlparse(str(url).strip())
        path = parsed.path.rstrip("/")
        if not path:
            return None
        segment = path.split("/")[-1]
        if not segment:
            return None
        # Normalize: lowercase, keep only a-z 0-9 hyphens, collapse duplicates
        slug = re.sub(r"[^a-z0-9-]", "", segment.lower())
        slug = re.sub(r"-+", "-", slug).strip("-")
        return slug if slug else None
    except Exception:
        return None


def _build_folder_name(published_date, slug):
    """Generate repo folder name: YYYY-MM-DD-<slug>."""
    safe_slug = re.sub(r"[^a-z0-9-]", "", slug.lower())
    return f"{published_date}-{safe_slug}"


def _folder_exists(folder):
    return (ARTICLES_DIR / folder).exists()


def _title_exists(title):
    """Check whether a case-insensitive title already exists in the repo."""
    if not ARTICLES_DIR.exists():
        return False
    target = title.strip().casefold()
    for p in ARTICLES_DIR.iterdir():
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


def _record_to_payload(record):
    """Map an Airtable record fields dict to an article payload dict."""
    fields = record.get("fields", {})
    payload = {}

    for key, airtable_name in AIRTABLE_FIELD_MAP.items():
        raw = fields.get(airtable_name)
        if key in ("tags", "first_ai_movers_services"):
            payload[key] = _to_list(raw)
        elif key in ("word_count", "read_time_minutes"):
            payload[key] = _to_int(raw)
        elif key == "published_date":
            payload[key] = _normalize_date(raw)
        elif key == "article_markdown":
            payload[key] = _normalize_article_body(raw)
        else:
            payload[key] = _to_str(raw)

    # Derive missing slug from canonical URL (GUID) when Airtable slug is absent
    if not payload.get("slug") and payload.get("canonical_url"):
        derived = _slug_from_canonical_url(payload["canonical_url"])
        if derived:
            payload["slug"] = derived

    # Drop None values so defaults are handled later
    payload = {k: v for k, v in payload.items() if v is not None}
    return payload


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

    # Slug pattern
    slug = payload.get("slug", "")
    if slug and not re.match(r"^[a-z0-9-]+$", slug):
        errors.append(f"Slug '{slug}' must be lowercase alphanumeric with hyphens only")

    # Date pattern
    date = payload.get("published_date", "")
    if date and not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        errors.append(f"Published date '{date}' must be YYYY-MM-DD")

    # Status gate
    status = payload.get("status", "").lower()
    if status and status not in ALLOWED_STATUSES:
        warnings.append(f"Status '{status}' is not in allowed set {ALLOWED_STATUSES}; record will be skipped")

    return errors, warnings


def _write_article(payload, record_id, dry_run):
    """Write article.md and metadata.json for a validated payload.

    Returns (folder_name, created_bool).
    """
    published_date = payload["published_date"]
    slug = payload["slug"]
    folder = _build_folder_name(published_date, slug)
    article_dir = ARTICLES_DIR / folder

    if _folder_exists(folder):
        return folder, False  # already exists — idempotent skip

    title = payload["title"]
    if _title_exists(title):
        return folder, False  # duplicate title — skip

    if dry_run:
        return folder, True  # would create

    article_dir.mkdir(parents=True, exist_ok=True)

    # article.md front matter
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

    # metadata.json
    metadata = {
        "id": record_id,
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
        "topics": [],  # populated by normalize_tags.py
    }
    # Drop None values to keep JSON clean
    metadata = {k: v for k, v in metadata.items() if v is not None}
    text = json.dumps(metadata, indent=2, ensure_ascii=False)
    if not text.endswith("\n"):
        text += "\n"
    (article_dir / "metadata.json").write_text(text, encoding="utf-8")

    return folder, True


def _fetch_records(pat, base_id, table_name, view_name=None, since_hours=None, record_id=None, limit=None):
    """Yield Airtable record dicts."""
    headers = {"Authorization": f"Bearer {pat}"}

    if record_id:
        url = f"{AIRTABLE_API_URL}/{base_id}/{table_name}/{record_id}"
        resp = requests.get(url, headers=headers, timeout=60)
        resp.raise_for_status()
        yield resp.json()
        return

    params = {}
    if view_name:
        params["view"] = view_name
    if limit:
        params["maxRecords"] = limit
    if since_hours:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=since_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
        params["filterByFormula"] = f"IS_AFTER(LAST_MODIFIED_TIME(), '{cutoff}')"

    url = f"{AIRTABLE_API_URL}/{base_id}/{table_name}"
    while True:
        query = urlencode(params)
        full_url = f"{url}?{query}" if query else url
        resp = requests.get(full_url, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        for record in data.get("records", []):
            yield record
        offset = data.get("offset")
        if not offset:
            break
        params["offset"] = offset


def main(argv=None):
    parser = argparse.ArgumentParser(description="Ingest articles from Airtable")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run in dry-run mode (default)")
    parser.add_argument("--write", action="store_true",
                        help="Write new article folders (default is dry-run)")
    parser.add_argument("--since-hours", type=int, default=72,
                        help="Only fetch records modified in the last N hours")
    parser.add_argument("--record-id",
                        help="Fetch a single Airtable record by ID")
    parser.add_argument("--limit", type=int,
                        help="Limit total records fetched (for testing)")
    parser.add_argument("--allow-no-status-gate", action="store_true",
                        help="Allow ingestion when no Status field is present")
    args = parser.parse_args(argv)

    if args.dry_run and args.write:
        parser.error("--dry-run and --write are mutually exclusive")

    dry_run = not args.write
    schema = _load_schema()

    pat = _env_required("AIRTABLE_PAT")
    base_id = _env_required("AIRTABLE_BASE_ID")
    table_name = _env_required("AIRTABLE_TABLE_NAME")
    view_name = os.environ.get("AIRTABLE_VIEW_NAME", "").strip() or None

    created = 0
    skipped = 0
    invalid = 0
    seen = 0

    try:
        for record in _fetch_records(pat, base_id, table_name, view_name, args.since_hours, args.record_id, args.limit):
            seen += 1
            record_id = record.get("id", "unknown")
            payload = _record_to_payload(record)
            errors, warnings = _validate_payload(payload, schema)

            if errors:
                print(f"[INVALID] {record_id}: {'; '.join(errors)}", file=sys.stderr)
                invalid += 1
                continue

            # Status gate
            status = payload.get("status", "").lower()
            if not status and not args.allow_no_status_gate:
                print(f"[SKIP] {record_id}: no Status field and --allow-no-status-gate not set", file=sys.stderr)
                skipped += 1
                continue
            if status and status not in ALLOWED_STATUSES:
                print(f"[SKIP] {record_id}: status '{status}' not in {ALLOWED_STATUSES}", file=sys.stderr)
                skipped += 1
                continue

            folder, was_created = _write_article(payload, record_id, dry_run)
            if was_created:
                action = "[CREATE]" if not dry_run else "[WOULD CREATE]"
                print(f"{action} {folder}")
                created += 1
            else:
                print(f"[SKIP] {record_id}: folder '{folder}' already exists or title duplicate")
                skipped += 1

    except requests.HTTPError as e:
        print(f"[ERROR] Airtable API failed: {e.response.status_code} {e.response.reason}", file=sys.stderr)
        try:
            body = e.response.json()
            print(f"  {body}", file=sys.stderr)
        except Exception:
            pass
        return 1
    except requests.RequestException as e:
        print(f"[ERROR] Network failure: {e}", file=sys.stderr)
        return 1

    mode = "(dry-run)" if dry_run else ""
    print(f"\nIngested {created} article(s) {mode}")
    print(f"Skipped {skipped} record(s)")
    print(f"Invalid {invalid} record(s)")
    print(f"Total seen {seen} record(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
