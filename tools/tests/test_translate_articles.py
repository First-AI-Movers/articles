#!/usr/bin/env python3
"""Tests for E39b translate_articles.py tool — Gate 1 (mock provider only)."""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TRANSLATE_ARTICLES = REPO_ROOT / "tools" / "translate_articles.py"


class TestTranslateArticlesTool:
    def _import_module(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("translate_articles", TRANSLATE_ARTICLES)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["translate_articles"] = mod
        spec.loader.exec_module(mod)
        return mod

    def _setup_article(self, tmp_path, mod, slug="test"):
        folder = "2026-04-01-test"
        (tmp_path / "articles" / folder).mkdir(parents=True)
        meta = {
            "folder": folder,
            "slug": slug,
            "title": "Test Article",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
        }
        (tmp_path / "articles" / folder / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        (tmp_path / "articles" / folder / "article.md").write_text(
            "---\ntitle: Test\n---\n\n# Test Article\n\nBody text here.\n",
            encoding="utf-8",
        )
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")
        return folder, meta

    def test_dry_run_writes_nothing(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        self._setup_article(tmp_path, mod)

        result = mod.main(["--dry-run", "--slug", "test", "--lang", "es", "--provider", "mock"])
        assert result == 0
        assert not (tmp_path / "translations" / "reviews" / "test.es.review.md").exists()
        # No article files created
        assert not list((tmp_path / "articles").rglob("article.*.md"))

    def test_mock_provider_creates_review_file(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        self._setup_article(tmp_path, mod)

        result = mod.main(["--write-review-files", "--slug", "test", "--lang", "es", "--provider", "mock"])
        assert result == 0
        review = (tmp_path / "translations" / "reviews" / "test.es.review.md").read_text(encoding="utf-8")
        assert "## Translated body" in review
        assert "Status: draft" in review
        assert "[MOCK ES]" in review

    def test_review_file_contains_terminology_table(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        self._setup_article(tmp_path, mod)

        result = mod.main(["--write-review-files", "--slug", "test", "--lang", "es", "--provider", "mock"])
        assert result == 0
        review = (tmp_path / "translations" / "reviews" / "test.es.review.md").read_text(encoding="utf-8")
        assert "## Terminology check" in review
        assert "| Term | Expected | Found |" in review
        assert "EU AI Act" in review

    def test_review_file_has_required_metadata(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        self._setup_article(tmp_path, mod)

        result = mod.main(["--write-review-files", "--slug", "test", "--lang", "es", "--provider", "mock"])
        assert result == 0
        review = (tmp_path / "translations" / "reviews" / "test.es.review.md").read_text(encoding="utf-8")
        assert "- **Slug:** test" in review
        assert "- **Language:** es" in review
        assert "- **Model:** mock" in review
        assert "- **Source chars:**" in review
        assert "- **Generated at:**" in review

    def test_draft_review_does_not_apply(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        folder, _ = self._setup_article(tmp_path, mod)

        # Generate review file
        mod.main(["--write-review-files", "--slug", "test", "--lang", "es", "--provider", "mock"])
        # Try to apply (should skip because status is draft)
        result = mod.main(["--apply-approved", "--slug", "test", "--lang", "es"])
        assert result == 0
        assert not (tmp_path / "articles" / folder / "article.es.md").exists()

    def test_approved_review_creates_article_lang_md(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        folder, _ = self._setup_article(tmp_path, mod)

        # Generate review file
        mod.main(["--write-review-files", "--slug", "test", "--lang", "es", "--provider", "mock"])
        # Mark as approved
        review_path = tmp_path / "translations" / "reviews" / "test.es.review.md"
        text = review_path.read_text(encoding="utf-8")
        text = text.replace("Status: draft", "Status: approved")
        text = text.replace("Reviewer:", "Reviewer: Test Reviewer")
        text = text.replace("Reviewed at:", "Reviewed at: 2026-04-29")
        review_path.write_text(text, encoding="utf-8")
        # Apply
        result = mod.main(["--apply-approved", "--slug", "test", "--lang", "es"])
        assert result == 0
        assert (tmp_path / "articles" / folder / "article.es.md").exists()
        # Verify translations.json was created
        tj = json.loads((tmp_path / "articles" / folder / "translations.json").read_text(encoding="utf-8"))
        assert tj["es"]["status"] == "published"
        assert tj["es"]["reviewer"] == "Test Reviewer"
        assert tj["es"]["reviewed_at"] == "2026-04-29"

    def test_character_budget_report(self, tmp_path, monkeypatch, capsys):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        self._setup_article(tmp_path, mod)

        mod.main(["--dry-run", "--slug", "test", "--lang", "es,fr", "--provider", "mock"])
        captured = capsys.readouterr()
        assert "Budget report:" in captured.out
        assert "Monthly budget:" in captured.out
        assert "Remaining:" in captured.out

    def test_invalid_language_rejected(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        self._setup_article(tmp_path, mod)

        with pytest.raises(SystemExit) as exc_info:
            mod.main(["--dry-run", "--slug", "test", "--lang", "xx", "--provider", "mock"])
        assert exc_info.value.code == 1

    def test_no_network_in_tests(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        self._setup_article(tmp_path, mod)

        result = mod.main(["--write-review-files", "--slug", "test", "--lang", "es", "--provider", "mock"])
        assert result == 0
        # Mock provider never calls network

    def test_deepl_provider_requires_allow_network(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        self._setup_article(tmp_path, mod)

        with pytest.raises(SystemExit) as exc_info:
            mod.main(["--write-review-files", "--slug", "test", "--lang", "es", "--provider", "deepl"])
        assert exc_info.value.code == 1

    def test_deepl_provider_dry_run_does_not_exit(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        self._setup_article(tmp_path, mod)

        result = mod.main(["--dry-run", "--slug", "test", "--lang", "es", "--provider", "deepl"])
        assert result == 0

    def test_no_original_mutation(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        folder, _ = self._setup_article(tmp_path, mod)
        original = (tmp_path / "articles" / folder / "article.md").read_text(encoding="utf-8")
        original_meta = (tmp_path / "articles" / folder / "metadata.json").read_text(encoding="utf-8")

        mod.main(["--write-review-files", "--slug", "test", "--lang", "es", "--provider", "mock"])

        after = (tmp_path / "articles" / folder / "article.md").read_text(encoding="utf-8")
        after_meta = (tmp_path / "articles" / folder / "metadata.json").read_text(encoding="utf-8")
        assert after == original
        assert after_meta == original_meta

    def test_slug_processes_one_article(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        for i, slug in enumerate(("alpha", "beta")):
            folder = f"2026-04-0{i+1}-{slug}"
            (tmp_path / "articles" / folder).mkdir(parents=True)
            meta = {
                "folder": folder,
                "slug": slug,
                "title": f"Test {slug}",
                "published_date": f"2026-04-0{i+1}",
                "canonical_url": "https://example.com",
            }
            (tmp_path / "articles" / folder / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
            (tmp_path / "articles" / folder / "article.md").write_text(f"# {slug}\n\nBody.\n", encoding="utf-8")

        index = {"articles": [
            {"folder": "2026-04-01-alpha", "slug": "alpha", "title": "Test alpha", "published_date": "2026-04-01", "canonical_url": "https://example.com"},
            {"folder": "2026-04-02-beta", "slug": "beta", "title": "Test beta", "published_date": "2026-04-02", "canonical_url": "https://example.com"},
        ]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        result = mod.main(["--write-review-files", "--slug", "beta", "--lang", "es", "--provider", "mock"])
        assert result == 0
        assert not (tmp_path / "translations" / "reviews" / "alpha.es.review.md").exists()
        assert (tmp_path / "translations" / "reviews" / "beta.es.review.md").exists()


class TestTranslateArticlesDocs:
    def test_translations_docs_exist(self):
        path = REPO_ROOT / "docs" / "TRANSLATIONS.md"
        assert path.exists(), "docs/TRANSLATIONS.md should exist"
        text = path.read_text(encoding="utf-8")
        assert "review" in text.lower()
        assert "draft" in text.lower()
        assert "approved" in text.lower()
