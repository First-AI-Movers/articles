#!/usr/bin/env python3
"""Tests for tools/summary_quality.py — the deterministic quality gate."""

from __future__ import annotations

import pytest

# tools/ is on sys.path via tools/tests/conftest.py.
import summary_quality as sq


# Helper to build a clean candidate that clears the gate by default.
def _ok_candidate() -> dict:
    return {
        "summary_short": "word " * 50,        # 50 words — in band
        "summary_medium": "word " * 200,      # 200 words — in band
        "summary_long": "word " * 500,        # 500 words — in band
    }


class TestGatePass:
    def test_clean_candidate_passes(self) -> None:
        result = sq.check_summaries(_ok_candidate())
        assert result.status is sq.GateStatus.PASS
        assert result.issues == []
        assert result.undersize_fields == []
        assert result.oversize_fields == []
        # word_counts populated even on PASS
        assert result.word_counts == {"short": 50, "medium": 200, "long": 500}

    def test_internal_form_keys_also_pass(self) -> None:
        """Provider returns short/medium/long; gate must accept that shape too."""
        result = sq.check_summaries({
            "short": "word " * 50,
            "medium": "word " * 200,
            "long": "word " * 500,
        })
        assert result.status is sq.GateStatus.PASS


class TestRejectShape:
    def test_not_a_dict_is_reject(self) -> None:
        result = sq.check_summaries("not a dict")
        assert result.status is sq.GateStatus.REJECT
        assert any("not a JSON object" in i for i in result.issues)

    def test_missing_required_field_is_reject(self) -> None:
        result = sq.check_summaries({"summary_short": "word " * 50})
        assert result.status is sq.GateStatus.REJECT
        # Both medium and long are missing.
        assert any("missing or empty" in i for i in result.issues)

    def test_empty_string_field_is_reject(self) -> None:
        cand = _ok_candidate()
        cand["summary_medium"] = "   "  # whitespace-only is treated as empty
        result = sq.check_summaries(cand)
        assert result.status is sq.GateStatus.REJECT
        assert any("missing or empty" in i for i in result.issues)


class TestRetryable:
    def test_under_min_short_only_is_retryable(self) -> None:
        cand = _ok_candidate()
        cand["summary_short"] = "word " * 30  # below 40
        result = sq.check_summaries(cand)
        assert result.status is sq.GateStatus.RETRYABLE
        assert result.undersize_fields == ["summary_short"]
        assert result.oversize_fields == []
        assert any("BELOW minimum 40" in i for i in result.issues)

    def test_multiple_underminimum_fields_is_retryable(self) -> None:
        cand = _ok_candidate()
        cand["summary_medium"] = "word " * 100  # below 170
        cand["summary_long"] = "word " * 300    # below 430
        result = sq.check_summaries(cand)
        assert result.status is sq.GateStatus.RETRYABLE
        assert set(result.undersize_fields) == {"summary_medium", "summary_long"}

    def test_mix_of_undersize_and_overissue_is_human_review(self) -> None:
        """When pattern issues mix with undersize, retry loop cannot fix safely."""
        cand = _ok_candidate()
        cand["summary_short"] = "word " * 30
        cand["summary_medium"] = (
            "Frequently Asked Questions: this is a fabricated heading. "
            + ("word " * 195)
        )  # under-min was not the only problem
        result = sq.check_summaries(cand)
        assert result.status is sq.GateStatus.HUMAN_REVIEW


class TestOverMax:
    def test_over_max_is_human_review_not_retryable(self) -> None:
        cand = _ok_candidate()
        cand["summary_short"] = "word " * 80  # above 60
        result = sq.check_summaries(cand)
        assert result.status is sq.GateStatus.HUMAN_REVIEW
        assert result.oversize_fields == ["summary_short"]
        assert any("ABOVE maximum 60" in i for i in result.issues)


class TestOrphanCitationIDs:
    def test_orphan_S_token_detected_when_absent_from_source(self) -> None:
        cand = _ok_candidate()
        cand["summary_short"] = ("word " * 49) + " citation S1"
        result = sq.check_summaries(cand, source_body="article text without that marker")
        assert result.status is sq.GateStatus.HUMAN_REVIEW
        assert any("orphan citation" in i for i in result.issues)

    def test_orphan_R_token_detected(self) -> None:
        cand = _ok_candidate()
        cand["summary_medium"] = ("word " * 199) + " R5"
        result = sq.check_summaries(cand, source_body="article text")
        assert result.status is sq.GateStatus.HUMAN_REVIEW

    def test_numeric_footnote_detected(self) -> None:
        cand = _ok_candidate()
        cand["summary_long"] = ("word " * 499) + " [1]"
        result = sq.check_summaries(cand, source_body="article text without brackets")
        assert result.status is sq.GateStatus.HUMAN_REVIEW

    def test_citation_token_present_in_source_does_not_flag(self) -> None:
        cand = _ok_candidate()
        cand["summary_short"] = ("word " * 49) + " citation S1"
        result = sq.check_summaries(
            cand,
            source_body="Earlier work shows S1 demonstrates the same property.",
        )
        # Source contains the same marker → not flagged → status stays PASS.
        assert result.status is sq.GateStatus.PASS


class TestFabricatedHeadings:
    def test_faq_in_summary_absent_from_source_is_flagged(self) -> None:
        cand = _ok_candidate()
        cand["summary_long"] = ("word " * 480) + " Frequently Asked Questions: invented"
        result = sq.check_summaries(cand, source_body="article without that heading")
        assert result.status is sq.GateStatus.HUMAN_REVIEW
        assert any("fabricated heading" in i for i in result.issues)

    def test_pilot_plan_heading_flagged(self) -> None:
        cand = _ok_candidate()
        cand["summary_medium"] = ("word " * 190) + " Pilot Plan: 30 days"
        result = sq.check_summaries(cand, source_body="article without that heading")
        assert result.status is sq.GateStatus.HUMAN_REVIEW

    def test_faq_in_source_does_not_flag(self) -> None:
        cand = _ok_candidate()
        cand["summary_long"] = ("word " * 480) + " Frequently Asked Questions: legitimate"
        # Source already mentions the heading → preservation, not fabrication.
        result = sq.check_summaries(
            cand,
            source_body="The article ends with a Frequently Asked Questions section.",
        )
        assert result.status is sq.GateStatus.PASS


class TestMarkdownLeakage:
    def test_markdown_heading_inside_summary_is_human_review(self) -> None:
        cand = _ok_candidate()
        cand["summary_medium"] = "## Inline heading\n" + ("word " * 200)
        result = sq.check_summaries(cand)
        assert result.status is sq.GateStatus.HUMAN_REVIEW
        assert any("markdown heading" in i for i in result.issues)

    def test_markdown_bullet_inside_summary_is_human_review(self) -> None:
        cand = _ok_candidate()
        cand["summary_long"] = "- bullet\n" + ("word " * 500)
        result = sq.check_summaries(cand)
        assert result.status is sq.GateStatus.HUMAN_REVIEW


class TestCountWords:
    def test_basic_split_count(self) -> None:
        assert sq.count_words("one two three") == 3
        assert sq.count_words("") == 0

    def test_non_string_input_returns_zero(self) -> None:
        assert sq.count_words(None) == 0  # type: ignore[arg-type]
