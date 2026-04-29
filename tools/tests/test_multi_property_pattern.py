#!/usr/bin/env python3
"""Tests for the multi-property archive pattern and cookiecutter template."""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PATTERN_DOC = REPO_ROOT / "docs" / "MULTI_PROPERTY_PATTERN.md"
TEMPLATE_DIR = REPO_ROOT / "cookiecutter-archive-template"
COOKIECUTTER_JSON = TEMPLATE_DIR / "cookiecutter.json"


class TestPatternDoc:
    def test_pattern_doc_exists(self):
        assert PATTERN_DOC.exists(), "docs/MULTI_PROPERTY_PATTERN.md should exist"

    def test_doc_states_no_merge_policy(self):
        text = PATTERN_DOC.read_text(encoding="utf-8")
        assert "Do not merge" in text or "do not merge" in text.lower()
        assert "separate archives" in text.lower() or "separate archive" in text.lower()

    def test_doc_mentions_topical_authority(self):
        text = PATTERN_DOC.read_text(encoding="utf-8")
        assert "topical authority" in text.lower()

    def test_doc_mentions_canonical_clarity(self):
        text = PATTERN_DOC.read_text(encoding="utf-8")
        assert "canonical" in text.lower()

    def test_doc_mentions_citation_license_clarity(self):
        text = PATTERN_DOC.read_text(encoding="utf-8")
        assert "citation" in text.lower() or "license" in text.lower()

    def test_doc_mentions_llm_ingestion(self):
        text = PATTERN_DOC.read_text(encoding="utf-8")
        assert "llm" in text.lower() or "ingestion" in text.lower()

    def test_doc_includes_fork_customize_checklist(self):
        text = PATTERN_DOC.read_text(encoding="utf-8")
        assert "checklist" in text.lower() or "fork-and-customize" in text.lower()

    def test_doc_includes_examples(self):
        text = PATTERN_DOC.read_text(encoding="utf-8")
        assert "example" in text.lower()

    def test_doc_warns_against_mixing_properties(self):
        text = PATTERN_DOC.read_text(encoding="utf-8")
        assert "do not mix" in text.lower() or "unrelated properties" in text.lower()


class TestCookiecutterTemplate:
    def test_cookiecutter_json_exists(self):
        assert COOKIECUTTER_JSON.exists(), "cookiecutter.json should exist"

    def test_cookiecutter_json_has_required_placeholders(self):
        data = json.loads(COOKIECUTTER_JSON.read_text(encoding="utf-8"))
        required = [
            "project_name",
            "repo_slug",
            "domain",
            "author_name",
            "publisher_name",
            "publisher_url",
            "content_license",
            "code_license",
        ]
        for key in required:
            assert key in data, f"cookiecutter.json missing key: {key}"

    def test_template_has_sample_article(self):
        sample_dir = TEMPLATE_DIR / "{{cookiecutter.repo_slug}}" / "articles" / "2026-01-01-sample-article"
        assert (sample_dir / "article.md").exists()
        assert (sample_dir / "metadata.json").exists()

    def test_template_has_license_split(self):
        root = TEMPLATE_DIR / "{{cookiecutter.repo_slug}}"
        assert (root / "LICENSE").exists()
        assert (root / "LICENSE-CODE").exists()

    def test_template_has_basic_templates(self):
        root = TEMPLATE_DIR / "{{cookiecutter.repo_slug}}" / "templates"
        assert (root / "base.html.j2").exists()
        assert (root / "home.html.j2").exists()
        assert (root / "article.html.j2").exists()
        assert (root / "topic.html.j2").exists()

    def test_template_has_static_assets(self):
        root = TEMPLATE_DIR / "{{cookiecutter.repo_slug}}" / "static"
        assert (root / "style.css").exists()
        assert (root / "search.js").exists()

    def test_template_has_build_tooling(self):
        root = TEMPLATE_DIR / "{{cookiecutter.repo_slug}}" / "tools"
        assert (root / "rebuild_local.py").exists()
        assert (root / "normalize_tags.py").exists()

    def test_template_has_ci_workflows(self):
        root = TEMPLATE_DIR / "{{cookiecutter.repo_slug}}" / ".github" / "workflows"
        assert (root / "tests.yml").exists()
        assert (root / "build-and-deploy.yml").exists()

    def test_template_has_docs(self):
        root = TEMPLATE_DIR / "{{cookiecutter.repo_slug}}" / "docs"
        assert (root / "ARCHITECTURE.md").exists()
        assert (root / "OPERATIONS.md").exists()

    def test_template_does_not_contain_production_articles(self):
        root = TEMPLATE_DIR / "{{cookiecutter.repo_slug}}" / "articles"
        folders = [p for p in root.iterdir() if p.is_dir()]
        # Only the sample article should exist
        assert len(folders) == 1, "Template should contain exactly one sample article"
        assert "sample" in folders[0].name.lower()

    def test_template_does_not_contain_secrets(self):
        """Ensure no API keys, tokens, or secrets are in template files."""
        root = TEMPLATE_DIR / "{{cookiecutter.repo_slug}}"
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix in (".pyc", ".parquet", ".png", ".jpg"):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            lower = text.lower()
            bad_patterns = [
                "sk-", "api_key", "apikey", "secret", "password",
                "cloudflare_api_token", "github_token", "doppler",
            ]
            for pat in bad_patterns:
                # Allow placeholder variables like {{cookiecutter...}}
                if pat in lower and "cookiecutter" not in lower:
                    pytest.fail(f"Possible secret pattern '{pat}' in {path}")
            # "token" is too broad (id-token, etc.); only flag explicit secret patterns
            if "token:" in lower or "token=" in lower:
                if "cookiecutter" not in lower and "id-token" not in lower:
                    pytest.fail(f"Possible secret pattern 'token' in {path}")

    def test_template_does_not_contain_heavy_artifacts(self):
        root = TEMPLATE_DIR / "{{cookiecutter.repo_slug}}"
        assert not (root / "embeddings.parquet").exists()
        assert not (root / "site").exists()
        assert not (root / "index.json").exists()

    def test_template_readme_warns_against_mixing(self):
        readme = TEMPLATE_DIR / "README.md"
        text = readme.read_text(encoding="utf-8")
        assert "do not mix" in text.lower() or "unrelated properties" in text.lower()

    def test_template_includes_placeholder_not_production_domain(self):
        sample = TEMPLATE_DIR / "{{cookiecutter.repo_slug}}" / "articles" / "2026-01-01-sample-article" / "metadata.json"
        text = sample.read_text(encoding="utf-8")
        assert "cookiecutter" in text or "example.com" in text or "{{" in text
        assert "firstaimovers.com" not in text
        assert "radar.firstaimovers.com" not in text


class TestDocsIntegration:
    def test_operations_links_to_pattern_doc(self):
        path = REPO_ROOT / "docs" / "OPERATIONS.md"
        text = path.read_text(encoding="utf-8")
        assert "MULTI_PROPERTY_PATTERN" in text or "multi-property" in text.lower()

    def test_contributing_mentions_property_scope(self):
        path = REPO_ROOT / "CONTRIBUTING.md"
        text = path.read_text(encoding="utf-8")
        assert "property scope" in text.lower() or "separate archive" in text.lower()
