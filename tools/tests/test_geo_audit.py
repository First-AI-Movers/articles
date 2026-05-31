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

    def test_zero_h1_without_metadata_title_fails(self):
        """Zero Markdown H1 lines AND no metadata title => fail.

        Calling without `meta` is equivalent to passing `meta={}` — the
        previous (legacy) contract.
        """
        from geo_audit import _check_single_h1
        body = "## Section\n\nParagraph.\n"
        result = _check_single_h1(body)
        assert result["passed"] is False
        assert result["points"] == 0
        assert "metadata title missing" in result["detail"]

    def test_zero_h1_with_empty_metadata_title_fails(self):
        """Empty / whitespace-only metadata title is treated as missing."""
        from geo_audit import _check_single_h1
        body = "## Section\n\nParagraph.\n"
        for empty in ({}, {"title": ""}, {"title": "   "}, {"title": None}):
            result = _check_single_h1(body, empty)
            assert result["passed"] is False, (
                f"meta={empty!r} should not be enough to pass single_h1; "
                f"got: {result!r}"
            )
            assert result["points"] == 0

    def test_zero_h1_with_metadata_title_passes(self):
        """The renderer in templates/article.html.j2 emits
        ``<h1>{{ title }}</h1>`` from metadata.json::title, so an article
        with zero Markdown H1 lines but a non-empty metadata title still
        has exactly one rendered H1 and must pass the audit.
        """
        from geo_audit import _check_single_h1
        body = "## Section\n\nParagraph.\n"
        meta = {"title": "Claude Code Across Every Device"}
        result = _check_single_h1(body, meta)
        assert result["passed"] is True
        assert result["points"] == 20
        assert "metadata title renders H1" in result["detail"]

    def test_multiple_h1_with_metadata_title_still_fails(self):
        """Metadata title does NOT rescue a body with >1 Markdown H1 — the
        rendered page would emit the metadata `<h1>` PLUS the body H1s,
        breaking the single-H1 invariant.
        """
        from geo_audit import _check_single_h1
        body = "# Title One\n\n# Title Two\n"
        meta = {"title": "Whatever"}
        result = _check_single_h1(body, meta)
        assert result["passed"] is False
        assert result["points"] == 0
        assert "Markdown H1 count: 2" in result["detail"]

    def test_score_article_uses_metadata_title_path(self):
        """`_score_article` must propagate meta into `_check_single_h1` so
        an article with zero Markdown H1 but a complete metadata block
        gets credit for the rendered H1.
        """
        from geo_audit import _score_article
        # Body has TL;DR, outbound link, numeric signal, hierarchy — but
        # NO Markdown H1. Metadata has title (renderer emits the H1).
        body = (
            "> **TL;DR:** Summary.\n\n"
            "## Section\n\n### Subsection\n\n"
            "[Source](https://example.com)\n\n"
            "Growth was 42%.\n"
        )
        meta = {
            "title": "Renderer-Supplied Title",
            "published_date": "2026-01-01",
            "canonical_url": "https://example.com",
            "tags": ["AI"], "author": "A", "author_url": "https://a.com",
            "company": "C", "company_url": "https://c.com",
            "word_count": 100, "read_time_minutes": 2,
        }
        result = _score_article(Path("test"), body, meta)
        # single_h1 must contribute its full 20 points via the metadata path.
        assert result["checks"]["single_h1"]["passed"] is True
        assert result["checks"]["single_h1"]["points"] == 20
        assert "metadata title renders H1" in result["checks"]["single_h1"]["detail"]
        # Whole article still scores 100 (matches the legacy "perfect" test
        # but reaches it via the metadata-rendered H1 instead of a body H1).
        assert result["score"] == 100
        assert result["status"] == "pass"

    def test_detail_string_distinguishes_paths(self):
        """The detail string for each pass / fail branch is stable so the
        GEO report stays diagnostic and operators can tell which path the
        article took.
        """
        from geo_audit import _check_single_h1
        cases = [
            ("# Title\n\nBody.\n", {"title": "T"}, "Markdown H1 count: 1"),
            ("## Section\n\nBody.\n", {"title": "T"}, "Markdown H1 count: 0; metadata title renders H1"),
            ("## Section\n\nBody.\n", {}, "Markdown H1 count: 0; metadata title missing"),
            ("# A\n# B\n# C\n", {"title": "T"}, "Markdown H1 count: 3"),
        ]
        for body, meta, expected in cases:
            result = _check_single_h1(body, meta)
            assert result["detail"] == expected, (
                f"For body={body!r} meta={meta!r}: expected detail "
                f"{expected!r}, got {result['detail']!r}"
            )


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

    def test_missing_tldr_without_metadata_fails(self):
        """No body marker AND no metadata.summary_short = fail (legacy)."""
        from geo_audit import _check_tldr
        body = "# Title\n\nParagraph.\n"
        result = _check_tldr(body)
        assert result["passed"] is False
        assert result["points"] == 0
        assert "not found in body or metadata" in result["detail"]

    def test_body_marker_passes_with_detail_path(self):
        """Body-marker path must be reported in the detail string."""
        from geo_audit import _check_tldr
        body = "> **TL;DR:** Summary in body.\n\nBody.\n"
        result = _check_tldr(body, {"summary_short": "Also in metadata."})
        assert result["passed"] is True
        assert result["points"] == 20
        # Body marker wins; detail reports the body path even when metadata
        # is also populated.
        assert result["detail"] == "TL;DR found in body"

    def test_metadata_summary_short_passes_when_no_body_tldr(self):
        """The site renderer surfaces `summary_short` via JSON-LD
        `description`, `llms-index.txt`, and `llms-full.txt` per-article
        headers — so a reviewed `summary_short` is functionally a TL;DR
        for AI consumers, even when the article body lacks an inline
        marker. The audit must credit it.
        """
        from geo_audit import _check_tldr
        body = "## Section\n\nProse body without any TL;DR marker.\n"
        meta = {"summary_short": "A concise reviewed summary."}
        result = _check_tldr(body, meta)
        assert result["passed"] is True
        assert result["points"] == 20
        assert "metadata.summary_short" in result["detail"]

    def test_metadata_empty_string_fails(self):
        from geo_audit import _check_tldr
        body = "## Section\n\nProse only.\n"
        for empty in ({}, {"summary_short": ""}, {"summary_short": None},
                      {"summary_short": "   "}, {"summary_short": "\t\n"}):
            result = _check_tldr(body, empty)
            assert result["passed"] is False, (
                f"meta={empty!r} must not pass; got: {result!r}"
            )
            assert result["points"] == 0

    def test_meta_none_treated_as_no_metadata(self):
        """Explicit `meta=None` (default arg) is the same as no metadata."""
        from geo_audit import _check_tldr
        body = "## Section\n\nProse only.\n"
        result = _check_tldr(body, None)
        assert result["passed"] is False

    def test_score_article_uses_metadata_tldr_path(self):
        """`_score_article` must propagate `meta` into `_check_tldr` so an
        article without a body TL;DR but with a reviewed `summary_short`
        gets credit for the rendered TL;DR.
        """
        from geo_audit import _score_article
        # Body has H1 (via title), heading hierarchy, outbound link, numeric
        # signal — but NO body TL;DR marker. Metadata carries summary_short.
        body = (
            "## Section\n\n"
            "[Source](https://example.com)\n\n"
            "Growth was 42%.\n"
        )
        meta = {
            "title": "An Article",
            "published_date": "2026-01-01",
            "canonical_url": "https://example.com",
            "tags": ["AI"], "author": "A", "author_url": "https://a.com",
            "company": "C", "company_url": "https://c.com",
            "word_count": 100, "read_time_minutes": 2,
            "summary_short": "A concise reviewed summary.",
        }
        result = _score_article(Path("test"), body, meta)
        # The tldr check must contribute 20 points via the metadata path.
        assert result["checks"]["tldr"]["passed"] is True
        assert result["checks"]["tldr"]["points"] == 20
        assert "metadata.summary_short" in result["checks"]["tldr"]["detail"]

    def test_detail_string_distinguishes_paths(self):
        """The detail string is stable across body / metadata / missing
        paths so the GEO report remains diagnostic.
        """
        from geo_audit import _check_tldr
        cases = [
            ("> **TL;DR:** Body.\n", {"summary_short": "Meta."},
             "TL;DR found in body"),
            ("Plain body.\n", {"summary_short": "Meta."},
             "TL;DR via metadata.summary_short"),
            ("Plain body.\n", {},
             "TL;DR not found in body or metadata"),
            ("Plain body.\n", None,
             "TL;DR not found in body or metadata"),
        ]
        for body, meta, expected in cases:
            result = _check_tldr(body, meta)
            assert result["detail"] == expected, (
                f"For body={body!r} meta={meta!r}: expected "
                f"{expected!r}, got {result['detail']!r}"
            )


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
