#!/usr/bin/env python3
"""Read-only Airtable <-> archive reconciliation (no writes, no backfill).

Surfaces eligible `Posted` Airtable records that are ABSENT from the repository
archive — the silent acquisition backlog that the daily 72-hour cron window can
permanently miss (a record whose LAST_MODIFIED_TIME ages past 72h without being
re-saved drops out of the cron's `IS_AFTER(LAST_MODIFIED_TIME(), now-72h)`
filter forever, and nothing else surfaces it).

This tool NEVER writes to Airtable or the repo, opens no PR, and performs no
backfill. It reuses `ingest_airtable`'s exact field mapping, schema validation,
and status gate so a record it counts as `eligible` / `invalid` /
`status_skipped` is classified identically to the real ingestion path.

Identity is the strongest stable pair the archive records: the Airtable record
id (`metadata.json.id`) and the normalized canonical URL (`metadata.json.
canonical_url`). Both are already public (committed in this public repo), so
comparing Posted records is public-safe.

Output is value-safe COUNTS by default. Raw article titles/bodies are never
emitted. Missing record ids (already public) are printed only under
`--emit-missing-ids`.

Environment (same as ingest_airtable):
    AIRTABLE_PAT, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_VIEW_NAME

Usage:
    python3 tools/audit_airtable_reconciliation.py            # full-view scan
    python3 tools/audit_airtable_reconciliation.py --since-hours 72
    python3 tools/audit_airtable_reconciliation.py --json
    python3 tools/audit_airtable_reconciliation.py --summary-file "$GITHUB_STEP_SUMMARY"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Reuse the exact ingestion contract (field map, validation, status gate,
# canonical-URL normalization, fetch) so the reconciliation counts mean the
# same thing as ingestion. Importing runs only module-level constant setup.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ingest_airtable as ing  # noqa: E402


def build_archive_index(articles_dir: Path) -> dict:
    """Return {'ids': set, 'urls': set, 'titles': set} of ingested Airtable
    record ids, normalized canonical URLs, and normalized titles from every
    articles/*/metadata.json.

    Titles are included because an upstream record can be re-created with a NEW
    Airtable id AND a drifted canonical URL (e.g. a beehiiv slug that gained or
    lost its hash suffix) while the article is ALREADY published. Matching on id
    or canonical URL alone then mis-reports such a record as MISSING even though
    its content is present. The normalized title is a stable content key here
    (archive titles are unique and ingestion's own writer already refuses to
    create a duplicate title), so it closes that identity-drift gap.
    """
    ids: set[str] = set()
    urls: set[str] = set()
    titles: set[str] = set()
    if not articles_dir.exists():
        return {"ids": ids, "urls": urls, "titles": titles}
    for p in articles_dir.iterdir():
        if not p.is_dir():
            continue
        meta = p / "metadata.json"
        if not meta.exists():
            continue
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        rid = str(data.get("id", "")).strip()
        if rid:
            ids.add(rid)
        cu = data.get("canonical_url", "")
        if cu:
            urls.add(ing._normalize_canonical_url(cu))
        t = ing._normalize_title(data.get("title", ""))
        if t:
            titles.add(t)
    return {"ids": ids, "urls": urls, "titles": titles}


def reconcile(records, archive, schema, *, allow_no_status_gate=False):
    """Pure reconciliation. Returns (counts dict, missing_record_ids list).

    Classification mirrors ingest_airtable.main():
      invalid          — fails schema validation (would be skipped as invalid)
      status_skipped   — no/other status (not in ALLOWED_STATUSES)
      eligible         — Posted + valid (would be a create candidate)
        eligible_present — already in the archive (by record id or canonical URL)
        eligible_missing — NOT in the archive by either identity (the backlog)
    """
    counts = {
        "fetched": 0,
        "invalid": 0,
        "status_skipped": 0,
        "eligible": 0,
        "eligible_present": 0,
        "eligible_missing": 0,
    }
    missing_ids: list[str] = []
    for rec in records:
        counts["fetched"] += 1
        rid = str(rec.get("id", "")).strip()
        payload = ing._record_to_payload(rec)
        errors, _ = ing._validate_payload(payload, schema)
        if errors:
            counts["invalid"] += 1
            continue
        status = (payload.get("status") or "").lower()
        if not status and not allow_no_status_gate:
            counts["status_skipped"] += 1
            continue
        if status and status not in ing.ALLOWED_STATUSES:
            counts["status_skipped"] += 1
            continue
        counts["eligible"] += 1
        url = ing._normalize_canonical_url(payload.get("canonical_url", ""))
        title = ing._normalize_title(payload.get("title", ""))
        archive_titles = archive.get("titles", set())
        # Present if the archive already has this record by ANY stable identity:
        # record id, normalized canonical URL, OR normalized title. The title
        # check catches re-created records whose id AND canonical URL drifted
        # but whose article is already published (identity-drift false-missing).
        if ((rid and rid in archive["ids"])
                or (url and url in archive["urls"])
                or (title and title in archive_titles)):
            counts["eligible_present"] += 1
        else:
            counts["eligible_missing"] += 1
            if rid:
                missing_ids.append(rid)
    return counts, missing_ids


def _render_summary(counts: dict, *, since_hours) -> str:
    scope = f"last {since_hours}h" if since_hours else "full view"
    return (
        "## Airtable ingestion reconciliation\n\n"
        f"- Scope: {scope}\n"
        f"- Archive articles: {counts.get('archive_articles', 0)}\n"
        f"- Airtable records fetched: {counts['fetched']}\n"
        f"- Eligible (Posted + valid): {counts['eligible']}\n"
        f"- Eligible present in archive: {counts['eligible_present']}\n"
        f"- **Eligible MISSING from archive: {counts['eligible_missing']}**\n"
        f"- Status-skipped: {counts['status_skipped']}\n"
        f"- Invalid (schema): {counts['invalid']}\n"
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Read-only Airtable <-> archive reconciliation (counts only)."
    )
    parser.add_argument(
        "--since-hours", type=int, default=None,
        help="Restrict to records modified in the last N hours (default: full view).",
    )
    parser.add_argument("--json", action="store_true", help="Emit counts as JSON.")
    parser.add_argument(
        "--emit-missing-ids", action="store_true",
        help="Also print missing Airtable record ids (already public in metadata.json).",
    )
    parser.add_argument(
        "--allow-no-status-gate", action="store_true",
        help="Count records with no status as eligible (mirrors ingest's flag).",
    )
    parser.add_argument(
        "--summary-file",
        help="Append a value-safe markdown summary to this path (e.g. $GITHUB_STEP_SUMMARY).",
    )
    args = parser.parse_args(argv)

    schema = ing._load_schema()
    pat = ing._env_required("AIRTABLE_PAT")
    base_id = ing._env_required("AIRTABLE_BASE_ID")
    table_name = ing._env_required("AIRTABLE_TABLE_NAME")
    view_name = os.environ.get("AIRTABLE_VIEW_NAME", "").strip() or None

    try:
        records = list(
            ing._fetch_records(
                pat, base_id, table_name, view_name,
                since_hours=args.since_hours, record_id=None, limit=None,
            )
        )
    except Exception as e:  # noqa: BLE001 — surface the failure without a token in the message
        print(f"[ERROR] Airtable fetch failed: {type(e).__name__}", file=sys.stderr)
        return 1

    archive = build_archive_index(ing.ARTICLES_DIR)
    counts, missing_ids = reconcile(
        records, archive, schema, allow_no_status_gate=args.allow_no_status_gate
    )
    counts["archive_articles"] = len(archive["ids"])

    if args.json:
        print(json.dumps(counts, indent=2))
    else:
        print(_render_summary(counts, since_hours=args.since_hours).replace("**", ""))
    if args.emit_missing_ids and missing_ids:
        print("missing_record_ids:")
        for rid in missing_ids:
            print(f"  {rid}")

    if args.summary_file:
        try:
            with open(args.summary_file, "a", encoding="utf-8") as fh:
                fh.write(_render_summary(counts, since_hours=args.since_hours))
        except OSError as e:
            print(f"[warn] could not write summary file: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
