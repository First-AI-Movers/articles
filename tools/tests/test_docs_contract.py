"""Contract tests for E16 documentation pipeline artifacts."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestDocsContract:
    def test_architecture_md_exists(self):
        assert (REPO_ROOT / "docs" / "ARCHITECTURE.md").exists()

    def test_operations_md_exists(self):
        assert (REPO_ROOT / "docs" / "OPERATIONS.md").exists()

    def test_changelog_md_exists(self):
        assert (REPO_ROOT / "docs" / "CHANGELOG.md").exists()

    def test_changelog_header_says_manual(self):
        text = (REPO_ROOT / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "reviewed snapshot generated manually" in text
        assert "not deployment-generated" in text

    def test_update_docs_py_exists(self):
        assert (REPO_ROOT / "tools" / "update_docs.py").exists()

    def test_build_changelog_py_exists(self):
        assert (REPO_ROOT / "tools" / "build_changelog.py").exists()

    def test_roadmap_has_operational_state_marker(self):
        text = (REPO_ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        assert "<!-- BEGIN auto:operational-state -->" in text
        assert "<!-- END auto:operational-state -->" in text

    def test_architecture_md_has_mermaid(self):
        text = (REPO_ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
        assert "```mermaid" in text

    def test_operations_md_has_runbooks(self):
        text = (REPO_ROOT / "docs" / "OPERATIONS.md").read_text(encoding="utf-8")
        assert "Adding an Article Manually" in text
        assert "Troubleshooting a Failed Build" in text
