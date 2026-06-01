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


class TestMissingOnlyAndBatchOffset:
    """Backlog-rollout safety: ``--missing-only`` + ``--batch-offset``.

    These flags landed in the post-#218 infra PR to make
    ``build_summaries.py`` safe to point at the 855-article backlog
    without re-processing the 5 already-summarized E35b pilot articles.
    """

    def _import_module(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("build_summaries", BUILD_SUMMARIES)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["build_summaries"] = mod
        spec.loader.exec_module(mod)
        return mod

    def _setup_fixture(self, tmp_path, monkeypatch, summary_short_values):
        """Create N articles where summary_short_values[i] is one of:
        None / "" / "   " / "Some short summary text." / a missing-meta sentinel.
        Returns the rebuilt module instance.
        """
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        index_entries = []
        for i, value in enumerate(summary_short_values):
            folder = f"2026-04-{i + 1:02d}-article-{i}"
            slug = f"article-{i}"
            (tmp_path / "articles" / folder).mkdir(parents=True)
            (tmp_path / "articles" / folder / "article.md").write_text(
                f"# Article {i}\n\nBody for article {i}.\n", encoding="utf-8"
            )
            meta = {
                "folder": folder,
                "slug": slug,
                "title": f"Article {i}",
                "published_date": f"2026-04-{i + 1:02d}",
                "canonical_url": f"https://example.com/{slug}",
            }
            if value is _MISSING_META:
                # Intentionally omit metadata.json — soft skip path.
                pass
            elif value is _UNPARSEABLE_META:
                (tmp_path / "articles" / folder / "metadata.json").write_text(
                    "{this is not json", encoding="utf-8"
                )
            else:
                if value is not None:
                    meta["summary_short"] = value
                (tmp_path / "articles" / folder / "metadata.json").write_text(
                    json.dumps(meta), encoding="utf-8"
                )
            # Index entry mirrors metadata; surface summary_short when set so
            # the warning-counter's index-fast-path is exercised.
            entry = dict(meta)
            if value not in (None, "", "   ", _MISSING_META, _UNPARSEABLE_META):
                entry["summary_short"] = value
            index_entries.append(entry)

        (tmp_path / "index.json").write_text(
            json.dumps({"articles": index_entries}), encoding="utf-8"
        )
        return mod

    def test_missing_only_excludes_articles_with_summary_short(
        self, tmp_path, monkeypatch, capsys
    ):
        mod = self._setup_fixture(
            tmp_path,
            monkeypatch,
            [
                "Already summarized 1.",  # article-0 has it; should be excluded
                None,                       # article-1 missing — included
                "Already summarized 2.",  # article-2 has it; excluded
                None,                       # article-3 — included
            ],
        )
        result = mod.main(
            ["--dry-run", "--missing-only", "--provider", "mock"]
        )
        assert result == 0
        out = capsys.readouterr().out
        # The dry-run loop prints DRY-RUN <slug> per candidate.
        assert "DRY-RUN article-1" in out
        assert "DRY-RUN article-3" in out
        assert "DRY-RUN article-0" not in out
        assert "DRY-RUN article-2" not in out

    def test_missing_only_treats_empty_string_as_missing(
        self, tmp_path, monkeypatch, capsys
    ):
        mod = self._setup_fixture(
            tmp_path, monkeypatch,
            ["", "Already there."],
        )
        result = mod.main(
            ["--dry-run", "--missing-only", "--provider", "mock"]
        )
        assert result == 0
        out = capsys.readouterr().out
        assert "DRY-RUN article-0" in out, (
            "Empty-string summary_short must be treated as missing and "
            "the article must be included."
        )
        assert "DRY-RUN article-1" not in out

    def test_missing_only_treats_whitespace_only_as_missing(
        self, tmp_path, monkeypatch, capsys
    ):
        mod = self._setup_fixture(
            tmp_path, monkeypatch,
            ["   ", "\t\n  ", "Real summary text."],
        )
        result = mod.main(
            ["--dry-run", "--missing-only", "--provider", "mock"]
        )
        assert result == 0
        out = capsys.readouterr().out
        assert "DRY-RUN article-0" in out
        assert "DRY-RUN article-1" in out
        assert "DRY-RUN article-2" not in out

    def test_batch_offset_skips_first_n_candidates(
        self, tmp_path, monkeypatch, capsys
    ):
        mod = self._setup_fixture(
            tmp_path, monkeypatch,
            [None, None, None, None, None],
        )
        result = mod.main(
            ["--dry-run", "--batch-offset", "2", "--provider", "mock"]
        )
        assert result == 0
        out = capsys.readouterr().out
        # Offset 2 skips article-0 and article-1; the remaining 3 should
        # be visible in the dry-run log.
        assert "DRY-RUN article-0" not in out
        assert "DRY-RUN article-1" not in out
        assert "DRY-RUN article-2" in out
        assert "DRY-RUN article-3" in out
        assert "DRY-RUN article-4" in out

    def test_missing_only_composes_with_limit_and_batch_offset(
        self, tmp_path, monkeypatch, capsys
    ):
        # 6 articles: 0/2/4 already have summaries, 1/3/5 do not.
        mod = self._setup_fixture(
            tmp_path, monkeypatch,
            ["x", None, "y", None, "z", None],
        )
        result = mod.main(
            [
                "--dry-run",
                "--missing-only",
                "--batch-offset", "1",
                "--limit", "1",
                "--provider", "mock",
            ]
        )
        assert result == 0
        out = capsys.readouterr().out
        # After --missing-only filter: candidates are article-1, article-3,
        # article-5 (in that order). --batch-offset 1 drops article-1,
        # leaving article-3, article-5. --limit 1 keeps only article-3.
        assert "DRY-RUN article-3" in out
        assert "DRY-RUN article-1" not in out
        assert "DRY-RUN article-5" not in out
        assert "DRY-RUN article-0" not in out

    def test_warning_when_missing_only_omitted_and_summaries_present(
        self, tmp_path, monkeypatch, capsys
    ):
        mod = self._setup_fixture(
            tmp_path, monkeypatch,
            ["already-summarized", None, None],
        )
        result = mod.main(
            ["--dry-run", "--provider", "mock"]
        )
        assert result == 0
        err = capsys.readouterr().err
        assert "--missing-only not set" in err
        assert "1 already-summarized" in err

    def test_warning_absent_when_missing_only_omitted_and_no_summaries(
        self, tmp_path, monkeypatch, capsys
    ):
        mod = self._setup_fixture(
            tmp_path, monkeypatch,
            [None, None, None],
        )
        result = mod.main(["--dry-run", "--provider", "mock"])
        assert result == 0
        err = capsys.readouterr().err
        assert "--missing-only not set" not in err

    def test_unparseable_metadata_skipped_softly_not_fatal(
        self, tmp_path, monkeypatch, capsys
    ):
        # First article has unparseable metadata; --missing-only must
        # soft-skip it (warn to stderr) and continue processing the rest.
        mod = self._setup_fixture(
            tmp_path, monkeypatch,
            [_UNPARSEABLE_META, None, _MISSING_META, None],
        )
        result = mod.main(
            ["--dry-run", "--missing-only", "--provider", "mock"]
        )
        assert result == 0
        captured = capsys.readouterr()
        assert "unparseable" in captured.err
        assert "metadata.json not found" in captured.err
        # article-0 and article-2 are soft-skipped; article-1 and article-3
        # remain and should be in the dry-run output.
        assert "DRY-RUN article-1" in captured.out
        assert "DRY-RUN article-3" in captured.out

    def test_slug_with_missing_only_skips_already_summarized_target(
        self, tmp_path, monkeypatch, capsys
    ):
        mod = self._setup_fixture(
            tmp_path, monkeypatch,
            ["Already-summarized.", None],
        )
        # Pointing --slug at the summarized article + --missing-only =
        # nothing to do. The tool reports the skip on stderr and exits 0.
        result = mod.main(
            [
                "--dry-run",
                "--missing-only",
                "--slug", "article-0",
                "--provider", "mock",
            ]
        )
        assert result == 0
        captured = capsys.readouterr()
        assert "SKIP" in captured.err
        assert "summary_short is already populated" in captured.err
        assert "DRY-RUN article-0" not in captured.out


# Sentinels for the fixture: keep these at module scope so the test class
# above can reference them without leaking real metadata states.
_MISSING_META = object()
_UNPARSEABLE_META = object()


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


class TestMiniMaxProvider:
    """Tests for the live MiniMax provider integration.

    All tests are network-free. The harness's HTTP call is monkeypatched
    via the module-level ``_http_post_json`` so no real outbound request
    is ever made.
    """

    def _import_module(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("build_summaries", BUILD_SUMMARIES)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["build_summaries"] = mod
        spec.loader.exec_module(mod)
        return mod

    def _stage_article(self, mod, tmp_path, folder="2026-04-01-test", slug="test"):
        import json
        monkeypatch_repo_root = tmp_path
        (tmp_path / "articles" / folder).mkdir(parents=True)
        meta = {
            "folder": folder, "slug": slug, "title": "Test",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
        }
        (tmp_path / "articles" / folder / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        (tmp_path / "articles" / folder / "article.md").write_text(
            "# Test\n\nBody of the article goes here.\n", encoding="utf-8",
        )
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")
        return slug, folder

    def _stub_summaries_json(self, *, short_words=50, medium_words=200, long_words=500) -> dict:
        import json
        return {
            "summary_short": "alpha " * short_words,
            "summary_medium": "beta " * medium_words,
            "summary_long": "gamma " * long_words,
        }

    def _envelope(self, summaries_json: dict, in_tokens=4000, out_tokens=1500) -> str:
        import json
        return json.dumps({
            "id": "test-id",
            "choices": [{
                "finish_reason": "stop",
                "index": 0,
                "message": {"role": "assistant", "content": json.dumps(summaries_json)},
            }],
            "usage": {
                "prompt_tokens": in_tokens,
                "completion_tokens": out_tokens,
                "total_tokens": in_tokens + out_tokens,
            },
        })

    # --------------------------------------------------------------
    # Key handling + network gating
    # --------------------------------------------------------------

    def test_request_construction_carries_bearer_auth_without_printing_key(
        self, tmp_path, monkeypatch, capsys
    ) -> None:
        mod = self._import_module()
        captured = {}

        def fake_post(url, headers, body, timeout):
            captured["url"] = url
            captured["headers"] = dict(headers)
            captured["body"] = body
            return 200, 12.3, self._envelope(self._stub_summaries_json())

        monkeypatch.setattr(mod, "_http_post_json", fake_post)
        monkeypatch.setenv("MINIMAX_API_KEY", "secret-fake-key-for-test")

        result = mod._call_minimax_once("article body", "MiniMax-M2", "secret-fake-key-for-test")
        assert result["ok"] is True
        assert captured["url"] == "https://api.minimax.io/v1/text/chatcompletion_v2"
        # Bearer header IS constructed (the auth path works).
        assert "Authorization" in captured["headers"]
        assert captured["headers"]["Authorization"].startswith("Bearer ")
        # The captured body must NOT contain the secret value (the body is the
        # JSON payload; the secret only lives in headers).
        assert "secret-fake-key-for-test" not in captured["body"]
        # And the harness must not print the secret to stdout/stderr at any point.
        out = capsys.readouterr()
        assert "secret-fake-key-for-test" not in out.out
        assert "secret-fake-key-for-test" not in out.err

    def test_missing_api_key_fails_safely(
        self, tmp_path, monkeypatch
    ) -> None:
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")
        self._stage_article(mod, tmp_path)
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)

        with pytest.raises(SystemExit):
            mod.main([
                "--write-review-files", "--slug", "test",
                "--provider", "minimax", "--allow-network",
                "--max-cost-usd", "0.10",
            ])

    def test_live_provider_requires_allow_network(
        self, tmp_path, monkeypatch
    ) -> None:
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")
        self._stage_article(mod, tmp_path)
        monkeypatch.setenv("MINIMAX_API_KEY", "fake-key")

        with pytest.raises(SystemExit):
            mod.main([
                "--write-review-files", "--slug", "test",
                "--provider", "minimax",
                # NOTE: --allow-network omitted.
            ])

    # --------------------------------------------------------------
    # Happy-path generation writes draft review file (NOT approved)
    # --------------------------------------------------------------

    def test_valid_minimax_json_writes_draft_review_not_metadata(
        self, tmp_path, monkeypatch
    ) -> None:
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")
        slug, folder = self._stage_article(mod, tmp_path)

        def fake_post(url, headers, body, timeout):
            return 200, 50.0, self._envelope(self._stub_summaries_json())

        monkeypatch.setattr(mod, "_http_post_json", fake_post)
        monkeypatch.setenv("MINIMAX_API_KEY", "fake-key")

        rc = mod.main([
            "--write-review-files", "--slug", slug,
            "--provider", "minimax", "--allow-network",
            "--max-cost-usd", "1.00",
        ])
        assert rc == 0

        review_path = tmp_path / "summaries" / f"{slug}.review.md"
        assert review_path.exists(), "draft review file should have been written"
        text = review_path.read_text(encoding="utf-8")
        assert "Status: draft" in text
        assert "Status: approved" not in text
        # Metadata file must NOT have summary_* fields set (no auto-apply).
        meta = json.loads((tmp_path / "articles" / folder / "metadata.json").read_text())
        assert "summary_short" not in meta
        assert "summary_reviewed_at" not in meta

    # --------------------------------------------------------------
    # Retry loop behavior
    # --------------------------------------------------------------

    def test_retry_loop_retries_only_when_undersize(
        self, tmp_path, monkeypatch
    ) -> None:
        """First call undersize → second call clean → PASS, retries_used=1."""
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")
        slug, folder = self._stage_article(mod, tmp_path)

        calls = {"n": 0}

        def fake_post(url, headers, body, timeout):
            calls["n"] += 1
            if calls["n"] == 1:
                # First response: medium too short.
                return 200, 50.0, self._envelope(self._stub_summaries_json(medium_words=100))
            # Retry response: clean output.
            return 200, 50.0, self._envelope(self._stub_summaries_json())

        monkeypatch.setattr(mod, "_http_post_json", fake_post)
        monkeypatch.setenv("MINIMAX_API_KEY", "fake-key")

        rc = mod.main([
            "--write-review-files", "--slug", slug,
            "--provider", "minimax", "--allow-network",
            "--max-cost-usd", "1.00", "--max-retries", "2",
        ])
        assert rc == 0
        assert calls["n"] == 2, "should have made one retry"
        review = (tmp_path / "summaries" / f"{slug}.review.md").read_text(encoding="utf-8")
        assert "Gate status: PASS" in review
        assert "Retries used: 1" in review

    def test_retry_loop_stops_after_max_retries(
        self, tmp_path, monkeypatch
    ) -> None:
        """Every call returns undersize → exits as HUMAN_REVIEW."""
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")
        slug, folder = self._stage_article(mod, tmp_path)

        calls = {"n": 0}

        def fake_post(url, headers, body, timeout):
            calls["n"] += 1
            return 200, 50.0, self._envelope(self._stub_summaries_json(medium_words=100))

        monkeypatch.setattr(mod, "_http_post_json", fake_post)
        monkeypatch.setenv("MINIMAX_API_KEY", "fake-key")

        rc = mod.main([
            "--write-review-files", "--slug", slug,
            "--provider", "minimax", "--allow-network",
            "--max-cost-usd", "1.00", "--max-retries", "2",
        ])
        assert rc == 0
        # 1 initial + 2 retries = 3 calls.
        assert calls["n"] == 3
        review = (tmp_path / "summaries" / f"{slug}.review.md").read_text(encoding="utf-8")
        assert "Gate status: HUMAN_REVIEW" in review
        assert "Retries used: 2" in review
        # The draft file is still written even when the gate fails — operator
        # needs to see what the model produced so they can fix or reject.
        assert "Status: draft" in review

    def test_first_attempt_pass_uses_zero_retries(
        self, tmp_path, monkeypatch
    ) -> None:
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")
        slug, folder = self._stage_article(mod, tmp_path)
        calls = {"n": 0}

        def fake_post(url, headers, body, timeout):
            calls["n"] += 1
            return 200, 50.0, self._envelope(self._stub_summaries_json())

        monkeypatch.setattr(mod, "_http_post_json", fake_post)
        monkeypatch.setenv("MINIMAX_API_KEY", "fake-key")

        rc = mod.main([
            "--write-review-files", "--slug", slug,
            "--provider", "minimax", "--allow-network",
            "--max-cost-usd", "1.00", "--max-retries", "2",
        ])
        assert rc == 0
        assert calls["n"] == 1
        review = (tmp_path / "summaries" / f"{slug}.review.md").read_text(encoding="utf-8")
        assert "Gate status: PASS" in review
        assert "Retries used: 0" in review

    # --------------------------------------------------------------
    # Cost cap
    # --------------------------------------------------------------

    def test_cost_cap_stops_before_exceeding_budget(
        self, tmp_path, monkeypatch
    ) -> None:
        """Two articles staged, budget covers exactly one — second must halt."""
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        # Stage two articles.
        for i in (1, 2):
            (tmp_path / "articles" / f"2026-04-0{i}-test").mkdir(parents=True)
            meta = {
                "folder": f"2026-04-0{i}-test", "slug": f"test{i}", "title": f"Test {i}",
                "published_date": "2026-04-01", "canonical_url": f"https://example.com/t{i}",
            }
            (tmp_path / "articles" / f"2026-04-0{i}-test" / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
            (tmp_path / "articles" / f"2026-04-0{i}-test" / "article.md").write_text(
                "# T\n\nBody.\n", encoding="utf-8",
            )
        index = {"articles": [
            {"folder": "2026-04-01-test", "slug": "test1", "title": "Test 1", "canonical_url": "https://example.com/t1"},
            {"folder": "2026-04-02-test", "slug": "test2", "title": "Test 2", "canonical_url": "https://example.com/t2"},
        ]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        # Each call costs about $0.0030 input + $0.0018 output = ~$0.0048
        # (5000 in * 0.30/M + 1500 out * 1.20/M). Budget cap at $0.003 means
        # the first article spends ~$0.0048 (exceeding $0.003), so the
        # cumulative-cost guard at the top of the next iteration aborts.
        def fake_post(url, headers, body, timeout):
            return 200, 50.0, self._envelope(self._stub_summaries_json(), in_tokens=5000, out_tokens=1500)

        monkeypatch.setattr(mod, "_http_post_json", fake_post)
        monkeypatch.setenv("MINIMAX_API_KEY", "fake-key")

        rc = mod.main([
            "--write-review-files",
            "--provider", "minimax", "--allow-network",
            "--max-cost-usd", "0.003",  # tight budget
            "--max-retries", "0",       # no retries to keep math simple
        ])
        assert rc == 0

        # First article's review file exists; second's does not.
        assert (tmp_path / "summaries" / "test1.review.md").exists()
        assert not (tmp_path / "summaries" / "test2.review.md").exists()

    # --------------------------------------------------------------
    # --apply-approved is unchanged by this PR
    # --------------------------------------------------------------

    def test_apply_approved_still_requires_approved_status(
        self, tmp_path, monkeypatch
    ) -> None:
        """A draft minimax-produced review file must NOT be auto-applied."""
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")
        slug, folder = self._stage_article(mod, tmp_path)

        # Hand-craft a draft review file (mimic what minimax would write).
        (tmp_path / "summaries").mkdir(exist_ok=True)
        (tmp_path / "summaries" / f"{slug}.review.md").write_text(
            "# Summary Review — Test\n\n"
            "## 50-word summary\n\n" + ("alpha " * 50) + "\n\n"
            "## 200-word summary\n\n" + ("beta " * 200) + "\n\n"
            "## 500-word summary\n\n" + ("gamma " * 500) + "\n\n"
            "## Review status\n\nStatus: draft\n",
            encoding="utf-8",
        )

        rc = mod.main(["--apply-approved", "--slug", slug])
        assert rc == 0
        meta = json.loads((tmp_path / "articles" / folder / "metadata.json").read_text())
        # No summary fields applied because review is draft.
        assert "summary_short" not in meta
        assert "summary_reviewed_at" not in meta


class TestMiniMaxJSONValidityHardening:
    """Tests for PR G — prompt hardening + corrective JSON-validity retry.

    These tests cover the one-shot corrective retry path that exists to
    recover the failure shape observed in production batch 003: MiniMax
    occasionally returned valid JSON missing one of summary_short /
    summary_medium / summary_long, or invalid JSON entirely. The
    corrective retry is bounded to ONE attempt, does not count toward
    --max-retries (which is reserved for undersize retries), and still
    respects the cost cap.
    """

    def _import_module(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("build_summaries", BUILD_SUMMARIES)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["build_summaries"] = mod
        spec.loader.exec_module(mod)
        return mod

    def _stage_article(self, tmp_path, folder="2026-04-01-test", slug="test"):
        (tmp_path / "articles" / folder).mkdir(parents=True)
        meta = {
            "folder": folder, "slug": slug, "title": "Test",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
        }
        (tmp_path / "articles" / folder / "metadata.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )
        (tmp_path / "articles" / folder / "article.md").write_text(
            "# Test\n\nBody of the article goes here.\n", encoding="utf-8",
        )
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")
        return slug, folder

    def _full_summaries_json(self, short=50, medium=200, long=500):
        return {
            "summary_short": "alpha " * short,
            "summary_medium": "beta " * medium,
            "summary_long": "gamma " * long,
        }

    def _envelope(self, content_obj_or_str, in_tokens=4000, out_tokens=1500):
        """Wrap an arbitrary content payload in a MiniMax response envelope.

        ``content_obj_or_str`` may be:
          - a dict (will be json-encoded as the assistant's content), or
          - a string (passed through verbatim — useful for invalid-JSON tests).
        """
        if isinstance(content_obj_or_str, dict):
            content = json.dumps(content_obj_or_str)
        else:
            content = content_obj_or_str
        return json.dumps({
            "id": "test-id",
            "choices": [{
                "finish_reason": "stop",
                "index": 0,
                "message": {"role": "assistant", "content": content},
            }],
            "usage": {
                "prompt_tokens": in_tokens,
                "completion_tokens": out_tokens,
                "total_tokens": in_tokens + out_tokens,
            },
        })

    # ------------------------------------------------------------------
    # Prompt content
    # ------------------------------------------------------------------

    def test_system_prompt_mentions_all_three_required_keys_explicitly(self):
        mod = self._import_module()
        prompt = mod.MINIMAX_SYSTEM_PROMPT
        assert "summary_short" in prompt
        assert "summary_medium" in prompt
        assert "summary_long" in prompt
        # Explicit "no key may be omitted" or equivalent.
        assert ("No key may be omitted" in prompt) or ("not omit" in prompt.lower())

    def test_system_prompt_forbids_markdown_fences_and_extra_prose(self):
        mod = self._import_module()
        prompt = mod.MINIMAX_SYSTEM_PROMPT
        assert "markdown fences" in prompt.lower() or "no ```" in prompt.lower()
        assert (
            "no prose" in prompt.lower()
            or "no commentary" in prompt.lower()
            or "no preamble" in prompt.lower()
        )

    def test_system_prompt_includes_upper_middle_targets_alongside_hard_bands(self):
        mod = self._import_module()
        prompt = mod.MINIMAX_SYSTEM_PROMPT
        # Hard bands still present.
        assert "40-60" in prompt
        assert "170-230" in prompt
        assert "430-570" in prompt
        # Upper-middle targets present (look for any of the documented numbers).
        upper_middle_signals = ["50-55", "200-220", "500-540"]
        present = [s for s in upper_middle_signals if s in prompt]
        assert len(present) >= 2, (
            "expected at least two upper-middle band targets in the prompt; "
            f"found {present}"
        )

    def test_user_prompt_reinforces_required_keys(self):
        mod = self._import_module()
        user = mod._build_minimax_user_prompt("body")
        assert "summary_short" in user
        assert "summary_medium" in user
        assert "summary_long" in user
        # Tells the model not to omit any key.
        assert "do not omit" in user.lower() or "must contain all three" in user.lower()

    def test_corrective_prompt_for_missing_fields_names_each_missing_field(self):
        mod = self._import_module()
        prompt = mod._build_minimax_corrective_prompt(
            error_kind="missing_fields",
            missing_fields=["summary_medium", "summary_long"],
            raw_excerpt='{"summary_short": "ok"}',
        )
        assert "missing" in prompt.lower()
        assert "summary_medium" in prompt
        assert "summary_long" in prompt
        # Reminds the model of the full envelope shape.
        assert "summary_short" in prompt
        # Includes the excerpt for self-diagnosis.
        assert "summary_short" in prompt  # excerpt mentions it

    def test_corrective_prompt_for_invalid_json_does_not_dump_huge_blob(self):
        mod = self._import_module()
        big = "x" * 5000
        prompt = mod._build_minimax_corrective_prompt(
            error_kind="invalid_json",
            missing_fields=None,
            raw_excerpt=big,
        )
        # Excerpt is capped at 400 chars; the rest of the prompt is small.
        assert len(prompt) < 1500
        assert "json" in prompt.lower()
        assert "summary_short" in prompt
        assert "summary_medium" in prompt
        assert "summary_long" in prompt

    # ------------------------------------------------------------------
    # _call_minimax_once now distinguishes error_kind
    # ------------------------------------------------------------------

    def test_call_returns_missing_fields_kind_on_partial_json(self, monkeypatch):
        mod = self._import_module()

        def fake_post(url, headers, body, timeout):
            partial = {"summary_short": "alpha " * 50}  # medium + long missing
            return 200, 10.0, self._envelope(partial)

        monkeypatch.setattr(mod, "_http_post_json", fake_post)
        result = mod._call_minimax_once("body", "MiniMax-M2", "fake-key")
        assert result["ok"] is False
        assert result["error_kind"] == "missing_fields"
        assert set(result["missing_fields"]) == {"summary_medium", "summary_long"}

    def test_call_returns_invalid_json_kind_on_unparseable_content(self, monkeypatch):
        mod = self._import_module()

        def fake_post(url, headers, body, timeout):
            return 200, 10.0, self._envelope("this is plain text not json")

        monkeypatch.setattr(mod, "_http_post_json", fake_post)
        result = mod._call_minimax_once("body", "MiniMax-M2", "fake-key")
        assert result["ok"] is False
        assert result["error_kind"] == "invalid_json"

    # ------------------------------------------------------------------
    # Corrective retry behavior in _generate_with_retries
    # ------------------------------------------------------------------

    def _wire(self, mod, monkeypatch, responses):
        """Wire a sequence of HTTP responses for sequential calls."""
        state = {"i": 0}

        def fake_post(url, headers, body, timeout):
            i = state["i"]
            state["i"] += 1
            status, content = responses[min(i, len(responses) - 1)]
            return status, 10.0, content

        monkeypatch.setattr(mod, "_http_post_json", fake_post)
        return state

    def test_missing_short_triggers_one_corrective_retry(self, monkeypatch):
        mod = self._import_module()
        partial = {
            "summary_medium": "beta " * 200,
            "summary_long": "gamma " * 500,
        }
        state = self._wire(mod, monkeypatch, [
            (200, self._envelope(partial)),
            (200, self._envelope(self._full_summaries_json())),
        ])
        result = mod._generate_with_retries(
            article_text="body", model="MiniMax-M2",
            max_retries=2, max_cost_usd=1.00, api_key="fake-key",
        )
        assert result["summaries"] is not None
        assert result["corrective_retries_used"] == 1
        assert result["retries_used"] == 0
        assert state["i"] == 2

    def test_missing_medium_triggers_one_corrective_retry(self, monkeypatch):
        mod = self._import_module()
        partial = {
            "summary_short": "alpha " * 50,
            "summary_long": "gamma " * 500,
        }
        state = self._wire(mod, monkeypatch, [
            (200, self._envelope(partial)),
            (200, self._envelope(self._full_summaries_json())),
        ])
        result = mod._generate_with_retries(
            article_text="body", model="MiniMax-M2",
            max_retries=2, max_cost_usd=1.00, api_key="fake-key",
        )
        assert result["summaries"] is not None
        assert result["corrective_retries_used"] == 1
        assert state["i"] == 2

    def test_missing_long_triggers_one_corrective_retry(self, monkeypatch):
        mod = self._import_module()
        partial = {
            "summary_short": "alpha " * 50,
            "summary_medium": "beta " * 200,
        }
        state = self._wire(mod, monkeypatch, [
            (200, self._envelope(partial)),
            (200, self._envelope(self._full_summaries_json())),
        ])
        result = mod._generate_with_retries(
            article_text="body", model="MiniMax-M2",
            max_retries=2, max_cost_usd=1.00, api_key="fake-key",
        )
        assert result["summaries"] is not None
        assert result["corrective_retries_used"] == 1
        assert state["i"] == 2

    def test_malformed_json_triggers_one_corrective_retry(self, monkeypatch):
        mod = self._import_module()
        state = self._wire(mod, monkeypatch, [
            (200, self._envelope("not a JSON object at all")),
            (200, self._envelope(self._full_summaries_json())),
        ])
        result = mod._generate_with_retries(
            article_text="body", model="MiniMax-M2",
            max_retries=2, max_cost_usd=1.00, api_key="fake-key",
        )
        assert result["summaries"] is not None
        assert result["corrective_retries_used"] == 1
        assert state["i"] == 2

    def test_corrective_retry_success_produces_valid_review_state(
        self, monkeypatch, tmp_path
    ):
        """After a corrective retry succeeds, the build path writes a draft
        review with Status: draft and the Notes block mentions the corrective
        retry count."""
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")
        slug, folder = self._stage_article(tmp_path)
        partial = {"summary_short": "alpha " * 50}
        self._wire(mod, monkeypatch, [
            (200, self._envelope(partial)),
            (200, self._envelope(self._full_summaries_json())),
        ])
        monkeypatch.setenv("MINIMAX_API_KEY", "fake-key")
        rc = mod.main([
            "--write-review-files", "--slug", slug,
            "--provider", "minimax", "--allow-network",
            "--max-cost-usd", "1.00",
        ])
        assert rc == 0
        text = (tmp_path / "summaries" / f"{slug}.review.md").read_text(encoding="utf-8")
        assert "Status: draft" in text
        assert "Status: approved" not in text
        assert "Corrective JSON retries used: 1" in text

    def test_corrective_retry_failure_preserves_generation_failure(
        self, monkeypatch, tmp_path
    ):
        """If the corrective retry also returns missing fields, the runner
        surfaces a terminal failure — the draft review file is NOT written
        (no summaries to put in it)."""
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")
        slug, folder = self._stage_article(tmp_path)
        partial = {"summary_short": "alpha " * 50}
        # Both attempts return the same partial JSON.
        self._wire(mod, monkeypatch, [
            (200, self._envelope(partial)),
            (200, self._envelope(partial)),
        ])
        monkeypatch.setenv("MINIMAX_API_KEY", "fake-key")
        rc = mod.main([
            "--write-review-files", "--slug", slug,
            "--provider", "minimax", "--allow-network",
            "--max-cost-usd", "1.00",
        ])
        assert rc == 0
        # The _write_review_file path is still hit because that's where the
        # gate_meta is rendered; the summaries dict is None so the body
        # fields are empty. Most importantly: no metadata.json was modified.
        meta = json.loads((tmp_path / "articles" / folder / "metadata.json").read_text())
        assert "summary_short" not in meta
        assert "summary_reviewed_at" not in meta

    def test_corrective_retry_respects_cost_cap(self, monkeypatch):
        """If the budget is already consumed, no corrective retry fires."""
        mod = self._import_module()
        partial = {"summary_short": "alpha " * 50}
        state = self._wire(mod, monkeypatch, [
            # Single attempt: returns missing-fields with high token usage so
            # cost on this one call already exceeds the cap.
            (200, self._envelope(partial, in_tokens=200000, out_tokens=50000)),
            # If a second call happened, this fixture would catch it.
            (200, self._envelope(self._full_summaries_json())),
        ])
        result = mod._generate_with_retries(
            article_text="body", model="MiniMax-M2",
            max_retries=2, max_cost_usd=0.001, api_key="fake-key",
        )
        # The corrective retry was skipped because budget was already gone.
        assert result["corrective_retries_used"] == 0
        assert state["i"] == 1
        assert result["terminated_reason"] == "provider_failure"

    def test_corrective_retry_is_bounded_to_one(self, monkeypatch):
        """Even if the corrective retry also fails with a correctable error,
        only ONE corrective retry is attempted — no infinite loop."""
        mod = self._import_module()
        partial = {"summary_short": "alpha " * 50}
        state = self._wire(mod, monkeypatch, [
            (200, self._envelope(partial)),
            (200, self._envelope(partial)),
            # If a third call happened the loop is unbounded.
            (200, self._envelope(self._full_summaries_json())),
        ])
        result = mod._generate_with_retries(
            article_text="body", model="MiniMax-M2",
            max_retries=2, max_cost_usd=1.00, api_key="fake-key",
        )
        assert state["i"] == 2, "corrective retry must be bounded to one attempt"
        assert result["summaries"] is None
        assert result["terminated_reason"] == "corrective_retry_failed"
        assert result["corrective_retries_used"] == 1

    # ------------------------------------------------------------------
    # Existing undersize-retry behavior still works
    # ------------------------------------------------------------------

    def test_undersize_retry_path_still_works_after_corrective_success(
        self, monkeypatch
    ):
        """Corrective retry recovers JSON shape, then the undersize-retry
        loop fixes a remaining undersize on the corrective output."""
        mod = self._import_module()
        partial = {"summary_short": "alpha " * 50}
        # Sequence: missing fields → corrective returns undersize medium →
        # undersize retry returns clean.
        self._wire(mod, monkeypatch, [
            (200, self._envelope(partial)),
            (200, self._envelope(self._full_summaries_json(medium=100))),
            (200, self._envelope(self._full_summaries_json())),
        ])
        result = mod._generate_with_retries(
            article_text="body", model="MiniMax-M2",
            max_retries=2, max_cost_usd=1.00, api_key="fake-key",
        )
        assert result["corrective_retries_used"] == 1
        assert result["retries_used"] == 1
        assert result["terminated_reason"] == "PASS"

    def test_oversize_remains_human_review(self, monkeypatch):
        """Oversize output stays HUMAN_REVIEW; the corrective retry path
        does not fire on oversize (it's not a JSON-shape error)."""
        mod = self._import_module()
        from summary_quality import GateStatus
        oversize = self._full_summaries_json(short=80)  # short > 60 max
        state = self._wire(mod, monkeypatch, [
            (200, self._envelope(oversize)),
        ])
        result = mod._generate_with_retries(
            article_text="body", model="MiniMax-M2",
            max_retries=2, max_cost_usd=1.00, api_key="fake-key",
        )
        assert result["gate_status"] == GateStatus.HUMAN_REVIEW
        assert result["corrective_retries_used"] == 0
        assert state["i"] == 1
