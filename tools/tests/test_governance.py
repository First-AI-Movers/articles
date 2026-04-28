import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

try:
    import yaml
    HAS_YAML = True
except Exception:
    HAS_YAML = False


class TestLicenseSplit:
    def test_license_code_exists(self):
        assert (REPO_ROOT / "LICENSE-CODE").exists()

    def test_license_code_contains_apache(self):
        text = (REPO_ROOT / "LICENSE-CODE").read_text(encoding="utf-8")
        assert "Apache License" in text

    def test_readme_mentions_cc_by_for_content(self):
        text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        assert "CC BY 4.0" in text

    def test_readme_mentions_apache_for_code(self):
        text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        assert "Apache" in text or "Apache-2.0" in text or "LICENSE-CODE" in text

    def test_readme_has_code_license_badge(self):
        text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        assert "Code_License" in text or "LICENSE-CODE" in text


class TestCodeowners:
    def test_codeowners_exists(self):
        assert (REPO_ROOT / ".github" / "CODEOWNERS").exists()

    def test_codeowners_covers_required_paths(self):
        text = (REPO_ROOT / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
        required = [
            "/articles/",
            "/tools/",
            "/templates/",
            "/static/",
            "/.github/",
            "/tests-e2e/",
            "/package.json",
            "/package-lock.json",
        ]
        for path in required:
            assert path in text, f"CODEOWNERS missing {path}"


class TestIssueTemplates:
    def test_bug_template_exists(self):
        p = REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "bug.yml"
        assert p.exists()

    def test_content_correction_template_exists(self):
        p = REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "content-correction.yml"
        assert p.exists()

    def test_security_template_exists(self):
        p = REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "security.yml"
        assert p.exists()

    def test_config_yml_exists(self):
        p = REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml"
        assert p.exists()

    @pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
    def test_bug_template_parses_as_yaml(self):
        p = REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "bug.yml"
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        assert data.get("name")
        assert "bug" in data.get("labels", [])

    @pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
    def test_content_correction_template_parses_as_yaml(self):
        p = REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "content-correction.yml"
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        assert data.get("name")
        assert "content" in data.get("labels", [])

    @pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
    def test_security_template_parses_as_yaml(self):
        p = REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "security.yml"
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        assert data.get("name")
        assert "security" in data.get("labels", [])


class TestBranchProtectionDoc:
    def test_branch_protection_doc_exists(self):
        assert (REPO_ROOT / "docs" / "BRANCH_PROTECTION.md").exists()

    def test_branch_protection_doc_mentions_required_checks(self):
        text = (REPO_ROOT / "docs" / "BRANCH_PROTECTION.md").read_text(encoding="utf-8")
        assert "Require status checks" in text or "status checks" in text

    def test_branch_protection_doc_mentions_no_force_push(self):
        text = (REPO_ROOT / "docs" / "BRANCH_PROTECTION.md").read_text(encoding="utf-8")
        assert "force" in text.lower()


class TestExternalPublishingDoc:
    def test_external_publishing_doc_exists(self):
        assert (REPO_ROOT / "docs" / "EXTERNAL_PUBLISHING.md").exists()

    def test_external_publishing_doc_has_payload_schema(self):
        text = (REPO_ROOT / "docs" / "EXTERNAL_PUBLISHING.md").read_text(encoding="utf-8")
        assert "title" in text and "slug" in text and "canonical_url" in text

    def test_external_publishing_doc_has_security_notes(self):
        text = (REPO_ROOT / "docs" / "EXTERNAL_PUBLISHING.md").read_text(encoding="utf-8")
        assert "secret" in text.lower() or "security" in text.lower()
