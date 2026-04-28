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

class TestTopicIntros:
    """Loader + content contract for tools/topic_intros.json."""

    REQUIRED_TOP_10 = [
        "European SME AI", "AI Strategy", "AI Governance", "AI Productivity Tools",
        "EU AI Act", "AI Workflow Automation", "AI Agents", "Healthcare AI",
        "B2B SaaS Growth", "GDPR & Data Privacy",
    ]

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def test_real_file_loads_with_top_10_topics(self):
        """The committed topic_intros.json covers every top-10 roadmap topic."""
        intros = self._mod()._load_topic_intros()
        for topic in self.REQUIRED_TOP_10:
            assert topic in intros, f"missing intro for {topic}"

    def test_real_file_entries_have_required_fields(self):
        """Each intro must have non-empty lede + at least 3 key themes + why_it_matters."""
        intros = self._mod()._load_topic_intros()
        for topic, obj in intros.items():
            assert obj["lede"], f"empty lede for {topic}"
            assert len(obj["key_themes"]) >= 3, f"need >=3 themes for {topic}"
            assert obj["why_it_matters"], f"empty why_it_matters for {topic}"

    def test_real_file_keys_are_canonical_topics(self):
        """Every topic key must exist in canonical_topics.json — guards against typos."""
        from pathlib import Path as P
        canonical = set(json.loads(
            (P(__file__).resolve().parents[1] / "canonical_topics.json").read_text()
        )["topics"])
        intros = self._mod()._load_topic_intros()
        unknown = set(intros) - canonical
        assert not unknown, f"intros reference non-canonical topics: {unknown}"

    def test_missing_file_returns_empty_dict(self, monkeypatch, tmp_path):
        """A missing intros file degrades silently — site still builds."""
        m = self._mod()
        monkeypatch.setattr(m, "TOPIC_INTROS_PATH", tmp_path / "does-not-exist.json")
        assert m._load_topic_intros() == {}

    def test_malformed_file_returns_empty_dict(self, monkeypatch, tmp_path, capsys):
        """Malformed JSON produces a warning to stderr but does not raise."""
        m = self._mod()
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json")
        monkeypatch.setattr(m, "TOPIC_INTROS_PATH", bad)
        assert m._load_topic_intros() == {}
        captured = capsys.readouterr()
        assert "malformed" in captured.err

    def test_loader_skips_non_dict_entries(self, monkeypatch, tmp_path):
        """Defensive: an intros entry that is not an object is dropped, not crashed on."""
        m = self._mod()
        path = tmp_path / "intros.json"
        path.write_text(json.dumps({
            "version": 1,
            "intros": {
                "Good": {"lede": "ok", "key_themes": ["a"], "why_it_matters": "b"},
                "Bad": "not a dict",
            },
        }))
        monkeypatch.setattr(m, "TOPIC_INTROS_PATH", path)
        result = m._load_topic_intros()
        assert "Good" in result
        assert "Bad" not in result

    def test_loader_normalizes_missing_optional_fields(self, monkeypatch, tmp_path):
        """Missing fields default to empty values rather than raising KeyError."""
        m = self._mod()
        path = tmp_path / "intros.json"
        path.write_text(json.dumps({
            "intros": {"Skeleton": {"lede": "only lede here"}},
        }))
        monkeypatch.setattr(m, "TOPIC_INTROS_PATH", path)
        result = m._load_topic_intros()
        assert result["Skeleton"]["lede"] == "only lede here"
        assert result["Skeleton"]["key_themes"] == []
        assert result["Skeleton"]["why_it_matters"] == ""


# =========================================================================
# Tests: rebuild_local.py llms-recent.txt (30-day slice)
# =========================================================================


