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

class TestXssResistance:
    """Strengthened XSS coverage for article body, title, summary, topic intro, JSON-LD."""

    def _mod(self):
        pytest.importorskip("jinja2")
        pytest.importorskip("markdown")
        import rebuild_local
        return rebuild_local

    def _run_with_custom_article(self, monkeypatch, tmp_path, folder, title, body_md, topics=None):
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

        d = tmp_path / "articles" / folder
        d.mkdir(parents=True, exist_ok=True)
        (d / "article.md").write_text(
            f'---\ntitle: "{title}"\nauthor: "Dr. Hernani Costa"\n'
            f'canonical_url: "https://radar.firstaimovers.com/{folder}"\n'
            f'published_date: "2026-04-20"\nlicense: "CC BY 4.0"\n---\n'
            f'# {title}\n\n{body_md}\n', encoding="utf-8")

        index = {"articles": [{
            "folder": folder, "slug": "unsafe", "title": title,
            "published_date": "2026-04-20", "tags": [],
            "topics": topics or ["AI Strategy"],
            "funnel_stage": "middle",
            "canonical_url": f"https://radar.firstaimovers.com/{folder}",
        }]}
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return (tmp_path / "site" / "articles" / "unsafe" / "index.html").read_text(encoding="utf-8")

    def _article_body_from_page(self, page_html):
        start = page_html.find('<div class="article-body">')
        end = page_html.find('</div>', start) + len('</div>')
        return page_html[start:end] if start != -1 else page_html

    def test_malicious_title_escaped_in_page(self, monkeypatch, tmp_path):
        title = '<script>alert("xss")</script>'
        page = self._run_with_custom_article(
            monkeypatch, tmp_path, "2026-04-20-t", title, "Body.")
        # h1 should contain escaped title (jinja2 escapes quotes as &#34;)
        assert '<h1>&lt;script&gt;alert(&#34;xss&#34;)&lt;/script&gt;</h1>' in page
        # meta description should be escaped
        assert '&lt;script&gt;alert(&#34;xss&#34;)&lt;/script&gt;' in page

    def test_malicious_summary_escaped_in_meta(self, monkeypatch, tmp_path):
        """Summary is used in <meta name=description>; must be escaped."""
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

        folder = "2026-04-20-s"
        d = tmp_path / "articles" / folder
        d.mkdir(parents=True, exist_ok=True)
        (d / "article.md").write_text(
            '---\ntitle: "Test"\n---\n# Test\n\n> **TL;DR:** <script>bad()</script>\n\nBody.\n',
            encoding="utf-8")

        index = {"articles": [{
            "folder": folder, "slug": "s", "title": "Test",
            "published_date": "2026-04-20", "tags": [], "topics": ["AI Strategy"],
            "funnel_stage": "middle", "canonical_url": "https://radar.firstaimovers.com/s",
        }]}
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        page = (tmp_path / "site" / "articles" / "s" / "index.html").read_text(encoding="utf-8")
        # meta description should contain escaped script tag
        assert '&lt;script&gt;bad()&lt;/script&gt;' in page

    def test_malicious_topic_intro_escaped_on_topic_page(self, monkeypatch, tmp_path):
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

        # Need >= MIN_ARTICLES_FOR_TOPIC_PAGE articles for topic page to exist
        articles = []
        for i in range(6):
            folder = f"2026-04-{20-i:02d}-t{i}"
            d = tmp_path / "articles" / folder
            d.mkdir(parents=True, exist_ok=True)
            (d / "article.md").write_text(f'---\ntitle: T{i}\n---\n# T{i}\n\nBody.\n', encoding="utf-8")
            articles.append({
                "folder": folder, "slug": f"t{i}", "title": f"T{i}",
                "published_date": f"2026-04-{20-i:02d}", "tags": [], "topics": ["AI Strategy"],
                "funnel_stage": "middle", "canonical_url": f"https://radar.firstaimovers.com/t{i}",
            })

        index = {"articles": articles}
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        monkeypatch.setattr(m, "_load_topic_intros", lambda: {
            "AI Strategy": {
                "lede": '<script>alert(1)</script>Lede here',
                "key_themes": ['<img src=x onerror=alert(1)>Theme'],
                "why_it_matters": '<iframe src="evil.com"></iframe>Why',
            },
        })
        m.build_site(index)
        page = (tmp_path / "site" / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        # meta description and JSON-LD should contain escaped tags
        assert "&lt;script&gt;alert(1)&lt;/script&gt;Lede here" in page
        # Raw malicious markup must not appear in content areas
        assert '<p class="lede">&lt;script&gt;alert(1)&lt;/script&gt;Lede here</p>' in page
        assert '<li>&lt;img src=x onerror=alert(1)&gt;Theme</li>' in page
        assert '<p>&lt;iframe src=&#34;evil.com&#34;&gt;&lt;/iframe&gt;Why</p>' in page

    def test_json_ld_remains_parseable_with_malicious_title(self, monkeypatch, tmp_path):
        title = 'Test "with quotes" and \\ backslash'
        page = self._run_with_custom_article(
            monkeypatch, tmp_path, "2026-04-20-j", title, "Body.")
        match = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.DOTALL)
        assert match is not None
        data = json.loads(match.group(1))
        assert data["@type"] == "Article"
        assert data["headline"] == title

    def test_article_body_script_tag_removed(self, monkeypatch, tmp_path):
        page = self._run_with_custom_article(
            monkeypatch, tmp_path, "2026-04-20-x",
            "Title", '<script>alert("xss")</script>')
        body = self._article_body_from_page(page)
        assert "<script>" not in body

    def test_article_body_javascript_url_removed(self, monkeypatch, tmp_path):
        page = self._run_with_custom_article(
            monkeypatch, tmp_path, "2026-04-20-x",
            "Title", '<a href="javascript:alert(1)">click</a>')
        body = self._article_body_from_page(page)
        assert "javascript:" not in body
        assert "click" in body


# =========================================================================
# Tests: E8 hardening — atomic writes
# =========================================================================


