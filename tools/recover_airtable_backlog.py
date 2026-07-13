#!/usr/bin/env python3
"""Bounded, deterministic recovery of the aged-out `Posted` Airtable backlog.

Read-selects the OLDEST valid `Posted` records that are ABSENT from the archive
— the backlog the daily 72-hour cron window can never re-reach (a record whose
LAST_MODIFIED_TIME ages past 72h without a re-save drops out of the
`IS_AFTER(LAST_MODIFIED_TIME(), now-72h)` filter permanently) — and, with
``--apply``, writes their article folders in bounded batches.

This tool NEVER writes to Airtable and NEVER opens a PR. It reuses
``ingest_airtable``'s exact field map / schema validation / status gate / article
writer and ``audit_airtable_reconciliation``'s archive index + classification, so
a record it recovers is byte-identical to one the daily ingestion path would have
created. A companion workflow rebuilds deterministic artifacts and opens the
batch PR; the operator/AI exact-head merges it.

Determinism & safety:
  * Batch is hard-capped at ``HARD_MAX_BATCH`` (5) creates — a larger
    ``--batch-size`` is a hard error, not a silent clamp.
  * Selection order is deterministic (oldest ``published_date`` first, record-id
    tiebreak), so an interrupted run resumes safely and the same backlog state
    always yields the same next batch.
  * ``ingest_airtable._write_article`` is idempotent (skips on existing folder /
    duplicate title / duplicate canonical URL), so re-running never double-writes.
  * Only ``Posted`` + schema-valid records absent from the archive by BOTH record
    id and normalized canonical URL are recoverable. Invalid / blank-canonical /
    status-skipped / already-present records are excluded (and never mutated).

Public-safety: stdout / summary emit value-safe COUNTS and already-public
identifiers only (record id and canonical URL are committed in every
metadata.json in this public repo; slug/folder derive from them). Article titles
and bodies are NEVER printed.

Environment (same as ingest_airtable):
    AIRTABLE_PAT, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_VIEW_NAME

Usage:
    python3 tools/recover_airtable_backlog.py                     # dry-run, batch of 5
    python3 tools/recover_airtable_backlog.py --batch-size 5 --apply
    python3 tools/recover_airtable_backlog.py --json --summary-file "$GITHUB_STEP_SUMMARY"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Reuse the exact ingestion + reconciliation contracts (field map, validation,
# status gate, canonical-URL normalization, writer, archive index) so a recovered
# record is classified and written identically to the real ingestion path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ingest_airtable as ing  # noqa: E402
import audit_airtable_reconciliation as recon  # noqa: E402

HARD_MAX_BATCH = 5


def find_recoverable(records, archive, schema, *, allow_no_status_gate=False):
    """Return the deterministic oldest-first list of recoverable records.

    Each item is a dict with only public-safe identifiers plus the full payload
    (payload is consumed by the writer; it is never printed):
        {record_id, payload, published_date, slug, canonical_url}

    Classification mirrors ingest_airtable.main() / reconcile(): a record is
    recoverable iff it is Posted (or blank-status under allow_no_status_gate),
    passes schema validation, and is ABSENT from the archive by both record id
    and normalized canonical URL.
    """
    candidates = []
    for rec in records:
        rid = str(rec.get("id", "")).strip()
        payload = ing._record_to_payload(rec)
        errors, _ = ing._validate_payload(payload, schema)
        if errors:
            continue
        status = (payload.get("status") or "").lower()
        if not status and not allow_no_status_gate:
            continue
        if status and status not in ing.ALLOWED_STATUSES:
            continue
        url = ing._normalize_canonical_url(payload.get("canonical_url", ""))
        present = (rid and rid in archive["ids"]) or (url and url in archive["urls"])
        if present:
            continue
        candidates.append(
            {
                "record_id": rid,
                "payload": payload,
                "published_date": payload.get("published_date", ""),
                "slug": payload.get("slug", ""),
                "canonical_url": payload.get("canonical_url", ""),
            }
        )
    # Deterministic oldest-first: published_date ascending, record-id tiebreak.
    candidates.sort(key=lambda c: (c["published_date"], c["record_id"]))
    return candidates


def select_batch(candidates, batch_size):
    """Slice the oldest ``batch_size`` candidates. Hard-fails on an over-cap size."""
    if batch_size < 1:
        raise ValueError("batch_size must be >= 1")
    if batch_size > HARD_MAX_BATCH:
        raise ValueError(
            f"batch_size {batch_size} exceeds hard maximum {HARD_MAX_BATCH}"
        )
    return candidates[:batch_size]


def apply_batch(selected, *, dry_run):
    """Write (or, in dry-run, would-write) each selected record's article folder.

    Returns a list of public-safe result dicts. Never writes Airtable.
    """
    results = []
    for item in selected:
        folder, created = ing._write_article(item["payload"], item["record_id"], dry_run)
        results.append(
            {
                "record_id": item["record_id"],
                "slug": item["slug"],
                "published_date": item["published_date"],
                "canonical_url": item["canonical_url"],
                "folder": folder,
                "created": bool(created),
            }
        )
    return results


def _counts(records, candidates, selected, results, *, dry_run):
    created = sum(1 for r in results if r["created"])
    return {
        "fetched": len(records),
        "recoverable_backlog": len(candidates),
        "batch_selected": len(selected),
        "created": created,
        "skipped_existing": len(results) - created,
        "remaining_after_batch": max(0, len(candidates) - created),
        "dry_run": bool(dry_run),
    }


def _render_summary(counts) -> str:
    mode = "dry-run" if counts["dry_run"] else "apply"
    return (
        "## Airtable backlog recovery\n\n"
        f"- Mode: {mode}\n"
        f"- Airtable records fetched: {counts['fetched']}\n"
        f"- Recoverable backlog (valid Posted, missing): {counts['recoverable_backlog']}\n"
        f"- Batch selected: {counts['batch_selected']}\n"
        f"- **Created this batch: {counts['created']}**\n"
        f"- Skipped (already present): {counts['skipped_existing']}\n"
        f"- Remaining backlog after batch: {counts['remaining_after_batch']}\n"
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Bounded, deterministic Airtable backlog recovery (never writes Airtable)."
    )
    parser.add_argument(
        "--batch-size", type=int, default=HARD_MAX_BATCH,
        help=f"Records to recover this run (1..{HARD_MAX_BATCH}; hard max {HARD_MAX_BATCH}).",
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write article folders. Default is dry-run (selects and reports only).",
    )
    parser.add_argument(
        "--allow-no-status-gate", action="store_true",
        help="Treat blank-status records as eligible (mirrors ingest's flag).",
    )
    parser.add_argument(
        "--manifest-file",
        help="Write a detailed JSON manifest (public-safe identifiers) to this path.",
    )
    parser.add_argument(
        "--summary-file",
        help="Append a value-safe markdown summary (e.g. $GITHUB_STEP_SUMMARY).",
    )
    parser.add_argument("--json", action="store_true", help="Emit counts + selection as JSON.")
    args = parser.parse_args(argv)

    # Validate the cap BEFORE any network call so an over-cap request fails fast.
    try:
        _ = select_batch([], args.batch_size)
    except ValueError as e:
        parser.error(str(e))

    schema = ing._load_schema()
    pat = ing._env_required("AIRTABLE_PAT")
    base_id = ing._env_required("AIRTABLE_BASE_ID")
    table_name = ing._env_required("AIRTABLE_TABLE_NAME")
    view_name = os.environ.get("AIRTABLE_VIEW_NAME", "").strip() or None

    try:
        records = list(
            ing._fetch_records(
                pat, base_id, table_name, view_name,
                since_hours=None, record_id=None, limit=None,
            )
        )
    except Exception as e:  # noqa: BLE001 — surface type only; never a token-bearing message
        print(f"[ERROR] Airtable fetch failed: {type(e).__name__}", file=sys.stderr)
        return 1

    archive = recon.build_archive_index(ing.ARTICLES_DIR)
    candidates = find_recoverable(
        records, archive, schema, allow_no_status_gate=args.allow_no_status_gate
    )
    selected = select_batch(candidates, args.batch_size)
    results = apply_batch(selected, dry_run=not args.apply)
    counts = _counts(records, candidates, selected, results, dry_run=not args.apply)

    if args.json:
        print(json.dumps({"counts": counts, "selection": results}, indent=2, ensure_ascii=False))
    else:
        print(_render_summary(counts).replace("**", ""))
        for r in results:
            action = "[CREATED]" if r["created"] else "[SKIP-EXISTS]"
            if counts["dry_run"]:
                action = "[WOULD-CREATE]" if r["created"] else "[SKIP-EXISTS]"
            print(f"  {action} {r['folder']}  id={r['record_id']}")

    if args.manifest_file:
        try:
            Path(args.manifest_file).write_text(
                json.dumps({"counts": counts, "selection": results}, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except OSError as e:
            print(f"[warn] could not write manifest file: {e}", file=sys.stderr)

    if args.summary_file:
        try:
            with open(args.summary_file, "a", encoding="utf-8") as fh:
                fh.write(_render_summary(counts))
        except OSError as e:
            print(f"[warn] could not write summary file: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
