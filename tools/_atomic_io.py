#!/usr/bin/env python3
"""Atomic file-write helpers for metadata and generated artifacts.

Writes to a same-directory temp file, then replaces the target atomically.
This prevents partial writes from leaving corrupted metadata JSON or
truncated generated files if a process is killed mid-write.
"""

import json
from pathlib import Path


def atomic_write_text(path, content, encoding="utf-8"):
    """Write `content` to `path` atomically via a same-directory temp file.

    Uses Path.replace() which is atomic on the same filesystem.
    """
    path = Path(path)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(content, encoding=encoding)
    temp.replace(path)


def atomic_write_json(path, data, indent=2, ensure_ascii=False):
    """Serialize `data` to JSON and write atomically.

    Preserves the repo convention: 2-space indent, ensure_ascii=False,
    trailing newline.
    """
    text = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
    if not text.endswith("\n"):
        text += "\n"
    atomic_write_text(path, text)
