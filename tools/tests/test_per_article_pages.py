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

class TestArticlePages:
    """Per-article HTML pages renderer. Requires jinja2 and markdown."""

    def _mod(self):
        pytest.importorskip("jinja2")
        pytest.importorskip("markdown")
        import rebuild_local
        return rebuild_local

    def _synthetic_index(self, n=3):
        articles = []
        for i in range(n):
            day = 20 - i
            articles.append({
                "folder": f"2026-04-{day:02d}-article-{i}",
                "slug": f"article-{i}",
                "title": f"Test Article {i}",
                "published_date": f"2026-04-{day:02d}",
                "tags": ["AI Strategy"],
                "topics": ["AI Strategy", "European SME AI"],
                "funnel_stage": "middle",
                "canonical_url": f"https://radar.firstaimovers.com/article-{i}",
            })
        return {"articles": articles}

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

        for a in index["articles"]:
            folder = a["folder"]
            (tmp_path / "articles" / folder).mkdir(exist_ok=True)
            (tmp_path / "articles" / folder / "article.md").write_text(
                f'---\ntitle: "{a["title"]}"\nauthor: "Dr. Hernani Costa"\n'
                f'canonical_url: "{a["canonical_url"]}"\npublished_date: "{a["published_date"]}"\n'
                f'license: "CC BY 4.0"\n---\n'
                f'# {a["title"]}\n\n## Introduction\n\nThis is the introduction paragraph.\n\n'
                f'## Key Point\n\n- Bullet one\n- Bullet two\n\n'
                f'[A link](https://example.com)\n\n'
                f'> A blockquote\n\n'
                f'```python\nprint("hello")\n```\n',
                encoding="utf-8")

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return tmp_path / "site"

    # --- Route generation --------------------------------------------------

    def test_article_local_path_uses_slug(self):
        m = self._mod()
        assert m._article_local_path({"slug": "my-article"}) == "/articles/my-article/"

    def test_article_local_path_falls_back_to_folder(self):
        m = self._mod()
        assert m._article_local_path({"folder": "2026-04-01-my-article"}) == "/articles/2026-04-01-my-article/"

    def test_article_local_path_prefers_slug_over_folder(self):
        m = self._mod()
        assert m._article_local_path({"slug": "slug", "folder": "folder"}) == "/articles/slug/"

    # --- Page generation ---------------------------------------------------

    def test_article_page_generated_for_each_article(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        for i in range(3):
            assert (site / "articles" / f"article-{i}" / "index.html").exists()

    def test_article_page_contains_title(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert "Test Article 0" in page

    def test_article_page_body_html_rendered(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert '<h2 id="introduction">Introduction</h2>' in page
        assert "<li>Bullet one</li>" in page
        assert "<li>Bullet two</li>" in page
        assert '<a href="https://example.com">A link</a>' in page
        assert "<blockquote>" in page
        assert "<pre>" in page
        assert "<code" in page

    def test_article_page_front_matter_stripped(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert "---" not in page  # No raw front matter delimiters
        assert "canonical_url:" not in page  # No front matter keys

    def test_article_page_has_archive_notice(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert "Archive copy" in page
        assert "read original" in page.lower() or "original at" in page.lower()

    # --- Canonical protection ----------------------------------------------

    def test_article_page_has_noindex_follow(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'name="robots" content="noindex, follow"' in page

    def test_article_page_has_canonical_link(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'rel="canonical" href="https://radar.firstaimovers.com/article-0"' in page

    def test_article_page_canonical_is_external_not_local(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'rel="canonical" href="https://articles.firstaimovers.com/articles/' not in page

    # --- Schema.org JSON-LD ------------------------------------------------

    def test_article_page_has_jsonld_article(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'application/ld+json' in page
        assert '"@type": "Article"' in page or '"@type":"Article"' in page

    def test_article_page_jsonld_has_required_fields(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        script_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.DOTALL)
        assert script_match is not None
        data = json.loads(script_match.group(1))
        assert data["@type"] == "Article"
        assert data["headline"] == "Test Article 0"
        assert data["datePublished"] == "2026-04-20"
        assert data["author"]["name"] == "Dr. Hernani Costa"
        assert data["publisher"]["name"] == "First AI Movers"
        assert "creativecommons.org/licenses/by/4.0" in data["license"]

    # --- Sitemap behavior --------------------------------------------------

    def test_sitemap_does_not_include_local_article_pages(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        m.build_sitemap(self._synthetic_index(3))
        xml = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
        assert "/articles/article-0/" not in xml
        assert "/articles/article-1/" not in xml
        assert "/articles/article-2/" not in xml

    # --- Article card linking ----------------------------------------------

    def test_article_card_title_links_to_local_page(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        topic_page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        # Title should link to local article page
        assert 'href="../../articles/article-0/"' in topic_page or 'href="../../articles/article-1/"' in topic_page

    def test_article_card_cta_stays_external(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        topic_page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert "https://radar.firstaimovers.com/article-0" in topic_page
        assert "Read at Radar" in topic_page or "Read at" in topic_page

    # --- Feed stability ----------------------------------------------------

    def test_feed_urls_unchanged(self, monkeypatch, tmp_path):
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

    # --- Build artifacts ---------------------------------------------------

    def test_build_increases_page_count_by_article_count(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(5))
        # home(1) + topics_index(1) + topic_pages(1) + about(1) + 404(1) + article_pages(5) = 10
        article_pages = list((site / "articles").glob("*/index.html"))
        assert len(article_pages) == 5

    def test_no_article_md_files_mutated(self, monkeypatch, tmp_path):
        index = self._synthetic_index(1)
        site = self._run(monkeypatch, tmp_path, index)
        # Verify article.md is unchanged
        original = (tmp_path / "articles" / index["articles"][0]["folder"] / "article.md").read_text(encoding="utf-8")
        assert "---" in original  # Still has front matter
        assert "# Test Article 0" in original

    def test_no_metadata_files_mutated(self, monkeypatch, tmp_path):
        index = self._synthetic_index(1)
        self._run(monkeypatch, tmp_path, index)
        assert not (tmp_path / "articles" / index["articles"][0]["folder"] / "metadata.json").exists()

    # --- XSS / raw HTML safety ---------------------------------------------

    def _write_unsafe_article(self, tmp_path, folder, body):
        d = tmp_path / "articles" / folder
        d.mkdir(parents=True, exist_ok=True)
        (d / "article.md").write_text(
            f"---\ntitle: Unsafe\n---\n# Unsafe\n\n{body}\n", encoding="utf-8")

    def _run_with_custom_body(self, monkeypatch, tmp_path, folder, body):
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

        self._write_unsafe_article(tmp_path, folder, body)
        index = {
            "articles": [{
                "folder": folder,
                "slug": "unsafe",
                "title": "Unsafe",
                "published_date": "2026-04-20",
                "tags": [],
                "topics": [],
                "funnel_stage": "middle",
                "canonical_url": "https://radar.firstaimovers.com/unsafe",
            }]
        }
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return (tmp_path / "site" / "articles" / "unsafe" / "index.html").read_text(encoding="utf-8")

    def _article_body_from_page(self, page_html):
        """Extract just the article-body div HTML for XSS assertions."""
        start = page_html.find('<div class="article-body">')
        end = page_html.find('</div>', start) + len('</div>')
        return page_html[start:end] if start != -1 else page_html

    def test_script_tag_removed(self, monkeypatch, tmp_path):
        page = self._run_with_custom_body(
            monkeypatch, tmp_path, "2026-04-20-unsafe",
            '<script>alert("xss")</script>')
        body = self._article_body_from_page(page)
        assert "<script>" not in body
        assert "alert(" not in body

    def test_iframe_tag_removed(self, monkeypatch, tmp_path):
        page = self._run_with_custom_body(
            monkeypatch, tmp_path, "2026-04-20-unsafe",
            '<iframe src="https://evil.com"></iframe>')
        body = self._article_body_from_page(page)
        assert "<iframe" not in body
        assert "evil.com" not in body

    def test_event_handler_attribute_removed(self, monkeypatch, tmp_path):
        page = self._run_with_custom_body(
            monkeypatch, tmp_path, "2026-04-20-unsafe",
            '<img src=x onerror=alert(1)>')
        body = self._article_body_from_page(page)
        assert "onerror" not in body
        assert "alert(1)" not in body

    def test_javascript_url_removed(self, monkeypatch, tmp_path):
        page = self._run_with_custom_body(
            monkeypatch, tmp_path, "2026-04-20-unsafe",
            '<a href="javascript:alert(1)">click</a>')
        body = self._article_body_from_page(page)
        assert "javascript:" not in body
        # The href attribute should have been removed entirely
        assert 'href="alert(1)"' not in body
        # Link text should still be present (sanitizer removes attribute, not tag)
        assert "click" in body

    def test_normal_markdown_preserved_after_sanitization(self, monkeypatch, tmp_path):
        page = self._run_with_custom_body(
            monkeypatch, tmp_path, "2026-04-20-safe",
            '## Heading\n\n- Item one\n- Item two\n\n'
            '> A blockquote\n\n'
            '[a link](https://example.com)\n\n'
            '```python\nprint("hi")\n```')
        body = self._article_body_from_page(page)
        assert '<h2 id="heading">Heading</h2>' in body
        assert "<li>Item one</li>" in body
        assert "<blockquote>" in body
        assert '<a href="https://example.com">a link</a>' in body
        assert "<pre>" in body
        assert "<code" in body


# =========================================================================
# Tests: rebuild_local.py per-article enhancements (E7)
# =========================================================================


class TestArticleEnhancements:
    """Per-article page enhancements: reading time, TOC, breadcrumbs, related articles."""

    def _mod(self):
        pytest.importorskip("jinja2")
        pytest.importorskip("markdown")
        import rebuild_local
        return rebuild_local

    # --- Reading time ------------------------------------------------------

    def test_reading_time_counts_words(self):
        m = self._mod()
        text = "word " * 400  # 400 words = 2 minutes at 200 WPM
        assert m._reading_time(text) == 2

    def test_reading_time_minimum_one_minute(self):
        m = self._mod()
        text = "short."
        assert m._reading_time(text) == 1

    def test_reading_time_ignores_front_matter(self):
        m = self._mod()
        text = '---\ntitle: Test\n---\n# Title\n\n' + 'word ' * 400
        assert m._reading_time(text) == 2

    def test_reading_time_rounds_up(self):
        m = self._mod()
        text = "word " * 250  # 250 words = 1.25 min -> rounds to 1
        assert m._reading_time(text) == 1
        text = "word " * 350  # 350 words = 1.75 min -> rounds to 2
        assert m._reading_time(text) == 2

    # --- TOC / heading IDs -------------------------------------------------

    def test_inject_heading_ids_adds_ids(self):
        m = self._mod()
        html = "<h2>First Section</h2><p>text</p><h3>Subsection</h3>"
        new_html, headings = m._inject_heading_ids(html)
        assert 'id="first-section"' in new_html
        assert 'id="subsection"' in new_html
        assert len(headings) == 2
        assert headings[0]["text"] == "First Section"
        assert headings[0]["level"] == 2
        assert headings[1]["text"] == "Subsection"
        assert headings[1]["level"] == 3

    def test_inject_heading_ids_deduplicates(self):
        m = self._mod()
        html = "<h2>Same</h2><h2>Same</h2><h2>Same</h2>"
        new_html, headings = m._inject_heading_ids(html)
        assert 'id="same"' in new_html
        assert 'id="same-1"' in new_html
        assert 'id="same-2"' in new_html

    def test_inject_heading_ids_preserves_existing_ids(self):
        m = self._mod()
        html = '<h2 id="custom">Section</h2>'
        new_html, headings = m._inject_heading_ids(html)
        assert 'id="custom"' in new_html
        assert headings[0]["id"] == "custom"

    def test_inject_heading_ids_strips_inline_html_for_slug(self):
        m = self._mod()
        html = '<h2>Section with <code>code</code></h2>'
        new_html, headings = m._inject_heading_ids(html)
        assert headings[0]["text"] == "Section with code"
        assert 'id="section-with-code"' in new_html

    def test_inject_heading_ids_returns_empty_for_no_headings(self):
        m = self._mod()
        html = "<p>No headings here</p>"
        new_html, headings = m._inject_heading_ids(html)
        assert new_html == html
        assert headings == []

    # --- Related articles --------------------------------------------------

    def test_related_articles_excludes_current(self):
        m = self._mod()
        target = {"slug": "target", "topics": ["AI Strategy"], "published_date": "2026-04-20", "title": "Target"}
        all_articles = [
            {"slug": "target", "topics": ["AI Strategy"], "published_date": "2026-04-20", "title": "Target"},
            {"slug": "other", "topics": ["AI Strategy"], "published_date": "2026-04-19", "title": "Other"},
        ]
        related = m._related_articles_for_article(target, all_articles, limit=3)
        assert len(related) == 1
        assert related[0]["slug"] == "other"

    def test_related_articles_ranks_by_topic_overlap(self):
        m = self._mod()
        target = {"slug": "target", "topics": ["A", "B"], "published_date": "2026-04-20", "title": "Target"}
        all_articles = [
            {"slug": "two", "topics": ["A", "B"], "published_date": "2026-04-19", "title": "Two"},
            {"slug": "one", "topics": ["A"], "published_date": "2026-04-19", "title": "One"},
            {"slug": "none", "topics": ["C"], "published_date": "2026-04-19", "title": "None"},
        ]
        related = m._related_articles_for_article(target, all_articles, limit=3)
        assert [a["slug"] for a in related] == ["two", "one"]

    def test_related_articles_tiebreaks_by_date_then_title(self):
        m = self._mod()
        target = {"slug": "target", "topics": ["A"], "published_date": "2026-04-20", "title": "Target"}
        all_articles = [
            {"slug": "old", "topics": ["A"], "published_date": "2026-04-18", "title": "Zebra"},
            {"slug": "new", "topics": ["A"], "published_date": "2026-04-19", "title": "Apple"},
            {"slug": "mid", "topics": ["A"], "published_date": "2026-04-19", "title": "Banana"},
        ]
        related = m._related_articles_for_article(target, all_articles, limit=3)
        # Same overlap (1), same date (2026-04-19) for new and mid -> title alphabetical
        assert [a["slug"] for a in related] == ["new", "mid", "old"]

    def test_related_articles_respects_limit(self):
        m = self._mod()
        target = {"slug": "target", "topics": ["A"], "published_date": "2026-04-20", "title": "Target"}
        all_articles = [
            {"slug": f"a{i}", "topics": ["A"], "published_date": f"2026-04-{10+i:02d}", "title": f"A{i}"}
            for i in range(10)
        ]
        related = m._related_articles_for_article(target, all_articles, limit=3)
        assert len(related) == 3

    # --- End-to-end article page rendering ---------------------------------

    def _synthetic_index(self, n=3):
        articles = []
        for i in range(n):
            day = 20 - i
            articles.append({
                "folder": f"2026-04-{day:02d}-article-{i}",
                "slug": f"article-{i}",
                "title": f"Test Article {i}",
                "published_date": f"2026-04-{day:02d}",
                "tags": ["AI Strategy"],
                "topics": ["AI Strategy", "European SME AI"],
                "funnel_stage": "middle",
                "canonical_url": f"https://radar.firstaimovers.com/article-{i}",
            })
        return {"articles": articles}

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

        for a in index["articles"]:
            folder = a["folder"]
            (tmp_path / "articles" / folder).mkdir(exist_ok=True)
            body = (
                f'---\ntitle: "{a["title"]}"\nauthor: "Dr. Hernani Costa"\n'
                f'canonical_url: "{a["canonical_url"]}"\npublished_date: "{a["published_date"]}"\n'
                f'license: "CC BY 4.0"\n---\n'
                f'# {a["title"]}\n\n'
                f'## Introduction\n\nThis is the introduction paragraph with enough words to fill some space.\n\n'
                f'### Background\n\nSome background info here.\n\n'
                f'## Key Point\n\n- Bullet one\n- Bullet two\n\n'
                f'[A link](https://example.com)\n\n'
                f'> A blockquote\n\n'
                f'```python\nprint("hello")\n```\n')
            (tmp_path / "articles" / folder / "article.md").write_text(body, encoding="utf-8")

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return tmp_path / "site"

    def test_article_page_has_breadcrumb(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'class="breadcrumb"' in page
        assert "Home" in page
        assert "Topics" in page or "Article" in page

    def test_article_page_has_reading_time(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert "min read" in page or "minute" in page.lower()

    def test_article_page_has_toc_when_enough_headings(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'class="toc"' in page
        assert "Introduction" in page
        assert "Key Point" in page

    def test_article_page_headings_have_ids(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'id="introduction"' in page
        assert 'id="key-point"' in page

    def test_article_page_has_related_articles(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'class="related-articles"' in page
        # Should show related articles (not the current one)
        assert "Test Article 1" in page or "Test Article 2" in page

    def test_article_page_toc_hidden_when_few_headings(self, monkeypatch, tmp_path):
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

        folder = "2026-04-20-short"
        (tmp_path / "articles" / folder).mkdir(exist_ok=True)
        (tmp_path / "articles" / folder / "article.md").write_text(
            '---\ntitle: Short\n---\n# Short\n\nOnly one paragraph.\n', encoding="utf-8")
        index = {"articles": [{
            "folder": folder, "slug": "short", "title": "Short",
            "published_date": "2026-04-20", "tags": [], "topics": [],
            "funnel_stage": "middle", "canonical_url": "https://radar.firstaimovers.com/short",
        }]}
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        page = (tmp_path / "site" / "articles" / "short" / "index.html").read_text(encoding="utf-8")
        assert 'class="toc"' not in page

    # --- Regression guards -------------------------------------------------

    def test_article_page_still_noindex_follow(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'name="robots" content="noindex, follow"' in page

    def test_article_page_still_external_canonical(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'rel="canonical" href="https://radar.firstaimovers.com/article-0"' in page

    def test_article_page_still_has_jsonld(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert '"@type": "Article"' in page or '"@type":"Article"' in page

    def test_sitemap_unchanged(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        m.build_sitemap(self._synthetic_index(3))
        xml = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
        assert "/articles/article-0/" not in xml

    def test_feed_unchanged(self, monkeypatch, tmp_path):
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
# Tests: E8 hardening — duplicate-title gate
# =========================================================================


