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

class TestDuplicateTitles:
    """Duplicate-title detection logic."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def test_no_duplicates_returns_empty(self):
        m = self._mod()
        index = {"articles": [
            {"folder": "a", "title": "Alpha"},
            {"folder": "b", "title": "Beta"},
        ]}
        assert m.check_duplicate_titles(index) == []

    def test_detects_duplicate_titles_case_insensitive(self):
        m = self._mod()
        index = {"articles": [
            {"folder": "a", "title": "Alpha", "published_date": "2026-04-01"},
            {"folder": "b", "title": "alpha", "published_date": "2026-04-02"},
        ]}
        dups = m.check_duplicate_titles(index)
        assert len(dups) == 1
        title, folders = dups[0]
        assert title == "alpha"
        assert sorted(folders) == [("a", "2026-04-01"), ("b", "2026-04-02")]

    def test_empty_titles_ignored(self):
        m = self._mod()
        index = {"articles": [
            {"folder": "a", "title": ""},
            {"folder": "b", "title": None},
            {"folder": "c", "title": "Real"},
        ]}
        assert m.check_duplicate_titles(index) == []

    def test_script_exits_zero_when_clean(self, tmp_path):
        index = {"articles": [
            {"folder": "a", "title": "Unique", "published_date": "2026-04-01"},
        ]}
        idx = tmp_path / "index.json"
        idx.write_text(json.dumps(index), encoding="utf-8")
        script = Path(__file__).resolve().parents[1] / "check_duplicate_titles.py"
        import subprocess
        result = subprocess.run(
            [sys.executable, str(script), "--index", str(idx)],
            capture_output=True, text=True)
        assert result.returncode == 0
        assert "no duplicate" in result.stdout.lower()

    def test_script_exits_one_with_context(self, tmp_path):
        index = {"articles": [
            {"folder": "2026-04-01-a", "title": "Same", "published_date": "2026-04-01"},
            {"folder": "2026-03-01-b", "title": "Same", "published_date": "2026-03-01"},
        ]}
        idx = tmp_path / "index.json"
        idx.write_text(json.dumps(index), encoding="utf-8")
        script = Path(__file__).resolve().parents[1] / "check_duplicate_titles.py"
        import subprocess
        result = subprocess.run(
            [sys.executable, str(script), "--index", str(idx)],
            capture_output=True, text=True)
        assert result.returncode == 1
        assert "2026-04-01-a" in result.stderr
        assert "2026-03-01-b" in result.stderr


# =========================================================================
# Tests: E8 hardening — feed byte-stability
# =========================================================================


