#!/usr/bin/env python3
"""Validate optional errata.md files in article folders.

Usage:
    python3 tools/check_errata.py
    python3 tools/check_errata.py --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = REPO_ROOT / "articles"

VALID_TYPES = {"correction", "clarification", "source-update", "retraction", "editorial-note"}
VALID_STATUSES = {"draft", "published"}
ERRATA_H1_RE = re.compile(r"^#\s+Errata\s*$", re.IGNORECASE)
ENTRY_HEADING_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s+[-—]\s+(.+)$")
BAD_ENTRY_HEADING_RE = re.compile(r"^##\s+(.+)$")
FIELD_RE = re.compile(r"^([A-Za-z][A-Za-z\s-]*):\s*(.*)$")


def _find_errata_files():
    if not ARTICLES_DIR.exists():
        return []
    return sorted(ARTICLES_DIR.glob("*/errata.md"))


def _parse_errata(text: str, path: Path):
    errors = []
    lines = text.splitlines()
    if not lines:
        errors.append("File is empty")
        return [], errors

    if not ERRATA_H1_RE.match(lines[0]):
        errors.append("File must start with '# Errata'")

    entries = []
    current = None
    for i, line in enumerate(lines[1:], start=2):
        m = ENTRY_HEADING_RE.match(line)
        if m:
            if current:
                entries.append(current)
            current = {
                "date": m.group(1),
                "title": m.group(2).strip(),
                "type": None,
                "status": None,
                "editor": None,
                "body_lines": [],
                "line": i,
            }
            continue

        bad = BAD_ENTRY_HEADING_RE.match(line)
        if bad:
            errors.append(f"Line {i}: entry heading must use '## YYYY-MM-DD — Title' format")
            continue

        if current is None:
            continue

        fm = FIELD_RE.match(line)
        if fm:
            key = fm.group(1).strip().lower().replace(" ", "-").replace("_", "-")
            val = fm.group(2).strip()
            if key == "type":
                current["type"] = val
            elif key == "status":
                current["status"] = val
            elif key == "editor":
                current["editor"] = val
            else:
                current["body_lines"].append(line)
        else:
            current["body_lines"].append(line)

    if current:
        entries.append(current)

    for e in entries:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", e["date"]):
            errors.append(f"Entry '{e['title']}' (line {e['line']}): date must be YYYY-MM-DD")
        if e["type"] is None:
            errors.append(f"Entry '{e['title']}' (line {e['line']}): missing Type field")
        elif e["type"] not in VALID_TYPES:
            errors.append(
                f"Entry '{e['title']}' (line {e['line']}): invalid type '{e['type']}'. "
                f"Allowed: {', '.join(sorted(VALID_TYPES))}"
            )
        if e["status"] is None:
            errors.append(f"Entry '{e['title']}' (line {e['line']}): missing Status field")
        elif e["status"] not in VALID_STATUSES:
            errors.append(
                f"Entry '{e['title']}' (line {e['line']}): invalid status '{e['status']}'. "
                f"Allowed: {', '.join(sorted(VALID_STATUSES))}"
            )
        if e["editor"] is None:
            errors.append(f"Entry '{e['title']}' (line {e['line']}): missing Editor field")

    return entries, errors


def validate_all():
    files = _find_errata_files()
    results = []
    total_errors = 0
    total_entries = 0

    for path in files:
        text = path.read_text(encoding="utf-8")
        entries, errors = _parse_errata(text, path)
        total_entries += len(entries)
        total_errors += len(errors)
        results.append({
            "folder": path.parent.name,
            "path": str(path),
            "entries": len(entries),
            "errors": errors,
        })

    return {
        "files_checked": len(files),
        "entries": total_entries,
        "errors": total_errors,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate article errata files")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    report = validate_all()

    if args.json:
        print(json.dumps(report, indent=2))
        return 1 if report["errors"] > 0 else 0

    if report["files_checked"] == 0:
        print("[errata] No errata files found — nothing to validate")
        return 0

    for r in report["results"]:
        print(f"[errata] {r['folder']}: {r['entries']} entries")
        for err in r["errors"]:
            print(f"  ERROR: {err}")

    if report["errors"] == 0:
        print(f"[errata] OK: {report['files_checked']} file(s), {report['entries']} entries, 0 errors")
        return 0
    else:
        print(
            f"[errata] FAILED: {report['files_checked']} file(s), {report['entries']} entries, "
            f"{report['errors']} error(s)"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
