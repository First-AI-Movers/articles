"""Tests for tools/build_changelog.py."""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BUILD_CHANGELOG = REPO_ROOT / "tools" / "build_changelog.py"


class TestBuildChangelogInternal:
    def test_parse_conventional_commit_feat(self):
        from build_changelog import _parse_type
        assert _parse_type("feat(governance): add repo policy (#67)") == "feat"

    def test_parse_conventional_commit_docs(self):
        from build_changelog import _parse_type
        assert _parse_type("docs(roadmap): mark E18 done (#68)") == "docs"

    def test_parse_non_conventional_returns_none(self):
        from build_changelog import _parse_type
        assert _parse_type("Rebuild derived artifacts") is None
        assert _parse_type("Add article: 2026-04-23-foo") is None
        assert _parse_type("PR A: sitemap cleanup (#32)") is None

    def test_pr_link_format(self):
        from build_changelog import _pr_link
        assert _pr_link("https://github.com/First-AI-Movers/articles", 67) == "[67](https://github.com/First-AI-Movers/articles/pull/67)"

    def test_git_log_returns_bounded_entries(self):
        from build_changelog import _git_log
        entries = _git_log(10)
        assert len(entries) <= 10
        # All entries should have PR numbers
        for e in entries:
            assert isinstance(e["pr"], int)
            assert "sha" in e
            assert "subject" in e

    def test_render_groups_by_type(self):
        from build_changelog import _render
        entries = [
            {"sha": "a", "subject": "feat(gov): add policy", "pr": 1},
            {"sha": "b", "subject": "fix(bug): resolve issue", "pr": 2},
            {"sha": "c", "subject": "docs(readme): update", "pr": 3},
        ]
        output = _render(entries, "https://github.com/First-AI-Movers/articles")
        assert "## Features" in output
        assert "## Bug Fixes" in output
        assert "## Documentation" in output
        assert "feat(gov): add policy" in output
        assert "[1](https://github.com/First-AI-Movers/articles/pull/1)" in output

    def test_render_non_conventional_in_other(self):
        from build_changelog import _render
        entries = [
            {"sha": "a", "subject": "PR A: sitemap cleanup", "pr": 32},
        ]
        output = _render(entries, "https://github.com/First-AI-Movers/articles")
        assert "## Other Changes" in output
        assert "PR A: sitemap cleanup" in output

    def test_render_empty_entries(self):
        from build_changelog import _render
        output = _render([], "https://github.com/First-AI-Movers/articles")
        assert "# Changelog" in output
        assert "not deployment-generated" in output


class TestBuildChangelogCLI:
    def test_check_mode_exits_zero_when_unchanged(self):
        result = subprocess.run(
            [sys.executable, str(BUILD_CHANGELOG), "--check"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0
        assert "up to date" in result.stdout

    def test_default_writes_file(self):
        # File already exists from generation; verify script completes
        result = subprocess.run(
            [sys.executable, str(BUILD_CHANGELOG)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0
        assert "wrote" in result.stdout

    def test_max_entries_bounds_output(self):
        result = subprocess.run(
            [sys.executable, str(BUILD_CHANGELOG), "--max-entries", "5"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0
        # Count PR links in output to verify bounding
        output = (REPO_ROOT / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
        pr_links = output.count("/pull/")
        # After writing with --max-entries 5, the file should have at most 5 PR links
        assert pr_links <= 5

        # Restore with full generation
        subprocess.run(
            [sys.executable, str(BUILD_CHANGELOG)],
            capture_output=True,
            cwd=REPO_ROOT,
        )

    def test_check_mode_exits_one_when_file_missing(self, tmp_path, monkeypatch):
        import build_changelog
        monkeypatch.setattr(build_changelog, "CHANGELOG_PATH", tmp_path / "missing.md")
        assert build_changelog.main(["--check"]) == 1
