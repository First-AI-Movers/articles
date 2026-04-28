"""Tests for E23 Zenodo DOI + Citation File Format release pipeline."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CITATION_CFF = REPO_ROOT / "CITATION.cff"
CHECK_CITATION = REPO_ROOT / "tools" / "check_citation.py"


class TestCitationCff:
    def test_citation_cff_exists(self):
        assert CITATION_CFF.exists()

    def test_citation_cff_has_required_fields(self):
        text = CITATION_CFF.read_text(encoding="utf-8")
        required = ["cff-version", "message", "title", "authors", "license"]
        for field in required:
            assert field in text, f"Missing required field: {field}"

    def test_citation_cff_has_type(self):
        text = CITATION_CFF.read_text(encoding="utf-8")
        assert "type:" in text

    def test_citation_cff_has_repository_code(self):
        text = CITATION_CFF.read_text(encoding="utf-8")
        assert "repository-code" in text

    def test_citation_cff_does_not_contain_fake_doi(self):
        text = CITATION_CFF.read_text(encoding="utf-8")
        lines = text.splitlines()
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            lower = stripped.lower()
            if "doi" in lower:
                assert "xxxxxxx" not in lower, f"Line {i}: DOI contains placeholder XXXXXXX"
                assert "placeholder" not in lower, f"Line {i}: DOI contains placeholder"
                assert "pending" not in lower, f"Line {i}: DOI contains pending"

    def test_citation_cff_author_has_orcid(self):
        text = CITATION_CFF.read_text(encoding="utf-8")
        assert "orcid" in text
        assert "0000-0002-6813-4641" in text

    def test_citation_cff_license_is_cc_by(self):
        text = CITATION_CFF.read_text(encoding="utf-8")
        assert "CC-BY-4.0" in text

    def test_citation_cff_no_apache_license_confusion(self):
        text = CITATION_CFF.read_text(encoding="utf-8")
        # The CITATION.cff should not claim Apache-2.0 for the content corpus
        for line in text.splitlines():
            if line.strip().startswith("#"):
                continue
            if "license:" in line:
                assert "Apache" not in line, "CITATION.cff license should be CC-BY-4.0, not Apache-2.0"


class TestCitationDocs:
    def test_citation_docs_exist(self):
        doc = REPO_ROOT / "docs" / "CITATION.md"
        assert doc.exists()
        text = doc.read_text(encoding="utf-8")
        assert "BibTeX" in text
        assert "APA" in text
        assert "CSL JSON" in text

    def test_citation_docs_include_bibtex_apa_csl(self):
        doc = REPO_ROOT / "docs" / "CITATION.md"
        text = doc.read_text(encoding="utf-8")
        assert "```bibtex" in text
        assert "```json" in text
        assert "APA" in text

    def test_citation_docs_mark_doi_pending(self):
        doc = REPO_ROOT / "docs" / "CITATION.md"
        text = doc.read_text(encoding="utf-8")
        assert "pending" in text.lower() or "DOI" in text

    def test_zenodo_release_docs_exist(self):
        doc = REPO_ROOT / "docs" / "ZENODO_RELEASE.md"
        assert doc.exists()
        text = doc.read_text(encoding="utf-8")
        assert "Zenodo" in text

    def test_zenodo_docs_warn_no_test_doi_on_production(self):
        doc = REPO_ROOT / "docs" / "ZENODO_RELEASE.md"
        text = doc.read_text(encoding="utf-8")
        assert "Sandbox" in text or "sandbox" in text.lower()
        assert "test" in text.lower()

    def test_zenodo_docs_has_release_checklist(self):
        doc = REPO_ROOT / "docs" / "ZENODO_RELEASE.md"
        text = doc.read_text(encoding="utf-8")
        assert "checklist" in text.lower() or "- [ ]" in text


class TestReadmeCitation:
    def test_readme_citation_section_is_truthful(self):
        readme = REPO_ROOT / "README.md"
        text = readme.read_text(encoding="utf-8")
        assert "## Citation" in text
        # Must not claim a DOI already exists
        assert "10.5281" not in text or "XXXXXXX" in text

    def test_readme_links_to_citation_cff(self):
        readme = REPO_ROOT / "README.md"
        text = readme.read_text(encoding="utf-8")
        assert "CITATION.cff" in text

    def test_readme_links_to_citation_docs(self):
        readme = REPO_ROOT / "README.md"
        text = readme.read_text(encoding="utf-8")
        # Should reference docs/CITATION.md or mention citation docs
        assert "docs/CITATION.md" in text or "docs/CITATION" in text


class TestCheckCitationTool:
    def test_check_citation_tool_exists(self):
        assert CHECK_CITATION.exists()

    def test_check_citation_validates_good_fixture(self, tmp_path):
        good = tmp_path / "CITATION.cff"
        good.write_text(
            'cff-version: 1.2.0\n'
            'message: "Cite me"\n'
            'title: "Good Archive"\n'
            'authors:\n'
            '  - family-names: Costa\n'
            '    given-names: Hernani\n'
            'license: CC-BY-4.0\n',
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(CHECK_CITATION), str(good)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "OK" in result.stdout

    def test_check_citation_rejects_fake_doi_fixture(self, tmp_path):
        bad = tmp_path / "CITATION.cff"
        bad.write_text(
            'cff-version: 1.2.0\n'
            'message: "Cite me"\n'
            'title: "Bad Archive"\n'
            'authors:\n'
            '  - family-names: Costa\n'
            '    given-names: Hernani\n'
            'license: CC-BY-4.0\n'
            'doi: "10.5281/zenodo.XXXXXXX"\n',
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(CHECK_CITATION), str(bad)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "placeholder" in result.stdout.lower() or "fake" in result.stdout.lower() or "doi" in result.stdout.lower()

    def test_check_citation_reports_missing_required_fields(self, tmp_path):
        bad = tmp_path / "CITATION.cff"
        bad.write_text(
            'cff-version: 1.2.0\n'
            'title: "Incomplete"\n',
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(CHECK_CITATION), str(bad)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Missing required field" in result.stdout

    def test_check_citation_warns_on_apache_license(self, tmp_path):
        warn = tmp_path / "CITATION.cff"
        warn.write_text(
            'cff-version: 1.2.0\n'
            'message: "Cite me"\n'
            'title: "Code Archive"\n'
            'authors:\n'
            '  - family-names: Costa\n'
            '    given-names: Hernani\n'
            'license: Apache-2.0\n',
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(CHECK_CITATION), str(warn)],
            capture_output=True,
            text=True,
        )
        if "PyYAML not installed" in result.stdout:
            pytest.skip("PyYAML not available; structured validation skipped")
        # Should pass but with a warning
        assert result.returncode == 0
        assert "Apache" in result.stdout


class TestWorkflow:
    def test_release_citation_check_workflow_exists(self):
        wf = REPO_ROOT / ".github" / "workflows" / "release-citation-check.yml"
        assert wf.exists()
        text = wf.read_text(encoding="utf-8")
        assert "workflow_dispatch" in text
        assert "check_citation.py" in text or "citation" in text.lower()
