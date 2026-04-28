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

class TestClientSearch:
    """Client-side search over index.json on home and topics index pages."""

    def _mod(self):
        pytest.importorskip("jinja2")
        pytest.importorskip("markdown")
        import rebuild_local
        return rebuild_local

    def _run(self, monkeypatch, tmp_path, index):
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

        for a in index.get("articles", []):
            folder = a.get("folder", "")
            if folder:
                (tmp_path / "articles" / folder).mkdir(exist_ok=True)
                (tmp_path / "articles" / folder / "article.md").write_text(
                    f"---\ntitle: {a.get('title', 'T')}\n---\n# {a.get('title', 'T')}\n\nBody.\n")

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return tmp_path / "site"

    def _synthetic_index(self, n=3):
        articles = []
        for i in range(n):
            day = 20 - i
            articles.append({
                "folder": f"2026-04-{day:02d}-article-{i}",
                "slug": f"article-{i}",
                "title": f"Test Article {i}",
                "published_date": f"2026-04-{day:02d}",
                "tags": ["AI Strategy", "SME"],
                "topics": ["AI Strategy", "European SME AI"],
                "funnel_stage": "middle",
                "canonical_url": f"https://radar.firstaimovers.com/article-{i}",
            })
        return {"articles": articles}

    def test_home_page_has_search_input(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        home = (site / "index.html").read_text(encoding="utf-8")
        assert '<input' in home
        assert 'type="search"' in home or 'id="archive-search"' in home

    def test_home_page_has_search_results_region(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        home = (site / "index.html").read_text(encoding="utf-8")
        assert 'id="search-results"' in home

    def test_topics_index_has_search_input(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        page = (site / "topics" / "index.html").read_text(encoding="utf-8")
        assert '<input' in page
        assert 'type="search"' in page or 'id="archive-search"' in page

    def test_topics_index_has_search_results_region(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        page = (site / "topics" / "index.html").read_text(encoding="utf-8")
        assert 'id="search-results"' in page

    def test_search_js_included_on_home(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        home = (site / "index.html").read_text(encoding="utf-8")
        assert "search.js" in home

    def test_search_js_included_on_topics_index(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        page = (site / "topics" / "index.html").read_text(encoding="utf-8")
        assert "search.js" in page

    def test_search_js_file_exists(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        assert (site / "search.js").exists()

    def test_search_input_has_accessible_label(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        home = (site / "index.html").read_text(encoding="utf-8")
        assert 'aria-label="Search articles"' in home or '<label' in home

    def test_search_results_has_aria_live(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        home = (site / "index.html").read_text(encoding="utf-8")
        assert 'aria-live="polite"' in home

    def test_article_page_does_not_have_search(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert "archive-search" not in page

    def test_about_page_does_not_have_search(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        page = (site / "about" / "index.html").read_text(encoding="utf-8")
        assert "archive-search" not in page

    def test_search_js_fetches_index_json(self):
        from pathlib import Path as P
        js = (P(__file__).resolve().parents[2] / "static" / "search.js").read_text(encoding="utf-8")
        assert "index.json" in js

    def test_search_js_links_to_local_article_pages(self):
        from pathlib import Path as P
        js = (P(__file__).resolve().parents[2] / "static" / "search.js").read_text(encoding="utf-8")
        assert "articles/" in js

    def test_search_js_caps_results(self):
        from pathlib import Path as P
        js = (P(__file__).resolve().parents[2] / "static" / "search.js").read_text(encoding="utf-8")
        assert "25" in js or "20" in js or "30" in js or "limit" in js.lower() or "max" in js.lower() or "cap" in js.lower() or "slice" in js.lower()

    def test_sitemap_still_excludes_local_article_pages(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        m.build_sitemap(self._synthetic_index(3))
        xml = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
        assert "/articles/article-0/" not in xml

    def test_feed_urls_still_canonical(self, monkeypatch, tmp_path):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        for a in self._synthetic_index(3)["articles"]:
            d = tmp_path / "articles" / a["folder"]
            d.mkdir(exist_ok=True)
            (d / "article.md").write_text(f"---\ntitle: {a['title']}\n---\n# {a['title']}\n\nBody.\n")
        m.build_feed(self._synthetic_index(3))
        xml = (tmp_path / "feed.xml").read_text(encoding="utf-8")
        assert "https://radar.firstaimovers.com/article-0" in xml
        assert "/articles/article-0/" not in xml


# =========================================================================
# Tests: PR B — IndexNow integration
# =========================================================================


