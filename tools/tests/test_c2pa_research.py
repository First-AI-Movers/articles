"""Governance tests for E32 C2PA research stub.

These tests enforce the research-only constraint: no signing, no manifests,
no cryptographic credentials, no dependencies, and no article/template changes.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestC2paResearchDocExists:
    def test_c2pa_research_md_exists(self):
        assert (REPO_ROOT / "docs" / "C2PA_RESEARCH.md").exists()

    def test_c2pa_research_md_has_research_stub_header(self):
        text = (REPO_ROOT / "docs" / "C2PA_RESEARCH.md").read_text(encoding="utf-8")
        assert "Research stub" in text or "research stub" in text.lower()

    def test_c2pa_research_md_cites_official_sources(self):
        text = (REPO_ROOT / "docs" / "C2PA_RESEARCH.md").read_text(encoding="utf-8")
        assert "spec.c2pa.org" in text
        assert "c2pa.org" in text
        assert "ai-act-service-desk.ec.europa.eu" in text or "artificialintelligenceact.eu" in text

    def test_c2pa_research_md_contains_gap_analysis(self):
        text = (REPO_ROOT / "docs" / "C2PA_RESEARCH.md").read_text(encoding="utf-8")
        assert "Gap Analysis" in text or "gap analysis" in text.lower()

    def test_c2pa_research_md_contains_decision_register(self):
        text = (REPO_ROOT / "docs" / "C2PA_RESEARCH.md").read_text(encoding="utf-8")
        assert "Decision Register" in text or "decision register" in text.lower()


class TestC2paAdrExists:
    def test_adr_001_exists(self):
        p = REPO_ROOT / "docs" / "decisions" / "adr-001-c2pa-content-credentials.md"
        assert p.exists()

    def test_adr_001_status_is_deferred(self):
        text = (REPO_ROOT / "docs" / "decisions" / "adr-001-c2pa-content-credentials.md").read_text(
            encoding="utf-8"
        )
        assert "Deferred" in text

    def test_adr_001_has_decision_section(self):
        text = (REPO_ROOT / "docs" / "decisions" / "adr-001-c2pa-content-credentials.md").read_text(
            encoding="utf-8"
        )
        assert "## Decision" in text

    def test_adr_001_has_consequences_section(self):
        text = (REPO_ROOT / "docs" / "decisions" / "adr-001-c2pa-content-credentials.md").read_text(
            encoding="utf-8"
        )
        assert "## Consequences" in text

    def test_adr_001_has_alternatives_section(self):
        text = (REPO_ROOT / "docs" / "decisions" / "adr-001-c2pa-content-credentials.md").read_text(
            encoding="utf-8"
        )
        assert "## Alternatives Considered" in text


class TestC2paNoImplementation:
    """Enforce the research-only constraint: no signing, no manifests, no deps."""

    def test_no_c2pa_dependency_in_requirements(self):
        req = REPO_ROOT / "tools" / "requirements.txt"
        if req.exists():
            text = req.read_text(encoding="utf-8").lower()
            assert "c2pa" not in text, "c2pa must not appear in requirements.txt"

    def test_no_c2pa_dependency_in_package_json(self):
        pkg = REPO_ROOT / "package.json"
        if pkg.exists():
            text = pkg.read_text(encoding="utf-8").lower()
            assert "c2pa" not in text, "c2pa must not appear in package.json"

    def test_no_c2pa_manifest_files_in_articles(self):
        """.c2pa sidecar files must not exist in the articles tree."""
        matches = list(REPO_ROOT.rglob("*.c2pa"))
        assert len(matches) == 0, f"Unexpected .c2pa files: {matches}"

    def test_no_c2pa_assertion_in_metadata_schema(self):
        """metadata.json schema must not contain c2pa-specific fields."""
        schema = REPO_ROOT / "tools" / "article_schema.json"
        if schema.exists():
            text = schema.read_text(encoding="utf-8").lower()
            assert "c2pa" not in text, "c2pa must not appear in article_schema.json"

    def test_no_c2pa_signing_in_rebuild_local(self):
        """rebuild_local.py must not invoke c2patool or C2PA SDK."""
        rebuild = REPO_ROOT / "tools" / "rebuild_local.py"
        if rebuild.exists():
            text = rebuild.read_text(encoding="utf-8").lower()
            assert "c2patool" not in text, "c2patool must not appear in rebuild_local.py"
            assert "c2pa" not in text, "c2pa must not appear in rebuild_local.py"

    def test_no_c2pa_signing_in_ci_workflows(self):
        """GitHub Actions workflows must not invoke c2patool or C2PA SDK."""
        workflows_dir = REPO_ROOT / ".github" / "workflows"
        if workflows_dir.exists():
            for wf in workflows_dir.glob("*.yml"):
                text = wf.read_text(encoding="utf-8").lower()
                assert "c2patool" not in text, f"c2patool must not appear in {wf.name}"
                assert "c2pa" not in text, f"c2pa must not appear in {wf.name}"

    def test_no_c2pa_template_changes(self):
        """Templates must not contain C2PA badges, verify links, or manifest markup."""
        templates_dir = REPO_ROOT / "templates"
        if templates_dir.exists():
            for tmpl in templates_dir.rglob("*.j2"):
                text = tmpl.read_text(encoding="utf-8").lower()
                assert "c2pa" not in text, f"c2pa must not appear in {tmpl.name}"
                assert "contentcredentials" not in text, (
                    f"contentcredentials must not appear in {tmpl.name}"
                )
                assert "content credentials" not in text, (
                    f"content credentials must not appear in {tmpl.name}"
                )
