"""Tests for tools/update_docs.py."""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
UPDATE_DOCS = REPO_ROOT / "tools" / "update_docs.py"


class TestComputeStats:
    def test_compute_stats_basic(self):
        from update_docs import compute_stats
        index = {
            "articles": [
                {"published_date": "2025-02-17", "tags": ["ai"], "topics": ["AI"], "funnel_stage": "top"},
                {"published_date": "2025-03-01", "tags": ["ml"], "topics": ["ML"], "funnel_stage": "middle"},
            ]
        }
        stats = compute_stats(index)
        assert stats["total"] == 2
        assert stats["tags_count"] == 2
        assert stats["topics_count"] == 2
        assert stats["date_min"] == "2025-02-17"
        assert stats["date_max"] == "2025-03-01"

    def test_compute_stats_empty(self):
        from update_docs import compute_stats
        stats = compute_stats({"articles": []})
        assert stats["total"] == 0
        assert stats["date_min"] == "unknown"


class TestPatchRoadmap:
    def test_marker_replace(self):
        from update_docs import _patch_roadmap, compute_stats
        content = (
            "Some header\n\n"
            "<!-- BEGIN auto:operational-state -->\n"
            "Old text.\n"
            "<!-- END auto:operational-state -->\n\n"
            "Some footer\n"
        )
        index = {
            "articles": [
                {"published_date": "2025-02-17", "tags": ["ai"], "topics": ["AI"], "funnel_stage": "top"},
            ] * 10
        }
        stats = compute_stats(index)
        new, status = _patch_roadmap(content, stats, index)
        assert status == "updated"
        assert "**10 articles**" in new
        assert "<!-- BEGIN auto:operational-state -->" in new
        assert "<!-- END auto:operational-state -->" in new
        assert "Old text." not in new

    def test_marker_idempotent(self):
        from update_docs import _patch_roadmap, compute_stats
        index = {
            "articles": [
                {"published_date": "2025-02-17", "tags": ["ai"], "topics": ["AI"], "funnel_stage": "top"},
            ] * 10
        }
        stats = compute_stats(index)
        content = (
            "<!-- BEGIN auto:operational-state -->\n"
            "Operational state today: **10 articles**, **1 canonical topics**, "
            "**1 rendered topic hubs**, **10 local noindex article pages**, "
            "sitemap limited to **4 first-party indexable URLs**, "
            "and the current test suite split across Python unit/integration tests plus Playwright E2E.\n"
            "<!-- END auto:operational-state -->\n"
        )
        new, status = _patch_roadmap(content, stats, index)
        assert status == "unchanged"
        assert new == content

    def test_missing_markers_skips(self):
        from update_docs import _patch_roadmap, compute_stats
        content = "No markers here.\n"
        index = {"articles": []}
        stats = compute_stats(index)
        new, status = _patch_roadmap(content, stats, index)
        assert status == "skipped (markers missing)"
        assert new == content


class TestPatchReadme:
    def test_updates_article_count(self):
        from update_docs import patch_readme
        content = (
            '"description": "The canonical, open-access article archive of First AI Movers: 100 original articles\n'
            "full-text, machine-readable versions of 100 original articles spanning January 2025–March 2025.\n"
            "**100** articles indexed\n"
            "**50** canonical topics\n"
        )
        stats = {"total": 200, "topics_count": 75, "date_min": "2025-01-01", "date_max": "2025-06-01", "funnel": {"top": 50, "middle": 100, "bottom": 50}}
        new = patch_readme(content, stats)
        assert "200 original articles" in new
        assert "**200** articles indexed" in new
        assert "**75** canonical topics" in new

    def test_idempotent(self):
        from update_docs import patch_readme
        stats = {"total": 200, "topics_count": 75, "date_min": "2025-01-01", "date_max": "2025-06-01", "funnel": {"top": 50, "middle": 100, "bottom": 50}}
        content = (
            '"description": "The canonical, open-access article archive of First AI Movers: 200 original articles\n'
            "full-text, machine-readable versions of 200 original articles spanning January 2025–June 2025.\n"
            "**200** articles indexed\n"
            "**75** canonical topics\n"
        )
        new = patch_readme(content, stats)
        assert new == content


class TestPatchLlms:
    def test_updates_count_and_span(self):
        from update_docs import patch_llms
        content = "100 original articles on AI strategy. Published January 2025–March 2025."
        stats = {"total": 200, "date_min": "2025-01-01", "date_max": "2025-06-01"}
        new = patch_llms(content, stats)
        assert "200 original articles on AI strategy" in new
        assert "Published January 2025–June 2025." in new

    def test_idempotent(self):
        from update_docs import patch_llms
        stats = {"total": 200, "date_min": "2025-01-01", "date_max": "2025-06-01"}
        content = "200 original articles on AI strategy. Published January 2025–June 2025."
        new = patch_llms(content, stats)
        assert new == content


class TestUpdateDocsCLI:
    def test_check_mode_exits_zero_when_unchanged(self):
        result = subprocess.run(
            [sys.executable, str(UPDATE_DOCS), "--check"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0
        assert "unchanged" in result.stdout or "skipped" in result.stdout

    def test_roadmap_only_flag(self):
        result = subprocess.run(
            [sys.executable, str(UPDATE_DOCS), "--roadmap-only", "--check"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0

    def test_readme_flag_patches_readme(self, tmp_path, monkeypatch):
        from update_docs import main
        readme = tmp_path / "README.md"
        readme.write_text(
            '"description": "The canonical, open-access article archive of First AI Movers: 100 original articles on AI strategy\n'
            "full-text, machine-readable versions of 100 original articles spanning January 2025–March 2025.\n"
            "**100** articles indexed\n"
            "**50** canonical topics\n",
            encoding="utf-8",
        )
        llms = tmp_path / "llms.txt"
        llms.write_text("Published January 2025–March 2025.", encoding="utf-8")
        index = tmp_path / "index.json"
        index.write_text(
            '{"articles": [{"published_date": "2025-01-01", "tags": ["ai"], "topics": ["AI"], "funnel_stage": "top"}]}',
            encoding="utf-8",
        )
        monkeypatch.setattr("update_docs.REPO_ROOT", tmp_path)
        ret = main(["--readme"])
        assert ret == 0
        text = readme.read_text(encoding="utf-8")
        assert "1 original articles on AI strategy" in text

    def test_llms_flag_patches_llms(self, tmp_path, monkeypatch):
        from update_docs import main
        readme = tmp_path / "README.md"
        readme.write_text("100 original articles on AI strategy.", encoding="utf-8")
        llms = tmp_path / "llms.txt"
        llms.write_text("Published January 2025–March 2025.", encoding="utf-8")
        index = tmp_path / "index.json"
        index.write_text(
            '{"articles": [{"published_date": "2025-01-01", "tags": ["ai"], "topics": ["AI"], "funnel_stage": "top"}]}',
            encoding="utf-8",
        )
        monkeypatch.setattr("update_docs.REPO_ROOT", tmp_path)
        ret = main(["--llms"])
        assert ret == 0
        text = llms.read_text(encoding="utf-8")
        assert "Published January 2025–January 2025." in text
