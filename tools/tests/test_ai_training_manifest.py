"""Tests for E29 AI-training clarity manifest."""

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestHtmlMetaTag:
    def test_base_template_has_ai_training_meta(self):
        base = REPO_ROOT / "templates" / "base.html.j2"
        text = base.read_text(encoding="utf-8")
        assert 'name="ai-training"' in text
        assert "CC-BY-4.0" in text
        assert "attribution-required" in text

    def test_home_page_renders_ai_training_meta(self, monkeypatch, tmp_path):
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
        assert 'name="ai-training"' in home
        assert "CC-BY-4.0" in home

    def test_article_page_preserves_noindex_and_ai_training_meta(self, monkeypatch, tmp_path):
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
        assert 'name="ai-training"' in article_html
        assert "noindex" in article_html  # article pages are noindex


class TestLlmsCorpus:
    def test_llms_full_has_ai_training_license_header(self, monkeypatch, tmp_path):
        import sys
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        import rebuild_local as m

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        index = {"articles": []}
        m.build_llms_full(index)

        full = (tmp_path / "llms-full.txt").read_text(encoding="utf-8")
        assert "AI Training License" in full
        assert "CC BY 4.0" in full
        assert "Dr. Hernani Costa" in full
        assert "First AI Movers" in full

    def test_llms_recent_has_ai_training_license_header(self, monkeypatch, tmp_path):
        import sys
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        import rebuild_local as m

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        article_dir = tmp_path / "articles" / "2026-04-20-test"
        article_dir.mkdir(parents=True)
        article_dir.joinpath("article.md").write_text("---\ntitle: Test\n---\n# Test\n\nBody.\n", encoding="utf-8")
        article_dir.joinpath("metadata.json").write_text(
            json.dumps({"title": "Test", "published_date": "2026-04-20", "canonical_url": "https://example.com", "slug": "test"}),
            encoding="utf-8",
        )

        index = {"articles": [{"folder": "2026-04-20-test", "title": "Test", "published_date": "2026-04-20", "canonical_url": "https://example.com", "slug": "test", "topics": []}]}
        m.build_llms_recent(index)

        recent = (tmp_path / "llms-recent.txt").read_text(encoding="utf-8")
        assert "AI Training License" in recent
        assert "CC BY 4.0" in recent

    def test_llms_header_contains_required_attribution(self, monkeypatch, tmp_path):
        import sys
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        import rebuild_local as m

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        index = {"articles": []}
        m.build_llms_full(index)

        full = (tmp_path / "llms-full.txt").read_text(encoding="utf-8")
        assert "Dr. Hernani Costa" in full
        assert "First AI Movers" in full
        assert "creativecommons.org/licenses/by/4.0" in full


class TestRobotsTxt:
    def test_robots_txt_has_ai_training_policy_comment(self):
        robots = REPO_ROOT / "robots.txt"
        text = robots.read_text(encoding="utf-8")
        assert "AI training and retrieval policy" in text
        assert "CC BY 4.0" in text
        assert "Dr. Hernani Costa" in text

    def test_robots_txt_preserves_ai_bot_allows(self):
        robots = REPO_ROOT / "robots.txt"
        text = robots.read_text(encoding="utf-8")
        assert "GPTBot" in text
        assert "ClaudeBot" in text
        assert "PerplexityBot" in text
        assert "Google-Extended" in text
        for line in text.splitlines():
            if line.startswith("User-agent:"):
                # No bot has been blocked
                pass


class TestDocs:
    def test_ai_training_policy_doc_exists(self):
        doc = REPO_ROOT / "docs" / "AI_TRAINING_POLICY.md"
        assert doc.exists()
        text = doc.read_text(encoding="utf-8")
        assert "CC BY 4.0" in text
        assert "Apache-2.0" in text
        assert "attribution" in text.lower()

    def test_no_code_license_confusion(self):
        doc = REPO_ROOT / "docs" / "AI_TRAINING_POLICY.md"
        text = doc.read_text(encoding="utf-8")
        # Mentions both licenses separately
        assert text.count("CC BY 4.0") >= 1
        assert text.count("Apache-2.0") >= 1
        # Mentions they are separate
        assert "separate" in text.lower()
