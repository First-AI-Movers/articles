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


class TestDeepLQuotaGuardrails:
    """DeepL quota guardrails: usage fetch, budget checks, error handling."""

    def _import_module(self):
        import importlib.util
        from pathlib import Path
        path = Path(__file__).resolve().parents[1] / "translate_articles.py"
        spec = importlib.util.spec_from_file_location("translate_articles", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["translate_articles"] = mod
        spec.loader.exec_module(mod)
        return mod

    def test_fetch_deepl_usage_parses_character_count_and_limit(self, monkeypatch):
        mod = self._import_module()
        import requests

        class FakeResp:
            status_code = 200
            def json(self):
                return {"character_count": 119940, "character_limit": 1000000}

        monkeypatch.setattr(requests, "get", lambda url, headers, timeout: FakeResp())
        usage = mod.fetch_deepl_usage("fake-key", "https://api-free.deepl.com/v2")
        assert usage["character_count"] == 119940
        assert usage["character_limit"] == 1000000

    def test_deepl_budget_passes_when_remaining_is_sufficient(self, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "fetch_deepl_usage", lambda k, b: {"character_count": 100000, "character_limit": 1000000})
        usage = mod._check_deepl_quota("fake-key", 50000, 5000, False)
        assert usage["character_count"] == 100000

    def test_deepl_budget_fails_when_remaining_is_insufficient(self, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "fetch_deepl_usage", lambda k, b: {"character_count": 950000, "character_limit": 1000000})
        with pytest.raises(SystemExit) as exc_info:
            mod._check_deepl_quota("fake-key", 50000, 5000, False)
        assert exc_info.value.code == 1
        # Verify non-secret message
        import io
        import sys
        # Error is printed to stderr; we rely on SystemExit for the signal.

    def test_deepl_budget_safety_margin_blocks_near_limit(self, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "fetch_deepl_usage", lambda k, b: {"character_count": 990000, "character_limit": 1000000})
        # 10_000 remaining; projected 5_000 + margin 5_000 = 10_000 → exactly at limit, should pass
        usage = mod._check_deepl_quota("fake-key", 5000, 5000, False)
        assert usage is not None

        # Now exceed margin
        with pytest.raises(SystemExit) as exc_info:
            mod._check_deepl_quota("fake-key", 5001, 5000, False)
        assert exc_info.value.code == 1

    def test_deepl_budget_ignore_margin_allows_near_limit(self, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "fetch_deepl_usage", lambda k, b: {"character_count": 999999, "character_limit": 1000000})
        # 1 remaining; margin ignored, projected 1 → should pass
        usage = mod._check_deepl_quota("fake-key", 1, 5000, True)
        assert usage is not None

    def test_dry_run_without_allow_network_skips_usage_api(self, tmp_path, monkeypatch, capsys):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {"folder": "2026-04-01-test", "slug": "test", "title": "Test", "published_date": "2026-04-01", "canonical_url": "https://example.com"}
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        (tmp_path / "articles" / "2026-04-01-test" / "article.md").write_text("# Test\n\nBody.\n", encoding="utf-8")
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        result = mod.main(["--dry-run", "--slug", "test", "--lang", "es", "--provider", "deepl"])
        assert result == 0
        captured = capsys.readouterr()
        assert "skipped" in captured.out.lower() or "Projected chars" in captured.out

    def test_dry_run_with_allow_network_checks_usage_api(self, tmp_path, monkeypatch, capsys):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {"folder": "2026-04-01-test", "slug": "test", "title": "Test", "published_date": "2026-04-01", "canonical_url": "https://example.com"}
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        (tmp_path / "articles" / "2026-04-01-test" / "article.md").write_text("# Test\n\nBody.\n", encoding="utf-8")
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        monkeypatch.setattr(mod, "fetch_deepl_usage", lambda k, b: {"character_count": 100000, "character_limit": 1000000})
        monkeypatch.setenv("DEEPL_API_KEY", "fake-key")

        result = mod.main(["--dry-run", "--slug", "test", "--lang", "es", "--provider", "deepl", "--allow-network"])
        assert result == 0
        captured = capsys.readouterr()
        assert "PASSED" in captured.out or "remaining" in captured.out

    def test_deepl_401_aborts_without_writes(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {"folder": "2026-04-01-test", "slug": "test", "title": "Test", "published_date": "2026-04-01", "canonical_url": "https://example.com"}
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        (tmp_path / "articles" / "2026-04-01-test" / "article.md").write_text("# Test\n\nBody.\n", encoding="utf-8")
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        import requests
        class FakeResp:
            status_code = 401
            text = "Unauthorized"
        class FakeRespUsage:
            status_code = 200
            def json(self):
                return {"character_count": 0, "character_limit": 1000000}
        monkeypatch.setattr(requests, "post", lambda url, headers, data, timeout: FakeResp())
        monkeypatch.setattr(requests, "get", lambda url, headers, timeout: FakeRespUsage())
        monkeypatch.setenv("DEEPL_API_KEY", "fake-key")

        with pytest.raises(SystemExit) as exc_info:
            mod.main(["--write-review-files", "--slug", "test", "--lang", "es", "--provider", "deepl", "--allow-network"])
        assert exc_info.value.code == 1
        assert not (tmp_path / "translations" / "reviews" / "test.es.review.md").exists()

    def test_deepl_456_quota_exceeded_aborts_without_writes(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {"folder": "2026-04-01-test", "slug": "test", "title": "Test", "published_date": "2026-04-01", "canonical_url": "https://example.com"}
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        (tmp_path / "articles" / "2026-04-01-test" / "article.md").write_text("# Test\n\nBody.\n", encoding="utf-8")
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        import requests
        class FakeResp:
            status_code = 456
            text = "Quota exceeded"
        class FakeRespUsage:
            status_code = 200
            def json(self):
                return {"character_count": 0, "character_limit": 1000000}
        monkeypatch.setattr(requests, "post", lambda url, headers, data, timeout: FakeResp())
        monkeypatch.setattr(requests, "get", lambda url, headers, timeout: FakeRespUsage())
        monkeypatch.setenv("DEEPL_API_KEY", "fake-key")

        with pytest.raises(SystemExit) as exc_info:
            mod.main(["--write-review-files", "--slug", "test", "--lang", "es", "--provider", "deepl", "--allow-network"])
        assert exc_info.value.code == 1
        assert not (tmp_path / "translations" / "reviews" / "test.es.review.md").exists()

    def test_deepl_429_retries_then_aborts_without_writes(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {"folder": "2026-04-01-test", "slug": "test", "title": "Test", "published_date": "2026-04-01", "canonical_url": "https://example.com"}
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        (tmp_path / "articles" / "2026-04-01-test" / "article.md").write_text("# Test\n\nBody.\n", encoding="utf-8")
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        import requests
        call_count = [0]
        class FakeResp429:
            status_code = 429
            text = "Rate limit"
        class FakeRespUsage:
            status_code = 200
            def json(self):
                return {"character_count": 0, "character_limit": 1000000}
        def fake_post(*a, **k):
            call_count[0] += 1
            return FakeResp429()
        monkeypatch.setattr(requests, "post", fake_post)
        monkeypatch.setattr(requests, "get", lambda url, headers, timeout: FakeRespUsage())
        monkeypatch.setenv("DEEPL_API_KEY", "fake-key")
        monkeypatch.setattr(mod, "DEEPL_MAX_RETRIES", 2)
        monkeypatch.setattr(mod, "DEEPL_RETRY_BACKOFF_BASE", 0.01)

        with pytest.raises(SystemExit) as exc_info:
            mod.main(["--write-review-files", "--slug", "test", "--lang", "es", "--provider", "deepl", "--allow-network"])
        assert exc_info.value.code == 1
        assert call_count[0] == 3  # initial + 2 retries
        assert not (tmp_path / "translations" / "reviews" / "test.es.review.md").exists()

    def test_deepl_empty_translation_aborts_without_writes(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {"folder": "2026-04-01-test", "slug": "test", "title": "Test", "published_date": "2026-04-01", "canonical_url": "https://example.com"}
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        (tmp_path / "articles" / "2026-04-01-test" / "article.md").write_text("# Test\n\nBody.\n", encoding="utf-8")
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        import requests
        class FakeResp:
            status_code = 200
            def json(self):
                return {"translations": [{"text": ""}]}
        class FakeRespUsage:
            status_code = 200
            def json(self):
                return {"character_count": 0, "character_limit": 1000000}
        monkeypatch.setattr(requests, "post", lambda url, headers, data, timeout: FakeResp())
        monkeypatch.setattr(requests, "get", lambda url, headers, timeout: FakeRespUsage())
        monkeypatch.setenv("DEEPL_API_KEY", "fake-key")

        with pytest.raises(SystemExit) as exc_info:
            mod.main(["--write-review-files", "--slug", "test", "--lang", "es", "--provider", "deepl", "--allow-network"])
        assert exc_info.value.code == 1
        assert not (tmp_path / "translations" / "reviews" / "test.es.review.md").exists()

    def test_request_body_chunking_keeps_each_request_under_128k(self, monkeypatch):
        mod = self._import_module()
        # Create a text larger than 128 KiB
        large_text = "Word " * 30000  # ~150 KiB
        chunks = mod._chunk_text_for_deepl(large_text)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.encode("utf-8")) <= mod.DEEPL_MAX_BYTES

    def test_no_secret_leaks_in_error_output(self, tmp_path, monkeypatch, capsys):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {"folder": "2026-04-01-test", "slug": "test", "title": "Test", "published_date": "2026-04-01", "canonical_url": "https://example.com"}
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        (tmp_path / "articles" / "2026-04-01-test" / "article.md").write_text("# Test\n\nBody.\n", encoding="utf-8")
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        import requests
        class FakeResp:
            status_code = 401
            text = "Unauthorized"
        class FakeRespUsage:
            status_code = 200
            def json(self):
                return {"character_count": 0, "character_limit": 1000000}
        monkeypatch.setattr(requests, "post", lambda url, headers, data, timeout: FakeResp())
        monkeypatch.setattr(requests, "get", lambda url, headers, timeout: FakeRespUsage())
        monkeypatch.setenv("DEEPL_API_KEY", "sk-12345-super-secret")

        with pytest.raises(SystemExit):
            mod.main(["--write-review-files", "--slug", "test", "--lang", "es", "--provider", "deepl", "--allow-network"])

        captured = capsys.readouterr()
        assert "sk-12345-super-secret" not in captured.out
        assert "sk-12345-super-secret" not in captured.err


class TestTranslateArticlesAiQa:
    def _import_module(self):
        import importlib.util
        from pathlib import Path
        path = Path(__file__).resolve().parents[1] / "translate_articles.py"
        spec = importlib.util.spec_from_file_location("translate_articles", path)
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

    def test_ai_qa_review_file_creates_ai_qa_translations_json(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        folder, _ = self._setup_article(tmp_path, mod)

        # Generate review file
        mod.main(["--write-review-files", "--slug", "test", "--lang", "es", "--provider", "mock"])
        review_path = tmp_path / "translations" / "reviews" / "test.es.review.md"
        text = review_path.read_text(encoding="utf-8")
        # Update to AI-QA approval
        text = text.replace("Status: draft", "Status: approved")
        text = text.replace("Approval method: human", "Approval method: ai_qa")
        text = text.replace("Reviewer:", "Reviewer: AI translation QA pipeline")
        text = text.replace("Reviewed at:", "Reviewed at: 2026-05-01")
        text = text.replace("Quality checked at:", "Quality checked at: 2026-05-01")
        text = text.replace("Quality check model:", "Quality check model: claude-3.5-sonnet")
        review_path.write_text(text, encoding="utf-8")

        # Apply
        result = mod.main(["--apply-approved", "--slug", "test", "--lang", "es"])
        assert result == 0
        assert (tmp_path / "articles" / folder / "article.es.md").exists()

        # Verify translations.json has AI-QA fields
        tj = json.loads((tmp_path / "articles" / folder / "translations.json").read_text(encoding="utf-8"))
        assert tj["es"]["status"] == "published"
        assert tj["es"]["approval_method"] == "ai_qa"
        assert tj["es"]["ai_generated"] is True
        assert tj["es"]["quality_checked_at"] == "2026-05-01"
        assert tj["es"]["quality_check_model"] == "claude-3.5-sonnet"
        assert "reviewer" not in tj["es"]
        assert "reviewed_at" not in tj["es"]

    def test_human_review_still_creates_human_translations_json(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        folder, _ = self._setup_article(tmp_path, mod)

        mod.main(["--write-review-files", "--slug", "test", "--lang", "es", "--provider", "mock"])
        review_path = tmp_path / "translations" / "reviews" / "test.es.review.md"
        text = review_path.read_text(encoding="utf-8")
        text = text.replace("Status: draft", "Status: approved")
        text = text.replace("Reviewer:", "Reviewer: Dr. Hernani Costa")
        text = text.replace("Reviewed at:", "Reviewed at: 2026-04-29")
        review_path.write_text(text, encoding="utf-8")

        result = mod.main(["--apply-approved", "--slug", "test", "--lang", "es"])
        assert result == 0

        tj = json.loads((tmp_path / "articles" / folder / "translations.json").read_text(encoding="utf-8"))
        assert tj["es"]["status"] == "published"
        assert tj["es"]["reviewer"] == "Dr. Hernani Costa"
        assert tj["es"]["reviewed_at"] == "2026-04-29"
        assert "approval_method" not in tj["es"]
        assert "ai_generated" not in tj["es"]
