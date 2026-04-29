#!/usr/bin/env python3
"""Series validator: check article metadata against the series registry.

Usage:
    python3 tools/check_series.py
    python3 tools/check_series.py --strict
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = REPO_ROOT / "articles"
REGISTRY_PATH = REPO_ROOT / "tools" / "series_registry.json"


def _load_registry():
    if not REGISTRY_PATH.exists():
        return {}
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return data.get("series", {})


def _validate(articles_dir: Path, registry: dict, strict: bool = False):
    errors = []
    warnings = []
    series_articles = {}  # slug -> list of (folder, order)

    for folder in sorted(articles_dir.iterdir()):
        if not folder.is_dir():
            continue
        meta_path = folder / "metadata.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        series = meta.get("series")
        order = meta.get("series_order")

        if order is not None and series is None:
            errors.append(f"{folder.name}: series_order without series")
            continue

        if series is None:
            continue

        if series not in registry:
            errors.append(f"{folder.name}: unknown series slug '{series}'")
            continue

        if order is None:
            warnings.append(f"{folder.name}: series '{series}' has no series_order")
        elif not isinstance(order, int) or order < 1:
            errors.append(f"{folder.name}: series_order must be a positive integer, got {order!r}")
        else:
            series_articles.setdefault(series, []).append((folder.name, order))

    # Check for duplicate orders within a series
    for series_slug, items in series_articles.items():
        orders = {}
        for folder, order in items:
            if order in orders:
                errors.append(
                    f"{folder}: duplicate series_order {order} in series '{series_slug}' "
                    f"(first seen in {orders[order]})"
                )
            else:
                orders[order] = folder

        if strict:
            # Check for gaps
            if items:
                sorted_orders = sorted(o for _, o in items)
                expected = list(range(1, len(sorted_orders) + 1))
                if sorted_orders != expected:
                    warnings.append(
                        f"series '{series_slug}': order gaps detected "
                        f"(have {sorted_orders}, expected {expected})"
                    )

    return errors, warnings


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate article series metadata")
    parser.add_argument("--articles-dir", default=str(ARTICLES_DIR), help="Directory containing article folders")
    parser.add_argument("--strict", action="store_true", help="Warn on order gaps within series")
    args = parser.parse_args(argv)

    articles_dir = Path(args.articles_dir)
    registry = _load_registry()

    if not registry:
        print("[series] No series defined in registry. Nothing to validate.")
        return 0

    errors, warnings = _validate(articles_dir, registry, strict=args.strict)

    if warnings:
        for w in warnings:
            print(f"[series] WARNING: {w}")

    if errors:
        for e in errors:
            print(f"[series] ERROR: {e}")
        print(f"[series] FAIL: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1

    print(f"[series] OK: {len(registry)} series defined, {len(errors)} error(s), {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
