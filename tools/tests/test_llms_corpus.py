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

class TestBuildLlmsFull:
    """Full-corpus concatenation for LLM ingestion."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def _run(self, monkeypatch, tmp_path, articles_on_disk=None):
        """Build llms-full.txt against a synthetic corpus."""
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        index = {"articles": []}
        for spec in (articles_on_disk or []):
            folder = spec["folder"]
            (tmp_path / "articles" / folder).mkdir(exist_ok=True)
            (tmp_path / "articles" / folder / "article.md").write_text(
                spec.get("body", f"---\ntitle: {spec['title']}\n---\n# {spec['title']}\n\nBody of {folder}.\n"))
            index["articles"].append({
                "folder": folder,
                "title": spec["title"],
                "published_date": spec["published_date"],
                "tags": spec.get("tags", []),
                "topics": spec.get("topics", []),
                "funnel_stage": "middle",
                "canonical_url": spec.get("canonical_url", f"https://radar.firstaimovers.com/{folder}"),
            })
        index["articles"].sort(key=lambda a: a["published_date"], reverse=True)
        m.build_llms_full(index)
        return (tmp_path / "llms-full.txt").read_text(encoding="utf-8")

    def test_header_contains_corpus_metadata(self, monkeypatch, tmp_path):
        out = self._run(monkeypatch, tmp_path, [
            {"folder": "2026-01-01-first", "title": "First", "published_date": "2026-01-01"},
        ])
        assert "First AI Movers — Full Article Archive" in out
        assert "CC BY 4.0" in out
        assert "ORCID 0000-0002-6813-4641" in out

    def test_articles_emitted_newest_first(self, monkeypatch, tmp_path):
        out = self._run(monkeypatch, tmp_path, [
            {"folder": "2025-06-01-older", "title": "Older Article", "published_date": "2025-06-01"},
            {"folder": "2026-04-01-newer", "title": "Newer Article", "published_date": "2026-04-01"},
        ])
        assert out.index("Newer Article") < out.index("Older Article")

    def test_per_entry_header_has_title_date_url_topics(self, monkeypatch, tmp_path):
        out = self._run(monkeypatch, tmp_path, [
            {"folder": "2026-04-01-x", "title": "The Title", "published_date": "2026-04-01",
             "topics": ["AI Strategy", "European SME AI"],
             "canonical_url": "https://radar.firstaimovers.com/the-title"},
        ])
        assert "# The Title" in out
        assert "**Published:** 2026-04-01" in out
        assert "**URL:** https://radar.firstaimovers.com/the-title" in out
        assert "**Topics:** AI Strategy, European SME AI" in out

    def test_leading_h1_in_body_is_stripped(self, monkeypatch, tmp_path):
        out = self._run(monkeypatch, tmp_path, [
            {"folder": "2026-04-01-x", "title": "The Title", "published_date": "2026-04-01",
             "body": "---\ntitle: x\n---\n# Duplicate Heading\n\nBody text here."},
        ])
        # Only the emitted header H1 should be present; body's H1 stripped
        assert out.count("# Duplicate Heading") == 0
        assert "Body text here." in out

    def test_missing_article_md_is_skipped_not_fatal(self, monkeypatch, tmp_path):
        m = self._mod()
        (tmp_path / "articles").mkdir()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        # Folder referenced in index but no file on disk
        index = {"articles": [
            {"folder": "ghost", "title": "Ghost", "published_date": "2026-01-01",
             "tags": [], "canonical_url": "https://radar.firstaimovers.com/ghost"},
        ]}
        m.build_llms_full(index)  # must not raise
        out = (tmp_path / "llms-full.txt").read_text(encoding="utf-8")
        assert "Ghost" not in out  # skipped entirely
        assert "Articles: 1" in out  # header still computed from index total

    def test_newline_canonical_is_cleaned(self, monkeypatch, tmp_path):
        """LinkedIn-batch articles have newlines inside the canonical_url value."""
        out = self._run(monkeypatch, tmp_path, [
            {"folder": "2026-01-21-x", "title": "LinkedIn One",
             "published_date": "2026-01-21",
             "canonical_url": "\nhttps://www.linkedin.com/pulse/linkedin-one\n"},
        ])
        assert "**URL:** https://www.linkedin.com/pulse/linkedin-one" in out


# =========================================================================
# Tests: normalize_tags.py — tag -> topic normalization
# =========================================================================


class TestBuildLlmsRecent:
    """Rolling window sibling of llms-full.txt."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def _run(self, monkeypatch, tmp_path, articles_on_disk):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        index = {"articles": []}
        for spec in articles_on_disk:
            folder = spec["folder"]
            (tmp_path / "articles" / folder).mkdir(exist_ok=True)
            (tmp_path / "articles" / folder / "article.md").write_text(
                f"---\ntitle: {spec['title']}\n---\n# {spec['title']}\n\nBody of {folder}.\n")
            index["articles"].append({
                "folder": folder,
                "title": spec["title"],
                "published_date": spec["published_date"],
                "tags": [], "topics": [],
                "funnel_stage": "middle",
                "canonical_url": f"https://radar.firstaimovers.com/{folder}",
            })
        index["articles"].sort(key=lambda a: a["published_date"], reverse=True)
        m.build_llms_recent(index)
        return (tmp_path / "llms-recent.txt").read_text(encoding="utf-8")

    def test_filters_to_window_relative_to_newest_not_today(self, monkeypatch, tmp_path):
        # Articles spanning 60 days; window should be 30 days back from newest.
        articles = [
            {"folder": "2026-04-20-new", "title": "NewArticle", "published_date": "2026-04-20"},
            {"folder": "2026-04-05-mid", "title": "MidArticle", "published_date": "2026-04-05"},
            {"folder": "2026-02-20-old", "title": "OldArticle", "published_date": "2026-02-20"},
        ]
        out = self._run(monkeypatch, tmp_path, articles)
        assert "NewArticle" in out
        assert "MidArticle" in out  # within 30 days of 2026-04-20
        assert "OldArticle" not in out  # 2026-02-20 is 59 days before newest

    def test_header_reports_window_count(self, monkeypatch, tmp_path):
        out = self._run(monkeypatch, tmp_path, [
            {"folder": "2026-04-20-a", "title": "A", "published_date": "2026-04-20"},
            {"folder": "2026-04-15-b", "title": "B", "published_date": "2026-04-15"},
        ])
        assert "Articles in window: 2" in out
        assert "Window: 2026-03-21 to 2026-04-20" in out

    def test_empty_index_writes_empty_file(self, monkeypatch, tmp_path):
        out = self._run(monkeypatch, tmp_path, [])
        assert out == ""

    def test_window_size_is_30_days(self):
        m = self._mod()
        assert m.LLMS_RECENT_DAYS == 30


