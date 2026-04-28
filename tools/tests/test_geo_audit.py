"""Tests for tools/geo_audit.py."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GEO_AUDIT = REPO_ROOT / "tools" / "geo_audit.py"


class TestCheckSingleH1:
    def test_single_h1_passes(self):
        from geo_audit import _check_single_h1
        body = "# Title\n\nParagraph.\n\n## Section\n"
        result = _check_single_h1(body)
        assert result["passed"] is True
        assert result["points"] == 20

    def test_multiple_h1_fails(self):
        from geo_audit import _check_single_h1
        body = "# Title\n\n# Another Title\n"
        result = _check_single_h1(body)
        assert result["passed"] is False
        assert result["points"] == 0
        assert "2" in result["detail"]

    def test_zero_h1_fails(self):
        from geo_audit import _check_single_h1
        body = "## Section\n\nParagraph.\n"
        result = _check_single_h1(body)
        assert result["passed"] is False
        assert result["points"] == 0


class TestCheckHeadingHierarchy:
    def test_valid_hierarchy_passes(self):
        from geo_audit import _check_heading_hierarchy
        body = "# Title\n\n## Section\n\n### Subsection\n\n## Section 2\n"
        result = _check_heading_hierarchy(body)
        assert result["passed"] is True
        assert result["points"] == 20

    def test_jump_detected(self):
        from geo_audit import _check_heading_hierarchy
        body = "# Title\n\n## Section\n\n#### Deep jump\n"
        result = _check_heading_hierarchy(body)
        assert result["passed"] is False
        assert result["points"] == 0
        assert "jump" in result["detail"].lower()

    def test_no_headings_partial_credit(self):
        from geo_audit import _check_heading_hierarchy
        body = "Paragraph only.\n"
        result = _check_heading_hierarchy(body)
        assert result["passed"] is True
        assert result["points"] == 10


class TestCheckTldr:
    def test_blockquote_tldr_detected(self):
        from geo_audit import _check_tldr
        body = "> **TL;DR:** Summary here.\n\nParagraph.\n"
        result = _check_tldr(body)
        assert result["passed"] is True
        assert result["points"] == 20

    def test_heading_tldr_detected(self):
        from geo_audit import _check_tldr
        body = "## TL;DR\n\nSummary.\n"
        result = _check_tldr(body)
        assert result["passed"] is True

    def test_missing_tldr(self):
        from geo_audit import _check_tldr
        body = "# Title\n\nParagraph.\n"
        result = _check_tldr(body)
        assert result["passed"] is False
        assert result["points"] == 0


class TestCheckOutboundSource:
    def test_external_link_detected(self):
        from geo_audit import _check_outbound_source
        body = "[Example](https://example.com/path)\n"
        result = _check_outbound_source(body)
        assert result["passed"] is True
        assert result["points"] == 15

    def test_internal_link_does_not_count(self):
        from geo_audit import _check_outbound_source
        body = "[Radar](https://radar.firstaimovers.com/post)\n"
        result = _check_outbound_source(body)
        assert result["passed"] is False
        assert result["points"] == 0

    def test_mailto_excluded(self):
        from geo_audit import _check_outbound_source
        body = "[Email](mailto:test@example.com)\n"
        result = _check_outbound_source(body)
        assert result["passed"] is False


class TestCheckNumericSignal:
    def test_percentage_detected(self):
        from geo_audit import _check_numeric_signal
        body = "Growth was 42% this year.\n"
        result = _check_numeric_signal(body)
        assert result["passed"] is True
        assert result["points"] == 15

    def test_monetary_detected(self):
        from geo_audit import _check_numeric_signal
        body = "Raised $1.2M in funding.\n"
        result = _check_numeric_signal(body)
        assert result["passed"] is True

    def test_scale_detected(self):
        from geo_audit import _check_numeric_signal
        body = "10 million users.\n"
        result = _check_numeric_signal(body)
        assert result["passed"] is True

    def test_no_numeric_signal(self):
        from geo_audit import _check_numeric_signal
        body = "This is just text without numbers.\n"
        result = _check_numeric_signal(body)
        assert result["passed"] is False
        assert result["points"] == 0


class TestCheckMetadata:
    def test_complete_metadata_passes(self):
        from geo_audit import _check_metadata
        meta = {
            "title": "T",
            "published_date": "2026-01-01",
            "canonical_url": "https://example.com",
            "tags": ["AI"],
            "author": "A",
            "author_url": "https://a.com",
            "company": "C",
            "company_url": "https://c.com",
            "word_count": 100,
            "read_time_minutes": 2,
        }
        result = _check_metadata(meta)
        assert result["passed"] is True
        assert result["points"] == 10

    def test_missing_required_metadata_fails(self):
        from geo_audit import _check_metadata
        meta = {"title": "T"}
        result = _check_metadata(meta)
        assert result["passed"] is False
        assert result["points"] < 10


class TestScoreArticle:
    def test_perfect_article_scores_100(self):
        from geo_audit import _score_article
        body = "# Title\n\n> **TL;DR:** Summary.\n\n## Section\n\n### Subsection\n\n[Source](https://example.com)\n\nGrowth was 42%.\n"
        meta = {
            "title": "T", "published_date": "2026-01-01",
            "canonical_url": "https://example.com",
            "tags": ["AI"], "author": "A", "author_url": "https://a.com",
            "company": "C", "company_url": "https://c.com",
            "word_count": 100, "read_time_minutes": 2,
        }
        result = _score_article(Path("test"), body, meta)
        assert result["score"] == 100
        assert result["status"] == "pass"

    def test_weak_article_scores_low(self):
        from geo_audit import _check_single_h1, _check_heading_hierarchy, _check_tldr, _check_outbound_source, _check_numeric_signal, _check_metadata
        # Stub out checks to simulate weak article
        body = "Paragraph only.\n"
        meta = {"title": "T", "published_date": "2026-01-01", "canonical_url": "https://example.com"}
        result = {
            "single_h1": _check_single_h1(body),
            "heading_hierarchy": _check_heading_hierarchy(body),
            "tldr": _check_tldr(body),
            "outbound_source": _check_outbound_source(body),
            "numeric_signal": _check_numeric_signal(body),
            "metadata": _check_metadata(meta),
        }
        total = sum(c["points"] for c in result.values())
        assert total < 60


class TestReports:
    def test_json_report_shape(self, tmp_path):
        from geo_audit import _build_json_report
        results = [
            {"score": 85, "status": "pass", "checks": {}, "title": "Good Article"},
            {"score": 55, "status": "fail", "checks": {}, "title": "Weak Article"},
        ]
        report = _build_json_report(results, 70)
        assert "generated_at" in report
        assert report["article_count"] == 2
        assert report["average_score"] == 70.0
        assert report["min_score"] == 55
        assert report["max_score"] == 85
        assert report["summary"]["pass_count"] == 1
        assert report["summary"]["fail_count"] == 1
        assert "criteria" in report
        assert "articles" in report

    def test_markdown_report_contains_summary(self):
        from geo_audit import _build_json_report, _build_md_report
        results = [
            {"score": 85, "status": "pass", "checks": {}, "title": "Good Article"},
            {"score": 55, "status": "fail", "checks": {}, "title": "Weak Article"},
        ]
        report = _build_json_report(results, 70)
        md = _build_md_report(report)
        assert "GEO Audit Report" in md
        assert "Average score" in md
        assert "Weakest Articles" in md
        assert "diagnostic" in md


class TestCLI:
    def test_default_exit_zero_even_with_low_scores(self, tmp_path):
        # Create a minimal articles dir with one weak article
        articles_dir = tmp_path / "articles"
        article_dir = articles_dir / "2026-01-01-test"
        article_dir.mkdir(parents=True)
        article_dir.joinpath("article.md").write_text("Paragraph.\n", encoding="utf-8")
        article_dir.joinpath("metadata.json").write_text(
            json.dumps({"title": "T", "published_date": "2026-01-01", "canonical_url": "https://example.com"}),
            encoding="utf-8",
        )
        json_out = tmp_path / "report.json"
        md_out = tmp_path / "report.md"
        result = subprocess.run(
            [sys.executable, str(GEO_AUDIT), "--articles-dir", str(articles_dir),
             "--json-out", str(json_out), "--md-out", str(md_out)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert json_out.exists()
        assert md_out.exists()

    def test_fail_below_threshold_exits_nonzero(self, tmp_path):
        articles_dir = tmp_path / "articles"
        article_dir = articles_dir / "2026-01-01-test"
        article_dir.mkdir(parents=True)
        article_dir.joinpath("article.md").write_text("Paragraph.\n", encoding="utf-8")
        article_dir.joinpath("metadata.json").write_text(
            json.dumps({"title": "T", "published_date": "2026-01-01", "canonical_url": "https://example.com"}),
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(GEO_AUDIT), "--articles-dir", str(articles_dir),
             "--json-out", str(tmp_path / "r.json"), "--md-out", str(tmp_path / "r.md"),
             "--min-score", "70", "--fail-below-threshold"],
            capture_output=True, text=True,
        )
        assert result.returncode == 1

    def test_audit_does_not_modify_articles(self, tmp_path):
        articles_dir = tmp_path / "articles"
        article_dir = articles_dir / "2026-01-01-test"
        article_dir.mkdir(parents=True)
        article_dir.joinpath("article.md").write_text("# Title\n\nBody.\n", encoding="utf-8")
        article_dir.joinpath("metadata.json").write_text(
            json.dumps({"title": "T", "published_date": "2026-01-01", "canonical_url": "https://example.com"}),
            encoding="utf-8",
        )
        before = article_dir.joinpath("article.md").read_text(encoding="utf-8")
        subprocess.run(
            [sys.executable, str(GEO_AUDIT), "--articles-dir", str(articles_dir),
             "--json-out", str(tmp_path / "r.json"), "--md-out", str(tmp_path / "r.md")],
            capture_output=True, text=True, check=True,
        )
        after = article_dir.joinpath("article.md").read_text(encoding="utf-8")
        assert before == after


class TestRepoStructure:
    def test_geo_workflow_exists_and_is_soft_gate(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "geo-audit.yml"
        assert workflow.exists()
        text = workflow.read_text(encoding="utf-8")
        assert "geo_audit.py" in text
        # Soft gate: should not have continue-on-error: false in a blocking way
        # Just verify it runs the script

    def test_geo_docs_exist(self):
        doc = REPO_ROOT / "docs" / "GEO_AUDIT.md"
        assert doc.exists()
        text = doc.read_text(encoding="utf-8")
        assert "GEO" in text
        assert "score" in text.lower()
