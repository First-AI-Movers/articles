#!/usr/bin/env python3
"""Tests for check_translations.py sidecar validator."""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestCheckTranslations:
    def test_passes_when_no_translation_files(self, tmp_path, monkeypatch):
        import check_translations as ct
        monkeypatch.setattr(ct, "ARTICLES_DIR", tmp_path / "articles")
        (tmp_path / "articles").mkdir()
        report = ct.validate_all()
        assert report["files_checked"] == 0
        assert report["errors"] == 0
        assert report["entries"] == 0

    def test_valid_published_translation_passes(self, tmp_path, monkeypatch):
        import check_translations as ct
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("translations.json").write_text(
            json.dumps({
                "es": {
                    "status": "published",
                    "title": "Título de prueba",
                    "reviewed_at": "2026-04-29",
                    "reviewer": "Dr. Hernani Costa",
                    "model": "deepl-free",
                    "source_chars": 13435,
                }
            }),
            encoding="utf-8",
        )
        monkeypatch.setattr(ct, "ARTICLES_DIR", articles)
        report = ct.validate_all()
        assert report["files_checked"] == 1
        assert report["entries"] == 1
        assert report["errors"] == 0

    def test_published_without_title_fails(self, tmp_path, monkeypatch):
        import check_translations as ct
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("translations.json").write_text(
            json.dumps({
                "es": {
                    "status": "published",
                    "reviewed_at": "2026-04-29",
                    "reviewer": "Dr. Hernani Costa",
                }
            }),
            encoding="utf-8",
        )
        monkeypatch.setattr(ct, "ARTICLES_DIR", articles)
        report = ct.validate_all()
        assert report["errors"] > 0
        assert any("requires 'title'" in e for e in report["results"][0]["errors"])

    def test_published_without_reviewer_fails(self, tmp_path, monkeypatch):
        import check_translations as ct
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("translations.json").write_text(
            json.dumps({
                "es": {
                    "status": "published",
                    "title": "Título",
                    "reviewed_at": "2026-04-29",
                }
            }),
            encoding="utf-8",
        )
        monkeypatch.setattr(ct, "ARTICLES_DIR", articles)
        report = ct.validate_all()
        assert report["errors"] > 0
        assert any("requires 'reviewer'" in e for e in report["results"][0]["errors"])

    def test_published_without_reviewed_at_fails(self, tmp_path, monkeypatch):
        import check_translations as ct
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("translations.json").write_text(
            json.dumps({
                "es": {
                    "status": "published",
                    "title": "Título",
                    "reviewer": "Dr. Hernani Costa",
                }
            }),
            encoding="utf-8",
        )
        monkeypatch.setattr(ct, "ARTICLES_DIR", articles)
        report = ct.validate_all()
        assert report["errors"] > 0
        assert any("requires 'reviewed_at'" in e for e in report["results"][0]["errors"])

    def test_published_with_bad_reviewed_at_format_fails(self, tmp_path, monkeypatch):
        import check_translations as ct
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("translations.json").write_text(
            json.dumps({
                "es": {
                    "status": "published",
                    "title": "Título",
                    "reviewed_at": "29 April 2026",
                    "reviewer": "Dr. Hernani Costa",
                }
            }),
            encoding="utf-8",
        )
        monkeypatch.setattr(ct, "ARTICLES_DIR", articles)
        report = ct.validate_all()
        assert report["errors"] > 0
        assert any("YYYY-MM-DD" in e for e in report["results"][0]["errors"])

    def test_draft_without_optional_fields_passes(self, tmp_path, monkeypatch):
        import check_translations as ct
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("translations.json").write_text(
            json.dumps({
                "es": {
                    "status": "draft",
                }
            }),
            encoding="utf-8",
        )
        monkeypatch.setattr(ct, "ARTICLES_DIR", articles)
        report = ct.validate_all()
        assert report["files_checked"] == 1
        assert report["entries"] == 1
        assert report["errors"] == 0

    def test_invalid_language_code_fails(self, tmp_path, monkeypatch):
        import check_translations as ct
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("translations.json").write_text(
            json.dumps({
                "it": {
                    "status": "draft",
                }
            }),
            encoding="utf-8",
        )
        monkeypatch.setattr(ct, "ARTICLES_DIR", articles)
        report = ct.validate_all()
        assert report["errors"] > 0
        assert any("Unknown language code" in e for e in report["results"][0]["errors"])

    def test_unknown_property_fails(self, tmp_path, monkeypatch):
        import check_translations as ct
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("translations.json").write_text(
            json.dumps({
                "es": {
                    "status": "draft",
                    "extra_field": "should fail",
                }
            }),
            encoding="utf-8",
        )
        monkeypatch.setattr(ct, "ARTICLES_DIR", articles)
        report = ct.validate_all()
        assert report["errors"] > 0
        assert any("Unknown property" in e for e in report["results"][0]["errors"])

    def test_json_output(self, tmp_path, monkeypatch):
        import check_translations as ct
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("translations.json").write_text(
            json.dumps({
                "es": {
                    "status": "published",
                    "title": "Título",
                    "reviewed_at": "2026-04-29",
                    "reviewer": "Dr. Hernani Costa",
                }
            }),
            encoding="utf-8",
        )
        monkeypatch.setattr(ct, "ARTICLES_DIR", articles)
        report = ct.validate_all()
        assert report["files_checked"] == 1
        assert report["entries"] == 1
        assert report["errors"] == 0
        assert report["results"][0]["folder"] == "2026-04-01-test"

    def test_multiple_languages_in_one_file(self, tmp_path, monkeypatch):
        import check_translations as ct
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("translations.json").write_text(
            json.dumps({
                "es": {
                    "status": "published",
                    "title": "Título ES",
                    "reviewed_at": "2026-04-29",
                    "reviewer": "Dr. Hernani Costa",
                },
                "fr": {
                    "status": "draft",
                }
            }),
            encoding="utf-8",
        )
        monkeypatch.setattr(ct, "ARTICLES_DIR", articles)
        report = ct.validate_all()
        assert report["files_checked"] == 1
        assert report["entries"] == 2
        assert report["errors"] == 0