# =========================================================================
# Tests: rebuild_local.py TL;DR extraction for Quick reads (E4)
# =========================================================================


class TestLlmsFullStability:
    """Prove llms-full.txt is deterministic for fixed input and fixed date."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def test_llms_full_identical_across_builds_for_fixed_date(self, monkeypatch, tmp_path):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        index = {"articles": [
            {"folder": "2026-04-01-a", "title": "A", "published_date": "2026-04-01",
             "tags": [], "topics": ["AI Strategy"],
             "canonical_url": "https://radar.firstaimovers.com/a"},
            {"folder": "2026-03-01-b", "title": "B", "published_date": "2026-03-01",
             "tags": [], "topics": ["AI Strategy"],
             "canonical_url": "https://radar.firstaimovers.com/b"},
        ]}
        for a in index["articles"]:
            d = tmp_path / "articles" / a["folder"]
            d.mkdir(exist_ok=True)
            (d / "article.md").write_text(f"---\ntitle: {a['title']}\n---\n# {a['title']}\n\nBody.\n")

        class _FixedDate:
            @staticmethod
            def today(): return __import__("datetime").date(2026, 4, 1)
            @classmethod
            def __getattr__(cls, name): return getattr(__import__("datetime").date, name)

        monkeypatch.setattr(m, "date", _FixedDate())
        m.build_llms_full(index)
        first = (tmp_path / "llms-full.txt").read_text(encoding="utf-8")
        m.build_llms_full(index)
        second = (tmp_path / "llms-full.txt").read_text(encoding="utf-8")
        assert first == second

    def test_llms_recent_identical_across_builds_for_fixed_date(self, monkeypatch, tmp_path):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        index = {"articles": [
            {"folder": "2026-04-01-a", "title": "A", "published_date": "2026-04-01",
             "tags": [], "topics": [], "canonical_url": "https://radar.firstaimovers.com/a"},
        ]}
        for a in index["articles"]:
            d = tmp_path / "articles" / a["folder"]
            d.mkdir(exist_ok=True)
            (d / "article.md").write_text(f"---\ntitle: {a['title']}\n---\n# {a['title']}\n\nBody.\n")

        class _FixedDate:
            @staticmethod
            def today(): return __import__("datetime").date(2026, 4, 1)
            @classmethod
            def __getattr__(cls, name): return getattr(__import__("datetime").date, name)

        monkeypatch.setattr(m, "date", _FixedDate())
        m.build_llms_recent(index)
        first = (tmp_path / "llms-recent.txt").read_text(encoding="utf-8")
        m.build_llms_recent(index)
        second = (tmp_path / "llms-recent.txt").read_text(encoding="utf-8")
        assert first == second


# =========================================================================
# Tests: E8 hardening — XSS resistance
# =========================================================================


