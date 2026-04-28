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

class TestExtractTldr:
    """TL;DR extraction from article markdown — existing content only, no generation."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def _write_article(self, tmp_path, folder, text):
        d = tmp_path / "articles" / folder
        d.mkdir(parents=True, exist_ok=True)
        (d / "article.md").write_text(text, encoding="utf-8")

    def test_extract_tldr_blockquote_format(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        self._write_article(tmp_path, "2026-04-01-test",
            "---\ntitle: Test\n---\n# Title\n\n> **TL;DR:** This is the summary.\n\nBody here.")
        assert m._extract_tldr("2026-04-01-test") == "This is the summary."

    def test_extract_tldr_heading_format(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        self._write_article(tmp_path, "2026-04-01-test",
            "---\ntitle: Test\n---\n# Title\n\n## TL;DR\n\nSummary paragraph.\n\nBody here.")
        assert m._extract_tldr("2026-04-01-test") == "Summary paragraph."

    def test_extract_tldr_multiline_blockquote(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        self._write_article(tmp_path, "2026-04-01-test",
            "---\ntitle: Test\n---\n# Title\n\n> **TL;DR:** Line one.\n> Line two.\n\nBody here.")
        result = m._extract_tldr("2026-04-01-test")
        assert "Line one." in result
        assert "Line two." in result

    def test_extract_tldr_returns_none_when_missing(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        self._write_article(tmp_path, "2026-04-01-test",
            "---\ntitle: Test\n---\n# Title\n\nBody here.\n")
        assert m._extract_tldr("2026-04-01-test") is None

    def test_extract_tldr_returns_none_when_file_missing(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        assert m._extract_tldr("2026-04-01-test") is None

    def test_extract_tldr_strips_markdown_links(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        self._write_article(tmp_path, "2026-04-01-test",
            "---\ntitle: Test\n---\n# Title\n\n> **TL;DR:** See [the guide](https://example.com) for details.\n\nBody.")
        result = m._extract_tldr("2026-04-01-test")
        assert "[the guide]" not in result
        assert "https://example.com" not in result
        assert "See the guide for details." in result

    def test_extract_tldr_no_fallback_generation(self, monkeypatch, tmp_path):
        """The extractor must never invent a TL;DR from article body text."""
        m = self._mod()
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        self._write_article(tmp_path, "2026-04-01-test",
            "---\ntitle: Test\n---\n# Title\n\nFirst paragraph of the article body.\n\nSecond paragraph.")
        result = m._extract_tldr("2026-04-01-test")
        assert result is None
        assert "First paragraph" not in (result or "")



class TestQuickReads:
    """Topic-page Quick reads section — E4 rendering contract."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def _synthetic_index(self, topic_counts):
        articles = []
        day = 1
        for topic, count in topic_counts.items():
            for _ in range(count):
                articles.append({
                    "folder": f"2026-04-{day:02d}-article-{day}",
                    "slug": f"article-{day}",
                    "title": f"Article {day}",
                    "published_date": f"2026-04-{day:02d}",
                    "tags": [],
                    "topics": [topic],
                    "funnel_stage": "middle",
                    "canonical_url": f"https://radar.firstaimovers.com/slug{day}",
                })
                day += 1
        articles.sort(key=lambda a: a["published_date"], reverse=True)
        return {"articles": articles}

    def _run(self, monkeypatch, tmp_path, index, tldr_map=None):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        from pathlib import Path as P
        real_root = P(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")

        for a in index["articles"]:
            folder = a["folder"]
            (tmp_path / "articles" / folder).mkdir(exist_ok=True)
            body = f"---\ntitle: {a['title']}\n---\n# {a['title']}\n\n"
            if tldr_map and folder in tldr_map:
                body += f"> **TL;DR:** {tldr_map[folder]}\n\n"
            body += "Body paragraph with enough text to serve as a summary for this test article.\n"
            (tmp_path / "articles" / folder / "article.md").write_text(body)

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return tmp_path / "site"

    def test_quick_reads_shown_when_tldrs_exist(self, monkeypatch, tmp_path):
        index = self._synthetic_index({"AI Strategy": 6})
        tldr_map = {
            "2026-04-06-article-6": "Summary for article six.",
            "2026-04-05-article-5": "Summary for article five.",
        }
        site = self._run(monkeypatch, tmp_path, index, tldr_map)
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert 'class="quick-reads"' in page
        assert "Summary for article six." in page
        assert "Summary for article five." in page
        assert "Article 6" in page
        assert "Article 5" in page

    def test_quick_reads_hidden_when_no_tldrs(self, monkeypatch, tmp_path):
        index = self._synthetic_index({"AI Strategy": 6})
        site = self._run(monkeypatch, tmp_path, index, {})
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert 'class="quick-reads"' not in page
        assert "Quick reads" not in page

    def test_quick_reads_links_use_canonical_url(self, monkeypatch, tmp_path):
        index = self._synthetic_index({"AI Strategy": 6})
        tldr_map = {
            "2026-04-06-article-6": "Summary for article six.",
        }
        site = self._run(monkeypatch, tmp_path, index, tldr_map)
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert "https://radar.firstaimovers.com/slug6" in page
        assert 'href="/articles/' not in page

    def test_quick_reads_respects_limit(self, monkeypatch, tmp_path):
        index = self._synthetic_index({"AI Strategy": 10})
        tldr_map = {f"2026-04-{d:02d}-article-{d}": f"Summary {d}." for d in range(1, 11)}
        site = self._run(monkeypatch, tmp_path, index, tldr_map)
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        # Should show at most QUICK_READS_MAX (5) items
        count = page.count('class="quick-read"')
        assert count <= 5
        # Newest articles should appear first
        assert page.index("Summary 10.") < page.index("Summary 6.")

    def test_quick_reads_no_fallback_summary(self, monkeypatch, tmp_path):
        """Articles without TL;DR must not appear in Quick reads via fabricated summaries."""
        index = self._synthetic_index({"AI Strategy": 6})
        tldr_map = {
            "2026-04-06-article-6": "Only this one has a TL;DR.",
        }
        site = self._run(monkeypatch, tmp_path, index, tldr_map)
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert "Only this one has a TL;DR." in page
        # Articles 1-5 have no TL;DR and must not appear in quick-reads
        qr_section = page.split('class="quick-reads"')[1].split('class="articles-heading"')[0] if 'class="quick-reads"' in page else ""
        assert "Article 1" not in qr_section
        assert "Article 2" not in qr_section
        assert "Article 3" not in qr_section


# =========================================================================
# Tests: rebuild_local.py JSON Feed (E5)
# =========================================================================


