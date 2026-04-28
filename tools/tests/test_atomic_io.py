#!/usr/bin/env python3
"""Tests for <MODULE>."""

import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from xml.etree.ElementTree import fromstring

import pytest

class TestAtomicWrites:
    """Atomic file-write helper contracts."""

    def test_atomic_write_json_produces_valid_json(self, tmp_path):
        from _atomic_io import atomic_write_json
        path = tmp_path / "test.json"
        atomic_write_json(path, {"key": "value", "num": 42})
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data == {"key": "value", "num": 42}

    def test_atomic_write_json_preserves_indent_and_newline(self, tmp_path):
        from _atomic_io import atomic_write_json
        path = tmp_path / "test.json"
        atomic_write_json(path, {"a": 1})
        text = path.read_text(encoding="utf-8")
        assert text.startswith("{\n")
        assert text.endswith("\n")

    def test_atomic_write_text_produces_readable_text(self, tmp_path):
        from _atomic_io import atomic_write_text
        path = tmp_path / "test.txt"
        atomic_write_text(path, "hello world\n")
        assert path.read_text(encoding="utf-8") == "hello world\n"

    def test_atomic_write_preserves_existing_file_if_temp_fails(self, monkeypatch, tmp_path):
        """Simulate a failure during temp write: existing file must survive."""
        from _atomic_io import atomic_write_text
        path = tmp_path / "target.txt"
        path.write_text("original", encoding="utf-8")

        real_write_text = type(path).write_text
        def failing_write_text(self, *args, **kwargs):
            if self.name.endswith(".tmp"):
                raise OSError("disk full")
            return real_write_text(self, *args, **kwargs)

        monkeypatch.setattr(type(path), "write_text", failing_write_text)
        with pytest.raises(OSError, match="disk full"):
            atomic_write_text(path, "new content")
        assert path.read_text(encoding="utf-8") == "original"

    def test_atomic_write_json_uses_utf8(self, tmp_path):
        from _atomic_io import atomic_write_json
        path = tmp_path / "test.json"
        atomic_write_json(path, {"emoji": "🚀", "euro": "€"})
        text = path.read_text(encoding="utf-8")
        assert "🚀" in text
        assert "€" in text


# =========================================================================
# Tests: E11 accessibility — skip link, landmarks, focus, theme toggle
# =========================================================================


