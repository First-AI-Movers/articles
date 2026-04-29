#!/usr/bin/env python3
"""Minimal tag normalization stub.

Expand this to map raw tags to canonical topics as your archive grows.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = REPO_ROOT / "articles"


def normalize():
    folders = sorted(p.name for p in ARTICLES_DIR.iterdir() if p.is_dir())
    for folder in folders:
        meta_path = ARTICLES_DIR / folder / "metadata.json"
        if not meta_path.exists():
            continue
        with meta_path.open("r+", encoding="utf-8") as fh:
            meta = json.load(fh)
            changed = False
            # Basic string cleanup
            for key in ("title", "slug", "canonical_url"):
                if key in meta and isinstance(meta[key], str):
                    cleaned = meta[key].strip()
                    if cleaned != meta[key]:
                        meta[key] = cleaned
                        changed = True
            if changed:
                fh.seek(0)
                json.dump(meta, fh, indent=2, ensure_ascii=False)
                fh.truncate()
    print("[normalize] Done")


if __name__ == "__main__":
    normalize()
