"""Tests for E26 Giscus comments integration."""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestCommentsConfig:
    def test_comments_config_exists(self):
        config = REPO_ROOT / "tools" / "comments_config.json"
        assert config.exists()

    def test_comments_config_disabled_by_default(self):
        config = REPO_ROOT / "tools" / "comments_config.json"
        data = json.loads(config.read_text(encoding="utf-8"))
        assert data.get("enabled") is False

    def test_comments_config_has_no_fake_ids(self):
        config = REPO_ROOT / "tools" / "comments_config.json"
        data = json.loads(config.read_text(encoding="utf-8"))
        repo_id = data.get("repo_id", "")
        category_id = data.get("category_id", "")
        fake_patterns = ["XXXX", "xxxx", "fake", "placeholder", "example", "todo", "fixme"]
        for val in (repo_id, category_id):
            for pattern in fake_patterns:
                assert pattern not in val.lower(), f"ID contains fake pattern: {pattern}"

    def test_comments_config_has_required_fields(self):
        config = REPO_ROOT / "tools" / "comments_config.json"
        data = json.loads(config.read_text(encoding="utf-8"))
        required = ["enabled", "provider", "repo", "repo_id", "category", "category_id",
                    "mapping", "strict", "reactions_enabled", "emit_metadata",
                    "input_position", "theme", "lang"]
        for field in required:
            assert field in data, f"Missing field: {field}"


class TestGiscusPartial:
    def test_giscus_partial_exists(self):
        partial = REPO_ROOT / "templates" / "partials" / "giscus.html.j2"
        assert partial.exists()

    def test_giscus_partial_contains_official_script(self):
        partial = REPO_ROOT / "templates" / "partials" / "giscus.html.j2"
        text = partial.read_text(encoding="utf-8")
        assert "giscus.app/client.js" in text
        assert "data-repo" in text
        assert "data-repo-id" in text
        assert "data-category-id" in text
        assert "crossorigin=\"anonymous\"" in text
        assert "async" in text

    def test_giscus_partial_uses_pathname_mapping(self):
        partial = REPO_ROOT / "templates" / "partials" / "giscus.html.j2"
        text = partial.read_text(encoding="utf-8")
        assert "data-mapping" in text
        # Template uses the Jinja2 variable; the config file contains the value
        assert "{{ comments_config.mapping }}" in text or "pathname" in text

    def test_giscus_partial_renders_nothing_when_disabled(self):
        partial = REPO_ROOT / "templates" / "partials" / "giscus.html.j2"
        text = partial.read_text(encoding="utf-8")
        assert "{% if comments_config and comments_config.enabled" in text

    def test_giscus_partial_has_accessible_note(self):
        partial = REPO_ROOT / "templates" / "partials" / "giscus.html.j2"
        text = partial.read_text(encoding="utf-8")
        assert "aria-label=\"Comments\"" in text or "aria-label=\"Comments" in text
        assert "GitHub account" in text or "GitHub" in text


class TestArticleTemplate:
    def test_article_template_includes_giscus_partial(self):
        article = REPO_ROOT / "templates" / "article.html.j2"
        text = article.read_text(encoding="utf-8")
        assert "partials/giscus.html.j2" in text

    def test_base_template_does_not_include_giscus(self):
        base = REPO_ROOT / "templates" / "base.html.j2"
        text = base.read_text(encoding="utf-8")
        assert "giscus" not in text.lower()


