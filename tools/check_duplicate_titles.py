#!/usr/bin/env python3
"""Check index.json for duplicate article titles.

Exits with code 1 and prints actionable output when duplicates are found.
Case-insensitive comparison via `.lower()`. Empty or missing titles ignored.

Note: the SOURCE-of-truth duplicate gate is at ingest time
(`tools/ingest_airtable.py::_title_exists`), which uses stricter
normalization (NFKC + dash/quote collapse) so new Airtable records cannot
be admitted with a title that differs from an existing archive entry only
in typography — the E41e issue #156 scenario. This index-level gate stays
on `.lower()` to avoid breaking on a small set of legacy smart-quote-vs-
straight-quote pairs that predate the strict gate; those are tracked as
an editorial cleanup follow-up.

Usage:
    python3 tools/check_duplicate_titles.py
    python3 tools/check_duplicate_titles.py --index path/to/index.json
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=REPO_ROOT / "index.json",
                        help="Path to index.json (default: repo root index.json)")
    args = parser.parse_args()

    index_path = args.index
    if not index_path.exists():
        print("ERROR: index.json not found", file=sys.stderr)
        sys.exit(1)

    index = json.loads(index_path.read_text(encoding="utf-8"))

    from collections import defaultdict
    by_title = defaultdict(list)
    for a in index.get("articles", []):
        title = a.get("title")
        if not title:
            continue
        by_title[title.lower()].append((a.get("folder", ""), a.get("published_date", "")))

    duplicates = [(t, folders) for t, folders in by_title.items() if len(folders) > 1]

    if not duplicates:
        print("OK: no duplicate titles found")
        sys.exit(0)

    print(f"ERROR: {len(duplicates)} duplicate title(s) found:\n", file=sys.stderr)
    for title, folders in sorted(duplicates, key=lambda x: x[0]):
        print(f'  "{title}"', file=sys.stderr)
        for folder, published_date in folders:
            print(f"    - {folder}  ({published_date})", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
