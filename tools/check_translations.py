#!/usr/bin/env python3
"""Validate optional translations.json sidecars in article folders.

Usage:
    python3 tools/check_translations.py
    python3 tools/check_translations.py --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = REPO_ROOT / "articles"
SCHEMA_PATH = REPO_ROOT / "tools" / "translations_schema.json"

VALID_LANGS = {"es", "fr", "de", "nl", "pt"}
STATUS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _load_schema():
    if not SCHEMA_PATH.exists():
        print(f"[translations] Schema not found: {SCHEMA_PATH}", file=sys.stderr)
        sys.exit(1)
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _find_translation_files():
    if not ARTICLES_DIR.exists():
        return []
    return sorted(ARTICLES_DIR.glob("*/translations.json"))


def validate_file(path: Path, schema: dict):
    """Validate a single translations.json file. Returns (data, errors)."""
    errors = []
    data = None
    try:
        data = json.loads(path.read_text(encoding="utf-8"), strict=False)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {e}")
        return None, errors

    if not isinstance(data, dict):
        errors.append("Root must be an object")
        return data, errors

    # Check for unknown top-level keys
    for key in data:
        if key not in VALID_LANGS:
            errors.append(f"Unknown language code: '{key}' (allowed: {', '.join(sorted(VALID_LANGS))})")

    # Per-language validation
    for lang, entry in data.items():
        if lang not in VALID_LANGS:
            continue  # already reported above
        if not isinstance(entry, dict):
            errors.append(f"[{lang}] Must be an object")
            continue

        status = entry.get("status")
        if status not in ("draft", "published"):
            errors.append(f"[{lang}] status must be 'draft' or 'published', got: {status}")

        # Check for unknown properties
        allowed_props = {"status", "title", "reviewed_at", "reviewer", "model", "source_chars"}
        for prop in entry:
            if prop not in allowed_props:
                errors.append(f"[{lang}] Unknown property: '{prop}'")

        # Published requires additional fields
        if status == "published":
            if not entry.get("title"):
                errors.append(f"[{lang}] status 'published' requires 'title'")
            if not entry.get("reviewed_at"):
                errors.append(f"[{lang}] status 'published' requires 'reviewed_at'")
            else:
                if not STATUS_RE.match(str(entry["reviewed_at"])):
                    errors.append(f"[{lang}] reviewed_at must be YYYY-MM-DD, got: {entry['reviewed_at']}")
            if not entry.get("reviewer"):
                errors.append(f"[{lang}] status 'published' requires 'reviewer'")

    return data, errors


def validate_all():
    schema = _load_schema()
    files = _find_translation_files()
    results = []
    total_errors = 0
    total_entries = 0

    for path in files:
        data, errors = validate_file(path, schema)
        entry_count = len(data) if data else 0
        total_entries += entry_count
        total_errors += len(errors)
        results.append({
            "folder": path.parent.name,
            "path": str(path),
            "entries": entry_count,
            "errors": errors,
        })

    return {
        "files_checked": len(files),
        "entries": total_entries,
        "errors": total_errors,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate article translations.json sidecars")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    report = validate_all()

    if args.json:
        print(json.dumps(report, indent=2))
        return 1 if report["errors"] > 0 else 0

    if report["files_checked"] == 0:
        print("[translations] No translations.json files found — nothing to validate")
        return 0

    for r in report["results"]:
        print(f"[translations] {r['folder']}: {r['entries']} entries")
        for err in r["errors"]:
            print(f"  ERROR: {err}")

    if report["errors"] == 0:
        print(f"[translations] OK: {report['files_checked']} file(s), {report['entries']} entries, 0 errors")
        return 0
    else:
        print(
            f"[translations] FAILED: {report['files_checked']} file(s), {report['entries']} entries, "
            f"{report['errors']} error(s)"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
