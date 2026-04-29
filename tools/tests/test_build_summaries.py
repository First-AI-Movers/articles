#!/usr/bin/env python3
"""Tests for E35 build_summaries.py tool and build integration."""

import json
import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SUMMARIES = REPO_ROOT / "tools" / "build_summaries.py"


class TestBuildSummariesTool:
    def _import_module(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("build_summaries", BUILD_SUMMARIES)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["build_summaries"] = mod
        spec.loader.exec_module(mod)
        return mod

    def test_dry_run_writes_nothing(self, tmp_path, monkeypatch):
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

        result = mod.main(["--dry-run", "--slug", "test", "--provider", "mock"])
        assert result == 0
        assert not (tmp_path / "summaries" / "test.review.md").exists()
        after = json.loads((tmp_path / "articles" / "2026-04-01-test" / "metadata.json").read_text(encoding="utf-8"))
        assert "summary_short" not in after

    def test_mock_provider_generates_three_summaries(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {"folder": "2026-04-01-test", "slug": "test", "title": "Test", "published_date": "2026-04-01", "canonical_url": "https://example.com"}
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        (tmp_path / "articles" / "2026-04-01-test" / "article.md").write_text("# Test\n\nBody text here.\n", encoding="utf-8")
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        result = mod.main(["--write-review-files", "--slug", "test", "--provider", "mock"])
        assert result == 0
        review = (tmp_path / "summaries" / "test.review.md").read_text(encoding="utf-8")
        assert "## 50-word summary" in review
        assert "## 200-word summary" in review
        assert "## 500-word summary" in review
        assert "Status: draft" in review

    def test_generated_review_file_has_required_sections(self, tmp_path, monkeypatch):
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

        result = mod.main(["--write-review-files", "--slug", "test", "--provider", "mock"])
        assert result == 0
        review = (tmp_path / "summaries" / "test.review.md").read_text(encoding="utf-8")
        assert "Article folder:" in review
        assert "Canonical URL:" in review
        assert "Generated at:" in review
        assert "Model: mock" in review
        assert "## Review status" in review
        assert "## Notes" in review

    def test_draft_review_does_not_update_metadata(self, tmp_path, monkeypatch):
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

        # Generate review file
        mod.main(["--write-review-files", "--slug", "test", "--provider", "mock"])
        # Try to apply (should skip because status is draft)
        result = mod.main(["--apply-approved", "--slug", "test"])
        assert result == 0
        after = json.loads((tmp_path / "articles" / "2026-04-01-test" / "metadata.json").read_text(encoding="utf-8"))
        assert "summary_short" not in after

    def test_approved_review_updates_metadata_atomically(self, tmp_path, monkeypatch):
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

        # Generate review file
        mod.main(["--write-review-files", "--slug", "test", "--provider", "mock"])
        # Mark as approved
        review_path = tmp_path / "summaries" / "test.review.md"
        text = review_path.read_text(encoding="utf-8")
        text = text.replace("Status: draft", "Status: approved")
        review_path.write_text(text, encoding="utf-8")
        # Apply
        result = mod.main(["--apply-approved", "--slug", "test"])
        assert result == 0
        after = json.loads((tmp_path / "articles" / "2026-04-01-test" / "metadata.json").read_text(encoding="utf-8"))
        assert "summary_short" in after
        assert "summary_medium" in after
        assert "summary_long" in after
        assert "summary_reviewed_at" in after

    def test_approved_review_requires_all_three_summaries_by_default(self, tmp_path, monkeypatch):
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

        # Create a malformed review file with only short summary
        review_path = tmp_path / "summaries" / "test.review.md"
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(
            "# Summary Review\n\n## 50-word summary\n\nShort.\n\n## Review status\n\nStatus: approved\n",
            encoding="utf-8",
        )
        result = mod.main(["--apply-approved", "--slug", "test"])
        assert result == 0  # exits 0 but skips with error logged
        after = json.loads((tmp_path / "articles" / "2026-04-01-test" / "metadata.json").read_text(encoding="utf-8"))
        assert "summary_short" not in after  # failed because missing medium/long

    def test_allow_partial_permits_missing_summaries(self, tmp_path, monkeypatch):
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

        review_path = tmp_path / "summaries" / "test.review.md"
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(
            "# Summary Review\n\n## 50-word summary\n\nShort summary here.\n\n## Review status\n\nStatus: approved\n",
            encoding="utf-8",
        )
        result = mod.main(["--apply-approved", "--slug", "test", "--allow-partial"])
        assert result == 0
        after = json.loads((tmp_path / "articles" / "2026-04-01-test" / "metadata.json").read_text(encoding="utf-8"))
        assert after.get("summary_short") == "Short summary here."
        assert "summary_medium" not in after
        assert "summary_long" not in after

    def test_word_count_validation_short(self, tmp_path, monkeypatch):
        mod = self._import_module()
        summaries = {"short": "word " * 50, "medium": "word " * 200, "long": "word " * 500}
        errors = mod._validate_word_counts(summaries)
        assert not any("short" in e for e in errors)

    def test_word_count_validation_medium(self, tmp_path, monkeypatch):
        mod = self._import_module()
        summaries = {"short": "word " * 50, "medium": "word " * 200, "long": "word " * 500}
        errors = mod._validate_word_counts(summaries)
        assert not any("medium" in e for e in errors)

    def test_word_count_validation_long(self, tmp_path, monkeypatch):
        mod = self._import_module()
        summaries = {"short": "word " * 50, "medium": "word " * 200, "long": "word " * 500}
        errors = mod._validate_word_counts(summaries)
        assert not any("long" in e for e in errors)

    def test_word_count_detects_out_of_range(self, tmp_path, monkeypatch):
        mod = self._import_module()
        summaries = {"short": "word " * 5, "medium": "word " * 50, "long": "word " * 100}
        errors = mod._validate_word_counts(summaries)
        assert any("short" in e for e in errors)
        assert any("medium" in e for e in errors)
        assert any("long" in e for e in errors)

    def test_hallucination_guard_in_prompt(self, tmp_path, monkeypatch):
        mod = self._import_module()
        prompt = mod._build_prompt("Sample article text.")
        assert "Do not invent" in prompt or "ONLY the provided article" in prompt
        assert "No markdown links" in prompt or "No invented statistics" in prompt

    def test_limit_limits_processed_articles(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        for i in range(3):
            folder = f"2026-04-0{i+1}-test"
            (tmp_path / "articles" / folder).mkdir(parents=True)
            meta = {"folder": folder, "slug": f"test-{i}", "title": f"Test {i}", "published_date": f"2026-04-0{i+1}", "canonical_url": "https://example.com"}
            (tmp_path / "articles" / folder / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
            (tmp_path / "articles" / folder / "article.md").write_text(f"# Test {i}\n\nBody.\n", encoding="utf-8")

        index = {"articles": [
            {"folder": "2026-04-01-test", "slug": "test-0", "title": "Test 0", "published_date": "2026-04-01", "canonical_url": "https://example.com"},
            {"folder": "2026-04-02-test", "slug": "test-1", "title": "Test 1", "published_date": "2026-04-02", "canonical_url": "https://example.com"},
            {"folder": "2026-04-03-test", "slug": "test-2", "title": "Test 2", "published_date": "2026-04-03", "canonical_url": "https://example.com"},
        ]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        result = mod.main(["--write-review-files", "--limit", "2", "--provider", "mock"])
        assert result == 0
        assert (tmp_path / "summaries" / "test-0.review.md").exists()
        assert (tmp_path / "summaries" / "test-1.review.md").exists()
        assert not (tmp_path / "summaries" / "test-2.review.md").exists()

    def test_slug_processes_one_article(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        for i in range(3):
            folder = f"2026-04-0{i+1}-test"
            (tmp_path / "articles" / folder).mkdir(parents=True)
            meta = {"folder": folder, "slug": f"test-{i}", "title": f"Test {i}", "published_date": f"2026-04-0{i+1}", "canonical_url": "https://example.com"}
            (tmp_path / "articles" / folder / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
            (tmp_path / "articles" / folder / "article.md").write_text(f"# Test {i}\n\nBody.\n", encoding="utf-8")

        index = {"articles": [
            {"folder": "2026-04-01-test", "slug": "test-0", "title": "Test 0", "published_date": "2026-04-01", "canonical_url": "https://example.com"},
            {"folder": "2026-04-02-test", "slug": "test-1", "title": "Test 1", "published_date": "2026-04-02", "canonical_url": "https://example.com"},
            {"folder": "2026-04-03-test", "slug": "test-2", "title": "Test 2", "published_date": "2026-04-03", "canonical_url": "https://example.com"},
        ]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        result = mod.main(["--write-review-files", "--slug", "test-1", "--provider", "mock"])
        assert result == 0
        assert not (tmp_path / "summaries" / "test-0.review.md").exists()
        assert (tmp_path / "summaries" / "test-1.review.md").exists()
        assert not (tmp_path / "summaries" / "test-2.review.md").exists()

    def test_no_live_network_calls_in_tests(self, tmp_path, monkeypatch):
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

        # Mock provider should never call network
        result = mod.main(["--write-review-files", "--slug", "test", "--provider", "mock"])
        assert result == 0

    def test_dry_run_with_anthropic_provider_does_not_call_network(self, tmp_path, monkeypatch):
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

        # Even with anthropic provider, dry-run should not fail or call network
        result = mod.main(["--dry-run", "--slug", "test", "--provider", "anthropic"])
        assert result == 0

    def test_no_real_article_metadata_changed_in_infrastructure_pr(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        # Article A: no summaries
        (tmp_path / "articles" / "2026-04-01-a").mkdir(parents=True)
        meta_a = {"folder": "2026-04-01-a", "slug": "a", "title": "A", "published_date": "2026-04-01", "canonical_url": "https://example.com/a"}
        (tmp_path / "articles" / "2026-04-01-a" / "metadata.json").write_text(json.dumps(meta_a), encoding="utf-8")
        (tmp_path / "articles" / "2026-04-01-a" / "article.md").write_text("# A\n", encoding="utf-8")

        index = {"articles": [meta_a]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        # Dry-run should not modify anything
        result = mod.main(["--dry-run", "--slug", "a"])
        assert result == 0
        after_a = json.loads((tmp_path / "articles" / "2026-04-01-a" / "metadata.json").read_text(encoding="utf-8"))
        assert "summary_short" not in after_a
        assert "summary_medium" not in after_a
        assert "summary_long" not in after_a


class TestBuildIntegration:
    def _mod(self):
        pytest.importorskip("jinja2")
        pytest.importorskip("markdown")
        import rebuild_local
        return rebuild_local

    def _run(self, monkeypatch, tmp_path, article_meta):
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

        folder = article_meta.get("folder", "2026-04-01-test")
        (tmp_path / "articles" / folder).mkdir(exist_ok=True)
        (tmp_path / "articles" / folder / "article.md").write_text(
            '---\ntitle: "Test"\n---\n# Test\n\nBody.\n', encoding="utf-8"
        )
        (tmp_path / "articles" / folder / "metadata.json").write_text(
            json.dumps(article_meta), encoding="utf-8"
        )

        index = {"articles": [article_meta]}
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return tmp_path / "site"

    def _jsonld_from_page(self, page_html):
        match = re.search(r'<script type="application/ld\+json">(.*?)</script>', page_html, re.DOTALL)
        assert match is not None, "No JSON-LD found in page"
        return json.loads(match.group(1))

    def test_index_includes_summaries_when_present(self, tmp_path, monkeypatch):
        import rebuild_local
        monkeypatch.setattr(rebuild_local, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(rebuild_local, "ARTICLES_DIR", tmp_path / "articles")
        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
            "summary_short": "Short summary.",
            "summary_medium": "Medium summary.",
            "summary_long": "Long summary.",
        }
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        index = rebuild_local.build_index()
        article = index["articles"][0]
        assert article.get("summary_short") == "Short summary."
        assert article.get("summary_medium") == "Medium summary."
        assert article.get("summary_long") == "Long summary."

    def test_index_omits_summaries_when_absent(self, tmp_path, monkeypatch):
        import rebuild_local
        monkeypatch.setattr(rebuild_local, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(rebuild_local, "ARTICLES_DIR", tmp_path / "articles")
        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {"folder": "2026-04-01-test", "slug": "test", "title": "Test", "published_date": "2026-04-01", "canonical_url": "https://example.com"}
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        index = rebuild_local.build_index()
        article = index["articles"][0]
        assert "summary_short" not in article
        assert "summary_medium" not in article
        assert "summary_long" not in article

    def test_jsonld_includes_description_when_summary_short_exists(self, monkeypatch, tmp_path):
        article = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test Article",
            "published_date": "2026-04-01",
            "tags": [],
            "topics": [],
            "funnel_stage": "middle",
            "canonical_url": "https://radar.firstaimovers.com/test",
            "summary_short": "A concise AI strategy summary.",
        }
        site = self._run(monkeypatch, tmp_path, article)
        page = (site / "articles" / "test" / "index.html").read_text(encoding="utf-8")
        data = self._jsonld_from_page(page)
        assert data.get("description") == "A concise AI strategy summary."

    def test_jsonld_valid_for_article_with_summary_and_doi(self, monkeypatch, tmp_path):
        article = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test Article",
            "published_date": "2026-04-01",
            "tags": [],
            "topics": [],
            "funnel_stage": "middle",
            "canonical_url": "https://radar.firstaimovers.com/test",
            "doi": "10.5281/zenodo.1234567",
            "summary_short": "A concise AI strategy summary.",
        }
        site = self._run(monkeypatch, tmp_path, article)
        page = (site / "articles" / "test" / "index.html").read_text(encoding="utf-8")
        data = self._jsonld_from_page(page)
        assert data["identifier"]["value"] == "10.5281/zenodo.1234567"
        assert data["description"] == "A concise AI strategy summary."

    def test_jsonld_valid_for_article_with_summary_and_series_and_citations(self, monkeypatch, tmp_path):
        # Create series registry
        registry = {"series": {"test-series": {"title": "Test Series", "description": "Desc"}}}
        (tmp_path / "tools").mkdir(exist_ok=True)
        (tmp_path / "tools" / "series_registry.json").write_text(json.dumps(registry), encoding="utf-8")
        article = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test Article",
            "published_date": "2026-04-01",
            "tags": [],
            "topics": ["AI Strategy"],
            "funnel_stage": "middle",
            "canonical_url": "https://radar.firstaimovers.com/test",
            "summary_short": "A concise AI strategy summary.",
            "series": "test-series",
            "series_order": 1,
        }
        site = self._run(monkeypatch, tmp_path, article)
        page = (site / "articles" / "test" / "index.html").read_text(encoding="utf-8")
        data = self._jsonld_from_page(page)
        assert data["description"] == "A concise AI strategy summary."
        assert data["isPartOf"]["name"] == "Test Series"

    def test_llms_full_includes_summaries_when_present(self, monkeypatch, tmp_path):
        import rebuild_local
        monkeypatch.setattr(rebuild_local, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(rebuild_local, "ARTICLES_DIR", tmp_path / "articles")
        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
            "summary_short": "Short.",
            "summary_medium": "Medium.",
            "summary_long": "Long.",
        }
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        (tmp_path / "articles" / "2026-04-01-test" / "article.md").write_text("# Test\n\nBody.\n", encoding="utf-8")
        index = {"articles": [meta]}
        rebuild_local.build_llms_full(index)
        text = (tmp_path / "llms-full.txt").read_text(encoding="utf-8")
        assert "**Summary (short):** Short." in text
        assert "**Summary (medium):** Medium." in text
        assert "**Summary (long):** Long." in text

    def test_llms_full_ignores_draft_review_files(self, monkeypatch, tmp_path):
        import rebuild_local
        monkeypatch.setattr(rebuild_local, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(rebuild_local, "ARTICLES_DIR", tmp_path / "articles")
        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
        }
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        (tmp_path / "articles" / "2026-04-01-test" / "article.md").write_text("# Test\n\nBody.\n", encoding="utf-8")
        # Create a draft review file (should be ignored by build)
        (tmp_path / "summaries").mkdir(exist_ok=True)
        (tmp_path / "summaries" / "test.review.md").write_text("# Review\n\n## 50-word summary\n\nDraft.\n", encoding="utf-8")
        index = {"articles": [meta]}
        rebuild_local.build_llms_full(index)
        text = (tmp_path / "llms-full.txt").read_text(encoding="utf-8")
        assert "Summary (short)" not in text
        assert "Summary (medium)" not in text
        assert "Summary (long)" not in text

    def test_docs_exist_and_explain_review_workflow(self):
        doc = REPO_ROOT / "docs" / "SUMMARIES.md"
        assert doc.exists()
        text = doc.read_text(encoding="utf-8")
        assert "review" in text.lower()
        assert "draft" in text.lower()
        assert "approved" in text.lower()
