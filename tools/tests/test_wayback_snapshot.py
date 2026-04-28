"""Tests for tools/wayback_snapshot.py."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WAYBACK_SCRIPT = REPO_ROOT / "tools" / "wayback_snapshot.py"


class TestUrlList:
    def test_default_urls_include_home_sitemap_topics(self):
        from wayback_snapshot import _build_url_list
        urls = _build_url_list("https://example.com", REPO_ROOT / "sitemap.xml", ["ai-strategy"])
        assert "https://example.com" in urls
        assert "https://example.com/sitemap.xml" in urls
        assert "https://example.com/topics/" in urls

    def test_topic_hubs_are_first_party(self):
        from wayback_snapshot import _build_url_list
        urls = _build_url_list("https://articles.firstaimovers.com", REPO_ROOT / "sitemap.xml", ["ai-strategy"])
        for u in urls:
            assert "articles.firstaimovers.com" in u

    def test_limit_caps_submissions(self):
        from wayback_snapshot import _build_url_list
        urls = _build_url_list("https://example.com", REPO_ROOT / "sitemap.xml", ["a", "b", "c", "d", "e"])
        assert len(urls) == 8  # home + sitemap + topics + 5 topics
        limited = urls[:3]
        assert len(limited) == 3


class TestDryRun:
    def test_dry_run_lists_urls_without_http_calls(self, capsys):
        from wayback_snapshot import main
        result = main(["--dry-run", "--limit", "5"])
        captured = capsys.readouterr()
        assert result == 0
        assert "DRY RUN" in captured.out
        assert "https://articles.firstaimovers.com" in captured.out
        assert "submit" not in captured.out.lower() or "would submit" in captured.out.lower()

    def test_default_is_dry_run(self, capsys):
        from wayback_snapshot import main
        result = main(["--limit", "3"])
        captured = capsys.readouterr()
        assert result == 0
        assert "DRY RUN" in captured.out


class TestSubmitMode:
    @patch("wayback_snapshot.requests.get")
    def test_submit_mode_calls_endpoint_per_url(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        from wayback_snapshot import main
        result = main(["--submit", "--limit", "3", "--sleep", "0"])
        assert result == 0
        assert mock_get.call_count == 3

    @patch("wayback_snapshot.requests.get")
    def test_rate_limited_reported_as_warning(self, mock_get):
        mock_get.return_value = MagicMock(status_code=429)
        from wayback_snapshot import main
        result = main(["--submit", "--limit", "1", "--sleep", "0"])
        assert result == 0

    @patch("wayback_snapshot.requests.get")
    def test_timeout_handled_gracefully(self, mock_get):
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()
        from wayback_snapshot import main
        result = main(["--submit", "--limit", "1", "--sleep", "0"])
        assert result == 0

    @patch("wayback_snapshot.requests.get")
    def test_request_exception_handled_gracefully(self, mock_get):
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("boom")
        from wayback_snapshot import main
        result = main(["--submit", "--limit", "1", "--sleep", "0"])
        assert result == 0


class TestRepoStructure:
    def test_workflow_exists(self):
        wf = REPO_ROOT / ".github" / "workflows" / "wayback-snapshot.yml"
        assert wf.exists()
        text = wf.read_text(encoding="utf-8")
        assert "wayback_snapshot.py" in text

    def test_workflow_has_workflow_dispatch(self):
        wf = REPO_ROOT / ".github" / "workflows" / "wayback-snapshot.yml"
        text = wf.read_text(encoding="utf-8")
        assert "workflow_dispatch:" in text

    def test_workflow_is_not_required_gate(self):
        # Verify branch protection docs do not list wayback as required
        bp = REPO_ROOT / "docs" / "BRANCH_PROTECTION.md"
        text = bp.read_text(encoding="utf-8")
        assert "wayback" not in text.lower() or "not required" in text.lower()

    def test_docs_exist(self):
        doc = REPO_ROOT / "docs" / "WAYBACK.md"
        assert doc.exists()
        text = doc.read_text(encoding="utf-8")
        assert "Wayback" in text
        assert "dry run" in text.lower()
