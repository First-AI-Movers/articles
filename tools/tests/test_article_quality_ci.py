#!/usr/bin/env python3
"""Contract tests for article quality CI configuration (Vale, Lychee, workflow, docs)."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestValeConfig:
    def test_vale_ini_exists(self):
        assert (REPO_ROOT / ".vale.ini").exists()

    def test_vale_ini_mentions_fam_style(self):
        text = (REPO_ROOT / ".vale.ini").read_text(encoding="utf-8")
        assert "FAM" in text

    def test_fam_style_directory_exists(self):
        assert (REPO_ROOT / ".vale" / "styles" / "FAM").is_dir()

    def test_hype_rule_exists(self):
        path = REPO_ROOT / ".vale" / "styles" / "FAM" / "Hype.yml"
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "extends: existence" in text
        assert "revolutionary" in text.lower()

    def test_weak_phrases_rule_exists(self):
        path = REPO_ROOT / ".vale" / "styles" / "FAM" / "WeakPhrases.yml"
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "extends: existence" in text
        assert "dive into" in text.lower()

    def test_terminology_rule_exists(self):
        path = REPO_ROOT / ".vale" / "styles" / "FAM" / "Terminology.yml"
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "extends: substitution" in text
        assert "AI governance" in text


class TestLycheeConfig:
    def test_lychee_toml_exists(self):
        assert (REPO_ROOT / ".lychee.toml").exists()

    def test_lychee_toml_has_include(self):
        text = (REPO_ROOT / ".lychee.toml").read_text(encoding="utf-8")
        assert "include" in text

    def test_lychee_excludes_known_noisy_domains(self):
        text = (REPO_ROOT / ".lychee.toml").read_text(encoding="utf-8")
        assert "linkedin.com" in text or "twitter.com" in text or "x.com" in text


class TestWorkflow:
    def test_article_quality_workflow_exists(self):
        assert (REPO_ROOT / ".github" / "workflows" / "article-quality.yml").exists()

    def test_workflow_is_soft_non_blocking(self):
        text = (
            REPO_ROOT / ".github" / "workflows" / "article-quality.yml"
        ).read_text(encoding="utf-8")
        # Vale and lychee jobs should have continue-on-error
        assert "continue-on-error: true" in text
        # No 'required' status or branch-protection mention
        assert text.count("continue-on-error: true") >= 2

    def test_workflow_triggers_on_pr_and_push(self):
        text = (
            REPO_ROOT / ".github" / "workflows" / "article-quality.yml"
        ).read_text(encoding="utf-8")
        assert "pull_request:" in text
        assert "push:" in text

    def test_workflow_has_readability_job(self):
        text = (
            REPO_ROOT / ".github" / "workflows" / "article-quality.yml"
        ).read_text(encoding="utf-8")
        assert "readability:" in text
        assert "tools/readability.py" in text

    def test_workflow_uploads_artifacts(self):
        text = (
            REPO_ROOT / ".github" / "workflows" / "article-quality.yml"
        ).read_text(encoding="utf-8")
        assert "upload-artifact" in text


class TestDocs:
    def test_article_quality_docs_exist(self):
        assert (REPO_ROOT / "docs" / "ARTICLE_QUALITY_CI.md").exists()

    def test_docs_mention_soft_gate(self):
        text = (REPO_ROOT / "docs" / "ARTICLE_QUALITY_CI.md").read_text(
            encoding="utf-8"
        )
        assert "soft" in text.lower() or "non-blocking" in text.lower()

    def test_docs_mention_editorial_approval(self):
        text = (REPO_ROOT / "docs" / "ARTICLE_QUALITY_CI.md").read_text(
            encoding="utf-8"
        )
        assert "editorial approval" in text.lower()

    def test_operations_doc_references_quality_ci(self):
        text = (REPO_ROOT / "docs" / "OPERATIONS.md").read_text(encoding="utf-8")
        assert "ARTICLE_QUALITY_CI" in text or "article quality" in text.lower()

    def test_contributing_references_quality_checks(self):
        text = (REPO_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        assert "readability" in text.lower()