class TestRenderedPages:
    def test_build_site_does_not_render_giscus_when_disabled(self, monkeypatch, tmp_path):
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

        # Write a disabled comments config
        comments_config = tmp_path / "tools"
        comments_config.mkdir(exist_ok=True)
        comments_config.joinpath("comments_config.json").write_text(
            json.dumps({"enabled": False, "provider": "giscus", "repo": "test/test", "repo_id": "", "category": "Comments", "category_id": ""}),
            encoding="utf-8",
        )

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "COMMENTS_CONFIG_PATH", tmp_path / "tools" / "comments_config.json")

        article_dir = tmp_path / "articles" / "2026-01-01-test"
        article_dir.mkdir(parents=True)
        article_dir.joinpath("article.md").write_text("---\ntitle: Test\n---\n# Test\n\nBody.\n", encoding="utf-8")
        article_dir.joinpath("metadata.json").write_text(
            json.dumps({"title": "Test", "published_date": "2026-01-01", "canonical_url": "https://example.com", "slug": "test"}),
            encoding="utf-8",
        )

        index = {
            "articles": [{"folder": "2026-01-01-test", "title": "Test", "published_date": "2026-01-01", "canonical_url": "https://example.com", "slug": "test", "topics": []}],
            "topics": {},
            "topics_with_page": [],
        }
        m.build_site(index)

        article_html = (tmp_path / "site" / "articles" / "test" / "index.html").read_text(encoding="utf-8")
        assert "giscus.app/client.js" not in article_html

    def test_article_page_renders_giscus_when_enabled_with_ids(self, monkeypatch, tmp_path):
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

        comments_config = tmp_path / "tools"
        comments_config.mkdir(exist_ok=True)
        comments_config.joinpath("comments_config.json").write_text(
            json.dumps({
                "enabled": True,
                "provider": "giscus",
                "repo": "First-AI-Movers/articles",
                "repo_id": "R_kgDORealId",
                "category": "Comments",
                "category_id": "DIC_kwDORealId",
                "mapping": "pathname",
                "strict": "0",
                "reactions_enabled": "1",
                "emit_metadata": "0",
                "input_position": "bottom",
                "theme": "preferred_color_scheme",
                "lang": "en",
            }),
            encoding="utf-8",
        )

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "COMMENTS_CONFIG_PATH", tmp_path / "tools" / "comments_config.json")

        article_dir = tmp_path / "articles" / "2026-01-01-test"
        article_dir.mkdir(parents=True)
        article_dir.joinpath("article.md").write_text("---\ntitle: Test\n---\n# Test\n\nBody.\n", encoding="utf-8")
        article_dir.joinpath("metadata.json").write_text(
            json.dumps({"title": "Test", "published_date": "2026-01-01", "canonical_url": "https://example.com", "slug": "test"}),
            encoding="utf-8",
        )

        index = {
            "articles": [{"folder": "2026-01-01-test", "title": "Test", "published_date": "2026-01-01", "canonical_url": "https://example.com", "slug": "test", "topics": []}],
            "topics": {},
            "topics_with_page": [],
        }
        m.build_site(index)

        article_html = (tmp_path / "site" / "articles" / "test" / "index.html").read_text(encoding="utf-8")
        assert "giscus.app/client.js" in article_html
        assert "R_kgDORealId" in article_html
        assert "DIC_kwDORealId" in article_html
        assert "pathname" in article_html

    def test_home_topic_about_do_not_render_giscus(self, monkeypatch, tmp_path):
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

        comments_config = tmp_path / "tools"
        comments_config.mkdir(exist_ok=True)
        comments_config.joinpath("comments_config.json").write_text(
            json.dumps({
                "enabled": True,
                "provider": "giscus",
                "repo": "First-AI-Movers/articles",
                "repo_id": "R_kgDORealId",
                "category": "Comments",
                "category_id": "DIC_kwDORealId",
                "mapping": "pathname",
                "strict": "0",
                "reactions_enabled": "1",
                "emit_metadata": "0",
                "input_position": "bottom",
                "theme": "preferred_color_scheme",
                "lang": "en",
            }),
            encoding="utf-8",
        )

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "COMMENTS_CONFIG_PATH", tmp_path / "tools" / "comments_config.json")
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

        home = (tmp_path / "site" / "index.html").read_text(encoding="utf-8")
        topic = (tmp_path / "site" / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        about = (tmp_path / "site" / "about" / "index.html").read_text(encoding="utf-8")

        assert "giscus.app/client.js" not in home
        assert "giscus.app/client.js" not in topic
        assert "giscus.app/client.js" not in about


class TestDocs:
    def test_comments_docs_exist(self):
        doc = REPO_ROOT / "docs" / "COMMENTS.md"
        assert doc.exists()
        text = doc.read_text(encoding="utf-8")
        assert "Giscus" in text

    def test_comments_docs_include_setup_and_rollback(self):
        doc = REPO_ROOT / "docs" / "COMMENTS.md"
        text = doc.read_text(encoding="utf-8")
        assert "Enabling comments" in text or "enable" in text.lower()
        assert "Disabling comments" in text or "disable" in text.lower()
        assert "rollback" in text.lower()

    def test_comments_docs_warn_github_account_required(self):
        doc = REPO_ROOT / "docs" / "COMMENTS.md"
        text = doc.read_text(encoding="utf-8")
        assert "GitHub" in text

    def test_no_article_metadata_changed_for_comments(self):
        # Verify no metadata.json files contain comments-related keys
        articles_dir = REPO_ROOT / "articles"
        for meta in articles_dir.rglob("metadata.json"):
            data = json.loads(meta.read_text(encoding="utf-8"))
            assert "comments_enabled" not in data, f"Unexpected comments_enabled in {meta}"
