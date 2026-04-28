"""Tests for E24 GoatCounter analytics integration."""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestBaseTemplate:
    def test_base_template_has_goatcounter_endpoint(self):
        base = REPO_ROOT / "templates" / "base.html.j2"
        text = base.read_text(encoding="utf-8")
        assert "firstaimovers.goatcounter.com/count" in text

    def test_base_template_uses_sri_versioned_count_script(self):
        base = REPO_ROOT / "templates" / "base.html.j2"
        text = base.read_text(encoding="utf-8")
        assert "gc.zgo.at/count.v5.js" in text
        assert "sha384-" in text
        assert "crossorigin=\"anonymous\"" in text

    def test_base_template_has_path_override_before_script(self):
        base = REPO_ROOT / "templates" / "base.html.j2"
        text = base.read_text(encoding="utf-8")
        # Path override must appear before the external script tag
        path_override_pos = text.find("window.goatcounter.path")
        script_tag_pos = text.find("gc.zgo.at/count.v5.js")
        assert path_override_pos != -1
        assert script_tag_pos != -1
        assert path_override_pos < script_tag_pos

    def test_path_override_uses_location_pathname_not_canonical(self):
        base = REPO_ROOT / "templates" / "base.html.j2"
        text = base.read_text(encoding="utf-8")
        # Extract the path override function body
        start = text.find("window.goatcounter.path = function () {")
        assert start != -1
        end = text.find("};", start)
        block = text[start:end]
        assert "location.pathname" in block
        # It must NOT use canonical URL or document.canonical
        assert "canonical" not in block.lower()

    def test_no_google_analytics_or_other_trackers(self):
        base = REPO_ROOT / "templates" / "base.html.j2"
        text = base.read_text(encoding="utf-8")
        forbidden = [
            "google-analytics",
            "googletagmanager",
            "gtag",
            "plausible",
            "fathom",
            "segment",
            "mixpanel",
            "amplitude",
        ]
        lower = text.lower()
        for term in forbidden:
            assert term not in lower, f"Unexpected tracker '{term}' in base template"


class TestNoDuplicateScripts:
    def test_no_duplicate_goatcounter_scripts(self):
        base = REPO_ROOT / "templates" / "base.html.j2"
        text = base.read_text(encoding="utf-8")
        assert text.count("firstaimovers.goatcounter.com/count") == 1

    def test_child_templates_do_not_add_second_script(self):
        article = REPO_ROOT / "templates" / "article.html.j2"
        text = article.read_text(encoding="utf-8")
        assert "goatcounter" not in text.lower()


class TestRenderedPages:
    def test_home_page_has_analytics_after_build(self, monkeypatch, tmp_path):
        import sys
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        import rebuild_local as m

        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        shutil.copytree(REPO_ROOT / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(REPO_ROOT / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(REPO_ROOT / "hernanicosta.json", tmp_path / "hernanicosta.json")

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")

        index = {"articles": [], "topics": {}, "topics_with_page": []}
        m.build_site(index)

        home = (tmp_path / "site" / "index.html").read_text(encoding="utf-8")
        assert "firstaimovers.goatcounter.com/count" in home
        assert "window.goatcounter.path" in home

    def test_article_page_keeps_noindex_and_has_analytics_after_build(self, monkeypatch, tmp_path):
        import sys
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        import rebuild_local as m

        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        shutil.copytree(REPO_ROOT / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(REPO_ROOT / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(REPO_ROOT / "hernanicosta.json", tmp_path / "hernanicosta.json")

        article_dir = tmp_path / "articles" / "2026-01-01-test"
        article_dir.mkdir(parents=True)
        article_dir.joinpath("article.md").write_text("---\ntitle: Test\n---\n# Test\n\nBody.\n", encoding="utf-8")
        article_dir.joinpath("metadata.json").write_text(
            json.dumps({"title": "Test", "published_date": "2026-01-01", "canonical_url": "https://example.com", "slug": "test"}),
            encoding="utf-8",
        )

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")

        index = {
            "articles": [{"folder": "2026-01-01-test", "title": "Test", "published_date": "2026-01-01", "canonical_url": "https://example.com", "slug": "test", "topics": []}],
            "topics": {},
            "topics_with_page": [],
        }
        m.build_site(index)

        article_html = (tmp_path / "site" / "articles" / "test" / "index.html").read_text(encoding="utf-8")
        assert "firstaimovers.goatcounter.com/count" in article_html
        assert "noindex" in article_html  # article pages remain noindex
        assert "https://example.com" in article_html  # external canonical preserved

    def test_topic_page_has_analytics_after_build(self, monkeypatch, tmp_path):
        import sys
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        import rebuild_local as m

        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        shutil.copytree(REPO_ROOT / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(REPO_ROOT / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(REPO_ROOT / "hernanicosta.json", tmp_path / "hernanicosta.json")

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "MIN_ARTICLES_FOR_TOPIC_PAGE", 1)

        article_dir = tmp_path / "articles" / "2026-01-01-test"
        article_dir.mkdir(parents=True)
        article_dir.joinpath("article.md").write_text("---\ntitle: Test\n---\n# Test\n\nBody.\n", encoding="utf-8")
        article_dir.joinpath("metadata.json").write_text(
            json.dumps({"title": "Test", "published_date": "2026-01-01", "canonical_url": "https://example.com", "slug": "test"}),
            encoding="utf-8",
        )

        index = {
            "articles": [{"folder": "2026-01-01-test", "title": "Test", "published_date": "2026-01-01", "canonical_url": "https://example.com", "slug": "test", "topics": ["AI Strategy"]}],
            "topics": {"AI Strategy": ["test"]},
            "topics_with_page": ["AI Strategy"],
        }
        m.build_site(index)

        topic_html = (tmp_path / "site" / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert "firstaimovers.goatcounter.com/count" in topic_html
        assert "robots\" content=\"index, follow\"" in topic_html  # topic pages remain indexable


class TestDocs:
    def test_analytics_doc_exists(self):
        doc = REPO_ROOT / "docs" / "ANALYTICS.md"
        assert doc.exists()
        text = doc.read_text(encoding="utf-8")
        assert "GoatCounter" in text
        assert "firstaimovers.goatcounter.com/count" in text

    def test_analytics_doc_mentions_privacy_and_rollback(self):
        doc = REPO_ROOT / "docs" / "ANALYTICS.md"
        text = doc.read_text(encoding="utf-8")
        assert "privacy" in text.lower()
        assert "rollback" in text.lower()
        assert "cookie" in text.lower()
        assert "GDPR" in text