class TestCheckTranslationsAiQa:
    def test_ai_qa_published_without_human_reviewer_passes(self, tmp_path, monkeypatch):
        import check_translations as ct
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("translations.json").write_text(
            json.dumps({
                "es": {
                    "status": "published",
                    "title": "Título AI",
                    "approval_method": "ai_qa",
                    "ai_generated": True,
                    "quality_checked_at": "2026-05-01",
                    "quality_check_model": "claude-3.5-sonnet",
                    "model": "deepl",
                    "source_chars": 1000,
                }
            }),
            encoding="utf-8",
        )
        monkeypatch.setattr(ct, "ARTICLES_DIR", articles)
        report = ct.validate_all()
        assert report["files_checked"] == 1
        assert report["entries"] == 1
        assert report["errors"] == 0

    def test_ai_qa_published_without_quality_checked_at_fails(self, tmp_path, monkeypatch):
        import check_translations as ct
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("translations.json").write_text(
            json.dumps({
                "es": {
                    "status": "published",
                    "title": "Título AI",
                    "approval_method": "ai_qa",
                    "ai_generated": True,
                    "model": "deepl",
                }
            }),
            encoding="utf-8",
        )
        monkeypatch.setattr(ct, "ARTICLES_DIR", articles)
        report = ct.validate_all()
        assert report["errors"] > 0
        assert any("quality_checked_at" in e for e in report["results"][0]["errors"])

    def test_ai_qa_published_without_ai_generated_fails(self, tmp_path, monkeypatch):
        import check_translations as ct
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("translations.json").write_text(
            json.dumps({
                "es": {
                    "status": "published",
                    "title": "Título AI",
                    "approval_method": "ai_qa",
                    "quality_checked_at": "2026-05-01",
                    "model": "deepl",
                }
            }),
            encoding="utf-8",
        )
        monkeypatch.setattr(ct, "ARTICLES_DIR", articles)
        report = ct.validate_all()
        assert report["errors"] > 0
        assert any("ai_generated" in e for e in report["results"][0]["errors"])

    def test_human_published_still_requires_reviewer(self, tmp_path, monkeypatch):
        import check_translations as ct
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("translations.json").write_text(
            json.dumps({
                "es": {
                    "status": "published",
                    "title": "Título",
                    "reviewed_at": "2026-04-29",
                    # reviewer missing
                }
            }),
            encoding="utf-8",
        )
        monkeypatch.setattr(ct, "ARTICLES_DIR", articles)
        report = ct.validate_all()
        assert report["errors"] > 0
        assert any("requires 'reviewer'" in e for e in report["results"][0]["errors"])

    def test_ai_qa_published_with_bad_quality_checked_at_format_fails(self, tmp_path, monkeypatch):
        import check_translations as ct
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("translations.json").write_text(
            json.dumps({
                "es": {
                    "status": "published",
                    "title": "Título AI",
                    "approval_method": "ai_qa",
                    "ai_generated": True,
                    "quality_checked_at": "01 May 2026",
                    "model": "deepl",
                }
            }),
            encoding="utf-8",
        )
        monkeypatch.setattr(ct, "ARTICLES_DIR", articles)
        report = ct.validate_all()
        assert report["errors"] > 0
        assert any("YYYY-MM-DD" in e for e in report["results"][0]["errors"])
