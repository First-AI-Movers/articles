#!/usr/bin/env python3
"""Tests for check_translation_quality.py — AI-QA review file validator."""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECK_QUALITY = REPO_ROOT / "tools" / "check_translation_quality.py"


class TestCheckTranslationQuality:
    def _import_module(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("check_translation_quality", CHECK_QUALITY)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["check_translation_quality"] = mod
        spec.loader.exec_module(mod)
        return mod

    def _make_review_file(self, tmp_path, slug="test", lang="es", **overrides):
        """Create a review file with customizable fields."""
        reviews_dir = tmp_path / "translations" / "reviews"
        reviews_dir.mkdir(parents=True, exist_ok=True)
        review_path = reviews_dir / f"{slug}.{lang}.review.md"

        defaults = {
            "slug": slug,
            "lang": lang,
            "original_title": "Test Article",
            "translated_title": "Artículo de prueba",
            "source_url": "https://example.com",
            "canonical_url": "https://example.com/es",
            "model": "deepl",
            "source_chars": 100,
            "generated_at": "2026-05-01",
            "body": "# Artículo de prueba\n\nTexto del cuerpo.\n\n## Sección\n\nMás texto.\n",
            "status": "approved",
            "approval_method": "ai_qa",
            "reviewer": "",
            "reviewed_at": "",
            "quality_checked_at": "2026-05-01",
            "quality_check_model": "claude-3.5-sonnet",
            "reviewer_notes": "",
        }
        defaults.update(overrides)

        lines = [
            f"# Translation Review — {defaults['original_title']}\n",
            f"- **Slug:** {defaults['slug']}",
            f"- **Language:** {defaults['lang']}",
            f"- **Target language name:** Spanish",
            f"- **Original title:** {defaults['original_title']}",
            f"- **Translated title:** {defaults['translated_title']}",
            f"- **Source URL:** {defaults['source_url']}",
            f"- **Canonical URL:** {defaults['canonical_url']}",
            f"- **Model:** {defaults['model']}",
            f"- **Source chars:** {defaults['source_chars']}",
            f"- **Generated at:** {defaults['generated_at']}",
            "",
            "## Terminology check",
            "",
            "| Term | Expected | Found |",
            "|---|---|---|",
            "| GDPR | RGPD | [x] |",
            "",
            "## Translated body",
            "",
            defaults["body"],
            "",
            "## Review status",
            "",
            f"Status: {defaults['status']}",
            f"Approval method: {defaults['approval_method']}",
            f"Reviewer: {defaults['reviewer']}",
            f"Reviewed at: {defaults['reviewed_at']}",
            f"Quality checked at: {defaults['quality_checked_at']}",
            f"Quality check model: {defaults['quality_check_model']}",
            "",
            "## Reviewer notes",
            "",
            defaults["reviewer_notes"],
        ]
        review_path.write_text("\n".join(lines), encoding="utf-8")
        return review_path

    def _setup_source_article(self, tmp_path, slug="test"):
        """Create a minimal source article for comparative checks."""
        articles_dir = tmp_path / "articles"
        folder = f"2026-04-01-{slug}"
        (articles_dir / folder).mkdir(parents=True)
        (articles_dir / folder / "article.md").write_text(
            "---\ntitle: Test\n---\n\n# Test Article\n\nBody text here.\n\n## Section\n\nMore text.\n",
            encoding="utf-8",
        )
        meta = {
            "folder": folder,
            "slug": slug,
            "title": "Test Article",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
        }
        (articles_dir / folder / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")
        return folder

    def test_valid_ai_qa_review_passes(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        self._setup_source_article(tmp_path)
        review_path = self._make_review_file(tmp_path)

        errors, warnings = mod.check_review_file(review_path)
        assert errors == []
        assert warnings == []

    def test_missing_quality_checked_at_fails(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        self._setup_source_article(tmp_path)
        review_path = self._make_review_file(tmp_path, quality_checked_at="")

        errors, warnings = mod.check_review_file(review_path)
        assert any("Quality checked at" in e for e in errors)

    def test_missing_quality_check_model_fails(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        self._setup_source_article(tmp_path)
        review_path = self._make_review_file(tmp_path, quality_check_model="")

        errors, warnings = mod.check_review_file(review_path)
        assert any("Quality check model" in e for e in errors)

    def test_draft_status_fails(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        self._setup_source_article(tmp_path)
        review_path = self._make_review_file(tmp_path, status="draft")

        errors, warnings = mod.check_review_file(review_path)
        assert any("status is 'draft'" in e for e in errors)

    def test_missing_translated_body_fails(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        self._setup_source_article(tmp_path)
        review_path = self._make_review_file(tmp_path, body="")

        errors, warnings = mod.check_review_file(review_path)
        assert any("missing translated body" in e for e in errors)

    def test_broken_code_fence_fails(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        self._setup_source_article(tmp_path)
        review_path = self._make_review_file(
            tmp_path,
            body="# Title\n\n```python\nprint('hello')\n",
        )

        errors, warnings = mod.check_review_file(review_path)
        assert any("unbalanced code fence" in e for e in errors)

    def test_mock_placeholder_fails(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        self._setup_source_article(tmp_path)
        review_path = self._make_review_file(
            tmp_path,
            body="# [MOCK ES] Title\n\nMOCK TRANSLATION placeholder text.\n",
        )

        errors, warnings = mod.check_review_file(review_path)
        assert any("mock/placeholder" in e for e in errors)

    def test_glossary_missing_in_strict_mode_fails(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        # Source contains GDPR but translation does not contain RGPD
        folder = "2026-04-01-test"
        (tmp_path / "articles" / folder).mkdir(parents=True)
        (tmp_path / "articles" / folder / "article.md").write_text(
            "---\ntitle: Test\n---\n\n# Test\n\nGDPR is important.\n",
            encoding="utf-8",
        )
        meta = {
            "folder": folder,
            "slug": "test",
            "title": "Test Article",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
        }
        (tmp_path / "articles" / folder / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        review_path = self._make_review_file(tmp_path, body="# Título\n\nTexto sin términos.\n")

        errors, warnings = mod.check_review_file(review_path, strict=True)
        assert any("GDPR" in e and "RGPD" in e for e in errors)

    def test_source_link_loss_detected(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        folder = "2026-04-01-test"
        (tmp_path / "articles" / folder).mkdir(parents=True)
        (tmp_path / "articles" / folder / "article.md").write_text(
            "---\ntitle: Test\n---\n\n# Test\n\nSee [link](https://example.com/page).\n",
            encoding="utf-8",
        )
        meta = {
            "folder": folder,
            "slug": "test",
            "title": "Test Article",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
        }
        (tmp_path / "articles" / folder / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        review_path = self._make_review_file(tmp_path, body="# Título\n\nSin enlaces.\n")

        errors, warnings = mod.check_review_file(review_path)
        assert any("source links possibly missing" in w for w in warnings)

    def test_human_review_file_warns_but_no_error(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        self._setup_source_article(tmp_path)
        review_path = self._make_review_file(
            tmp_path,
            approval_method="human",
            reviewer="Dr. Hernani Costa",
            reviewed_at="2026-04-30",
            quality_checked_at="",
            quality_check_model="",
        )

        errors, warnings = mod.check_review_file(review_path)
        assert errors == []
        assert any("human" in w.lower() for w in warnings)

    def test_heading_count_drop_warns(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        folder = "2026-04-01-test"
        (tmp_path / "articles" / folder).mkdir(parents=True)
        (tmp_path / "articles" / folder / "article.md").write_text(
            "---\ntitle: Test\n---\n\n# Test\n\n## A\n\n## B\n\n## C\n\n## D\n",
            encoding="utf-8",
        )
        meta = {
            "folder": folder,
            "slug": "test",
            "title": "Test Article",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
        }
        (tmp_path / "articles" / folder / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        # Translation has only 1 heading vs 4 in source
        review_path = self._make_review_file(tmp_path, body="# Título\n\nSolo texto.\n")

        errors, warnings = mod.check_review_file(review_path)
        assert any("heading count dropped severely" in e for e in errors)

    def test_quality_checked_at_bad_format_fails(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        self._setup_source_article(tmp_path)
        review_path = self._make_review_file(tmp_path, quality_checked_at="01 May 2026")

        errors, warnings = mod.check_review_file(review_path)
        assert any("YYYY-MM-DD" in e for e in errors)


class TestCheckTranslationQualityCLI:
    def _import_module(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("check_translation_quality", CHECK_QUALITY)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["check_translation_quality"] = mod
        spec.loader.exec_module(mod)
        return mod

    def test_main_no_review_files(self, tmp_path, monkeypatch, capsys):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "REVIEWS_DIR", tmp_path / "translations" / "reviews")

        result = mod.main([])
        assert result == 0
        captured = capsys.readouterr()
        assert "No review files found" in captured.out

    def test_main_valid_file_exits_zero(self, tmp_path, monkeypatch, capsys):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")
        monkeypatch.setattr(mod, "REVIEWS_DIR", tmp_path / "translations" / "reviews")

        # Setup source article
        folder = "2026-04-01-test"
        (tmp_path / "articles" / folder).mkdir(parents=True)
        (tmp_path / "articles" / folder / "article.md").write_text(
            "---\ntitle: Test\n---\n\n# Test\n\nBody.\n",
            encoding="utf-8",
        )
        meta = {
            "folder": folder,
            "slug": "test",
            "title": "Test Article",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
        }
        (tmp_path / "articles" / folder / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        # Setup review file
        reviews_dir = tmp_path / "translations" / "reviews"
        reviews_dir.mkdir(parents=True)
        review_path = reviews_dir / "test.es.review.md"
        lines = [
            "# Translation Review — Test Article\n",
            "- **Slug:** test",
            "- **Language:** es",
            "- **Translated title:** Artículo de prueba",
            "- **Model:** deepl",
            "- **Source chars:** 100",
            "- **Generated at:** 2026-05-01",
            "",
            "## Translated body",
            "",
            "# Artículo de prueba\n\nTexto del cuerpo.\n",
            "",
            "## Review status",
            "",
            "Status: approved",
            "Approval method: ai_qa",
            "Reviewer:",
            "Reviewed at:",
            "Quality checked at: 2026-05-01",
            "Quality check model: claude-3.5-sonnet",
            "",
            "## Reviewer notes",
            "",
        ]
        review_path.write_text("\n".join(lines), encoding="utf-8")

        result = mod.main([])
        captured = capsys.readouterr()
        assert result == 0
        assert "checked=1 passed=1" in captured.out

    def test_main_invalid_lang_exits_one(self, tmp_path, monkeypatch, capsys):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "REVIEWS_DIR", tmp_path / "translations" / "reviews")

        result = mod.main(["--lang", "xx"])
        assert result == 1
        captured = capsys.readouterr()
        assert "invalid language code" in (captured.out + captured.err).lower()

    def test_main_slug_filter(self, tmp_path, monkeypatch, capsys):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")
        monkeypatch.setattr(mod, "REVIEWS_DIR", tmp_path / "translations" / "reviews")

        # Setup two source articles
        for slug in ("alpha", "beta"):
            folder = f"2026-04-01-{slug}"
            (tmp_path / "articles" / folder).mkdir(parents=True)
            (tmp_path / "articles" / folder / "article.md").write_text(
                "---\ntitle: Test\n---\n\n# Test\n\nBody.\n",
                encoding="utf-8",
            )
            meta = {
                "folder": folder,
                "slug": slug,
                "title": "Test Article",
                "published_date": "2026-04-01",
                "canonical_url": "https://example.com",
            }
            (tmp_path / "articles" / folder / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")

        index = {"articles": [
            {"folder": "2026-04-01-alpha", "slug": "alpha", "title": "Alpha", "published_date": "2026-04-01", "canonical_url": "https://example.com"},
            {"folder": "2026-04-01-beta", "slug": "beta", "title": "Beta", "published_date": "2026-04-01", "canonical_url": "https://example.com"},
        ]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        # Setup two review files
        reviews_dir = tmp_path / "translations" / "reviews"
        reviews_dir.mkdir(parents=True)
        for slug in ("alpha", "beta"):
            review_path = reviews_dir / f"{slug}.es.review.md"
            lines = [
                f"# Translation Review — {slug}\n",
                f"- **Slug:** {slug}",
                "- **Language:** es",
                "- **Translated title:** Título",
                "- **Model:** deepl",
                "- **Source chars:** 100",
                "- **Generated at:** 2026-05-01",
                "",
                "## Translated body",
                "",
                "# Título\n\nTexto.\n",
                "",
                "## Review status",
                "",
                "Status: approved",
                "Approval method: ai_qa",
                "Reviewer:",
                "Reviewed at:",
                "Quality checked at: 2026-05-01",
                "Quality check model: claude-3.5-sonnet",
                "",
                "## Reviewer notes",
                "",
            ]
            review_path.write_text("\n".join(lines), encoding="utf-8")

        result = mod.main(["--slug", "beta"])
        captured = capsys.readouterr()
        assert result == 0
        assert "checked=1 passed=1" in captured.out
        assert "alpha" not in captured.out

    def test_main_strict_converts_warnings_to_errors(self, tmp_path, monkeypatch, capsys):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")
        monkeypatch.setattr(mod, "REVIEWS_DIR", tmp_path / "translations" / "reviews")

        # Source with GDPR
        folder = "2026-04-01-test"
        (tmp_path / "articles" / folder).mkdir(parents=True)
        (tmp_path / "articles" / folder / "article.md").write_text(
            "---\ntitle: Test\n---\n\n# Test\n\nGDPR is important.\n",
            encoding="utf-8",
        )
        meta = {
            "folder": folder,
            "slug": "test",
            "title": "Test Article",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
        }
        (tmp_path / "articles" / folder / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        # Review without RGPD
        reviews_dir = tmp_path / "translations" / "reviews"
        reviews_dir.mkdir(parents=True)
        review_path = reviews_dir / "test.es.review.md"
        lines = [
            "# Translation Review — Test\n",
            "- **Slug:** test",
            "- **Language:** es",
            "- **Translated title:** Título",
            "- **Model:** deepl",
            "- **Source chars:** 100",
            "- **Generated at:** 2026-05-01",
            "",
            "## Translated body",
            "",
            "# Título\n\nTexto sin términos.\n",
            "",
            "## Review status",
            "",
            "Status: approved",
            "Approval method: ai_qa",
            "Reviewer:",
            "Reviewed at:",
            "Quality checked at: 2026-05-01",
            "Quality check model: claude-3.5-sonnet",
            "",
            "## Reviewer notes",
            "",
        ]
        review_path.write_text("\n".join(lines), encoding="utf-8")

        result = mod.main(["--strict"])
        captured = capsys.readouterr()
        assert result == 1
        assert "ERROR" in captured.out
        assert "GDPR" in captured.out


class TestCheckTranslationQualityDocs:
    def test_checker_docs_exist(self):
        path = REPO_ROOT / "docs" / "TRANSLATIONS.md"
        assert path.exists(), "docs/TRANSLATIONS.md should exist"
        text = path.read_text(encoding="utf-8")
        assert "check_translation_quality" in text or "quality check" in text.lower()
