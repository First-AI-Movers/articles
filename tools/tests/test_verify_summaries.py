#!/usr/bin/env python3
"""Tests for tools/verify_summaries.py — the dual-verifier review tool.

All tests are network-free. The verifier's HTTP transport is monkeypatched
through ``verify_summaries._http_post_json`` so no real outbound request is
ever made.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

# tools/ is on sys.path via tools/tests/conftest.py.
import verify_summaries as vs
from summary_quality import GateStatus


REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _ok_summaries(short_w: int = 50, medium_w: int = 200, long_w: int = 500) -> dict[str, str]:
    return {
        "summary_short": "alpha " * short_w,
        "summary_medium": "beta " * medium_w,
        "summary_long": "gamma " * long_w,
    }


def _stage_article(tmp_path: Path, folder: str = "2026-04-01-test") -> Path:
    """Create articles/<folder>/article.md and return its parent dir."""
    art_dir = tmp_path / "articles" / folder
    art_dir.mkdir(parents=True)
    (art_dir / "article.md").write_text(
        "---\ntitle: Test\n---\n# Test article\n\nBody text here.\n",
        encoding="utf-8",
    )
    return tmp_path / "articles"


def _stage_review(
    tmp_path: Path,
    slug: str,
    folder: str,
    summaries: dict[str, str],
    status: str = "draft",
    extra_tail: str = "",
) -> Path:
    """Write a draft review file under <tmp>/summaries/<slug>.review.md."""
    summaries_dir = tmp_path / "summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)
    path = summaries_dir / f"{slug}.review.md"
    lines = [
        f"# Summary Review — Test Title {slug}",
        "",
        f"Article folder: {folder}",
        f"Canonical URL: https://example.com/{slug}",
        "Generated at: 2026-06-01",
        "Model: minimax (MiniMax-M2)",
        "",
        "## 50-word summary",
        "",
        summaries["summary_short"].strip(),
        "",
        "## 200-word summary",
        "",
        summaries["summary_medium"].strip(),
        "",
        "## 500-word summary",
        "",
        summaries["summary_long"].strip(),
        "",
        "## Review status",
        "",
        f"Status: {status}",
        "Reviewer:",
        "Reviewed at:",
        "",
        "## Notes",
        "",
        "- (none)",
        "",
    ]
    if extra_tail:
        lines.append(extra_tail)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _openai_response_body(verdict: str = "AUTO_APPROVE", top_issue: str = "") -> str:
    """Construct an OpenAI chat completions envelope carrying a verifier verdict."""
    verdict_obj = {
        "verdict": verdict,
        "scores": {
            "faithfulness": 5,
            "durability": 5,
            "volatile_facts_handling": 5,
            "fabrication_check": 5,
            "voice_match": 5,
        },
        "top_issue": top_issue,
        "notes": ["no fabrications detected"],
    }
    return json.dumps({
        "id": "chatcmpl-test",
        "choices": [{
            "finish_reason": "stop",
            "index": 0,
            "message": {"role": "assistant", "content": json.dumps(verdict_obj)},
        }],
        "usage": {
            "prompt_tokens": 4000,
            "completion_tokens": 250,
        },
    })


def _anthropic_response_body(verdict: str = "AUTO_APPROVE") -> str:
    """Construct an Anthropic Messages envelope carrying a verifier verdict."""
    verdict_obj = {
        "verdict": verdict,
        "scores": {
            "faithfulness": 5, "durability": 5,
            "volatile_facts_handling": 5, "fabrication_check": 5,
            "voice_match": 5,
        },
        "top_issue": "",
        "notes": [],
    }
    return json.dumps({
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": json.dumps(verdict_obj)}],
        "usage": {"input_tokens": 4200, "output_tokens": 280},
    })


# ===========================================================================
# Review-file parsing
# ===========================================================================

class TestReviewFileParsing:
    def test_parses_summaries_correctly(self, tmp_path: Path) -> None:
        review = _stage_review(tmp_path, "demo", "2026-04-01-test", _ok_summaries())
        parsed = vs.parse_review_file(review)
        assert "alpha" in parsed.short
        assert "beta" in parsed.medium
        assert "gamma" in parsed.long
        assert parsed.article_folder == "2026-04-01-test"
        assert parsed.canonical_url == "https://example.com/demo"
        assert parsed.status == "draft"

    def test_loads_article_body_by_folder(self, tmp_path: Path) -> None:
        _stage_article(tmp_path, folder="2026-04-01-test")
        review = _stage_review(tmp_path, "demo", "2026-04-01-test", _ok_summaries())
        parsed = vs.parse_review_file(review)
        body = vs.load_article_body(tmp_path / "articles", parsed.article_folder)
        assert body.startswith("# Test article")
        # YAML frontmatter stripped.
        assert "title: Test" not in body

    def test_missing_article_body_returns_empty(self, tmp_path: Path) -> None:
        review = _stage_review(tmp_path, "demo", "missing-folder", _ok_summaries())
        parsed = vs.parse_review_file(review)
        assert vs.load_article_body(tmp_path / "articles", parsed.article_folder) == ""

    def test_discover_review_files_filters_by_slug(self, tmp_path: Path) -> None:
        _stage_review(tmp_path, "a", "f1", _ok_summaries())
        _stage_review(tmp_path, "b", "f2", _ok_summaries())
        all_files = vs.discover_review_files(tmp_path / "summaries")
        assert len(all_files) == 2
        b_only = vs.discover_review_files(tmp_path / "summaries", slug="b")
        assert len(b_only) == 1
        assert b_only[0].name == "b.review.md"


# ===========================================================================
# Network gating / safety
# ===========================================================================

class TestNetworkGating:
    def test_dry_run_makes_no_network_call(self, tmp_path: Path, monkeypatch) -> None:
        _stage_article(tmp_path)
        review = _stage_review(tmp_path, "demo", "2026-04-01-test", _ok_summaries())

        calls = {"n": 0}

        def trip_wire(*args, **kwargs):  # pragma: no cover - must not run
            calls["n"] += 1
            raise AssertionError("dry-run must not call network")

        monkeypatch.setattr(vs, "_http_post_json", trip_wire)
        rc = vs.main([
            "--review-file", str(review),
            "--articles-dir", str(tmp_path / "articles"),
        ])
        assert rc == 0
        assert calls["n"] == 0

    def test_live_verification_requires_allow_network(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        _stage_article(tmp_path)
        review = _stage_review(tmp_path, "demo", "2026-04-01-test", _ok_summaries())

        calls = {"n": 0}

        def trip_wire(*args, **kwargs):  # pragma: no cover - must not run
            calls["n"] += 1
            raise AssertionError("must not call network without --allow-network")

        monkeypatch.setattr(vs, "_http_post_json", trip_wire)
        # Without --allow-network, even if OPENAI_API_KEY is set the verifier
        # must not be invoked.
        monkeypatch.setenv("OPENAI_API_KEY", "fake-key")
        rc = vs.main([
            "--review-file", str(review),
            "--articles-dir", str(tmp_path / "articles"),
        ])
        assert rc == 0
        assert calls["n"] == 0

    def test_write_requires_write_verification_flag(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        _stage_article(tmp_path)
        review = _stage_review(tmp_path, "demo", "2026-04-01-test", _ok_summaries())
        original = review.read_text(encoding="utf-8")

        # Dry-run with no --write-verification: file unchanged.
        rc = vs.main([
            "--review-file", str(review),
            "--articles-dir", str(tmp_path / "articles"),
        ])
        assert rc == 0
        assert review.read_text(encoding="utf-8") == original

    def test_missing_openai_key_fails_safely_when_live_requested(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        _stage_article(tmp_path)
        review = _stage_review(tmp_path, "demo", "2026-04-01-test", _ok_summaries())
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        rc = vs.main([
            "--review-file", str(review),
            "--articles-dir", str(tmp_path / "articles"),
            "--allow-network",
            "--single-verifier",
        ])
        captured = capsys.readouterr()
        assert rc == 2
        assert "OPENAI_API_KEY" in captured.err
        # Never print value (no value to print, but assert defensively).
        assert "fake-key" not in captured.err
        assert "Bearer" not in captured.err

    def test_missing_anthropic_key_fails_safely_when_secondary_live(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        _stage_article(tmp_path)
        review = _stage_review(tmp_path, "demo", "2026-04-01-test", _ok_summaries())
        monkeypatch.setenv("OPENAI_API_KEY", "openai-fake")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        # Pre-flight emits WARN about the missing Anthropic key; primary
        # still runs successfully → exit 0 with the missing-key warning.
        def fake_post(url, headers, body, timeout):
            return 200, 10.0, _openai_response_body("AUTO_APPROVE")

        monkeypatch.setattr(vs, "_http_post_json", fake_post)
        rc = vs.main([
            "--review-file", str(review),
            "--articles-dir", str(tmp_path / "articles"),
            "--allow-network",
        ])
        captured = capsys.readouterr()
        assert rc == 0
        assert "ANTHROPIC_API_KEY" in captured.err


# ===========================================================================
# Request construction never prints secrets
# ===========================================================================

class TestNoSecretsPrinted:
    def test_openai_request_does_not_print_or_write_key(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        _stage_article(tmp_path)
        review = _stage_review(tmp_path, "demo", "2026-04-01-test", _ok_summaries())
        # Intentionally chosen NOT to look like a real key (no `sk-` prefix)
        # so local pre-commit secret scanners do not flag the fixture, while
        # still being a unique sentinel we can grep for to prove non-leakage.
        secret_value = "VERIFIER-FIXTURE-OPENAI-MUST-NOT-LEAK-12345"
        monkeypatch.setenv("OPENAI_API_KEY", secret_value)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "anth-fake")

        captured_calls: list[dict[str, Any]] = []

        def fake_post(url, headers, body, timeout):
            captured_calls.append({"url": url, "headers": dict(headers), "body": body})
            if "anthropic.com" in url:
                return 200, 10.0, _anthropic_response_body("AUTO_APPROVE")
            return 200, 10.0, _openai_response_body("AUTO_APPROVE")

        monkeypatch.setattr(vs, "_http_post_json", fake_post)
        rc = vs.main([
            "--review-file", str(review),
            "--articles-dir", str(tmp_path / "articles"),
            "--allow-network",
            "--write-verification",
        ])
        assert rc == 0

        # OpenAI Bearer header WAS constructed on the OpenAI call.
        openai_calls = [c for c in captured_calls if "openai.com" in c["url"]]
        assert openai_calls, "expected at least one OpenAI call"
        assert openai_calls[0]["headers"].get("Authorization", "").startswith("Bearer ")
        # The secret value must not appear in any request body or in stdout/stderr.
        for call in captured_calls:
            assert secret_value not in call["body"]
        out = capsys.readouterr()
        assert secret_value not in out.out
        assert secret_value not in out.err
        # And the secret must not appear in the review file.
        assert secret_value not in review.read_text(encoding="utf-8")

    def test_anthropic_request_does_not_print_or_write_key(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        _stage_article(tmp_path)
        review = _stage_review(tmp_path, "demo", "2026-04-01-test", _ok_summaries())
        secret_value = "VERIFIER-FIXTURE-ANTHROPIC-MUST-NOT-LEAK-67890"
        monkeypatch.setenv("OPENAI_API_KEY", "openai-fake")
        monkeypatch.setenv("ANTHROPIC_API_KEY", secret_value)

        captured: dict[str, Any] = {}

        def fake_post(url, headers, body, timeout):
            captured.setdefault("calls", []).append({"url": url, "headers": dict(headers), "body": body})
            if "anthropic.com" in url:
                return 200, 10.0, _anthropic_response_body("AUTO_APPROVE")
            return 200, 10.0, _openai_response_body("AUTO_APPROVE")

        monkeypatch.setattr(vs, "_http_post_json", fake_post)
        rc = vs.main([
            "--review-file", str(review),
            "--articles-dir", str(tmp_path / "articles"),
            "--allow-network",
            "--write-verification",
        ])
        assert rc == 0
        for call in captured["calls"]:
            assert secret_value not in call["body"]
        out = capsys.readouterr()
        assert secret_value not in out.out
        assert secret_value not in out.err
        assert secret_value not in review.read_text(encoding="utf-8")


# ===========================================================================
# Verifier JSON parser
# ===========================================================================

class TestVerifierJSONParser:
    def test_valid_response_parses(self) -> None:
        valid = {
            "verdict": "AUTO_APPROVE",
            "scores": {"faithfulness": 5},
            "top_issue": "",
            "notes": ["fine"],
        }
        ok, norm = vs.parse_verifier_response_json(valid)
        assert ok is True
        assert norm["verdict"] == "AUTO_APPROVE"
        assert norm["scores"]["faithfulness"] == 5
        assert norm["notes"] == ["fine"]

    def test_malformed_response_rejected(self) -> None:
        ok, norm = vs.parse_verifier_response_json({"not": "a verdict"})
        assert ok is False
        assert norm["verdict"] is None

    def test_unknown_verdict_value_rejected(self) -> None:
        ok, norm = vs.parse_verifier_response_json({"verdict": "MAYBE"})
        assert ok is False
        assert norm["verdict"] is None

    def test_none_input_rejected(self) -> None:
        ok, _ = vs.parse_verifier_response_json(None)
        assert ok is False

    def test_extract_strips_markdown_fence(self) -> None:
        wrapped = '```json\n{"verdict": "REJECT"}\n```'
        obj = vs._extract_json_object(wrapped)
        assert obj == {"verdict": "REJECT"}


# ===========================================================================
# Merge logic
# ===========================================================================

def _gate_pass() -> Any:
    return vs.check_summaries(_ok_summaries(), source_body="some body")


def _gate_undersize() -> Any:
    return vs.check_summaries(_ok_summaries(short_w=20))  # RETRYABLE


def _gate_reject() -> Any:
    return vs.check_summaries({"summary_short": ""})  # REJECT


def _ok_verifier_result(verdict: str, spec_key: str = "gpt-5.4-mini") -> vs.VerifierResult:
    return vs.VerifierResult(
        spec=vs.VERIFIERS[spec_key],
        ok=True,
        verdict=verdict,
        scores={"faithfulness": 5},
        top_issue="",
        notes=["ok"],
        cost_usd=0.001,
    )


class TestMergeLogic:
    def test_deterministic_reject_prevents_auto_approve(self) -> None:
        det = _gate_reject()
        primary = _ok_verifier_result("AUTO_APPROVE")
        secondary = _ok_verifier_result("AUTO_APPROVE", "claude-haiku-4-5-20251001")
        fv = vs.merge_final_verdict(
            det, primary, secondary,
            single_verifier=False, secondary_skipped_cost_cap=False,
        )
        assert fv.final == "REJECT"

    def test_deterministic_retryable_caps_at_human_review(self) -> None:
        det = _gate_undersize()
        primary = _ok_verifier_result("AUTO_APPROVE")
        secondary = _ok_verifier_result("AUTO_APPROVE", "claude-haiku-4-5-20251001")
        fv = vs.merge_final_verdict(
            det, primary, secondary,
            single_verifier=False, secondary_skipped_cost_cap=False,
        )
        assert fv.final == "HUMAN_REVIEW"

    def test_both_auto_approve_with_pass_gate_yields_auto_approve(self) -> None:
        det = _gate_pass()
        primary = _ok_verifier_result("AUTO_APPROVE")
        secondary = _ok_verifier_result("AUTO_APPROVE", "claude-haiku-4-5-20251001")
        fv = vs.merge_final_verdict(
            det, primary, secondary,
            single_verifier=False, secondary_skipped_cost_cap=False,
        )
        assert fv.final == "AUTO_APPROVE"

    def test_disagreement_yields_human_review(self) -> None:
        det = _gate_pass()
        primary = _ok_verifier_result("AUTO_APPROVE")
        secondary = _ok_verifier_result("HUMAN_REVIEW", "claude-haiku-4-5-20251001")
        fv = vs.merge_final_verdict(
            det, primary, secondary,
            single_verifier=False, secondary_skipped_cost_cap=False,
        )
        assert fv.final == "HUMAN_REVIEW"
        assert "disagreement" in fv.explanation.lower() or "human_review" in fv.explanation.lower()

    def test_any_reject_yields_reject(self) -> None:
        det = _gate_pass()
        primary = _ok_verifier_result("AUTO_APPROVE")
        secondary = _ok_verifier_result("REJECT", "claude-haiku-4-5-20251001")
        fv = vs.merge_final_verdict(
            det, primary, secondary,
            single_verifier=False, secondary_skipped_cost_cap=False,
        )
        assert fv.final == "REJECT"

    def test_single_verifier_auto_approve_with_opt_in(self) -> None:
        det = _gate_pass()
        primary = _ok_verifier_result("AUTO_APPROVE")
        fv = vs.merge_final_verdict(
            det, primary, None,
            single_verifier=True, secondary_skipped_cost_cap=False,
        )
        assert fv.final == "AUTO_APPROVE"
        assert fv.single_verifier is True

    def test_cost_cap_skip_downgrades_auto_approve(self) -> None:
        det = _gate_pass()
        primary = _ok_verifier_result("AUTO_APPROVE")
        fv = vs.merge_final_verdict(
            det, primary, None,
            single_verifier=False, secondary_skipped_cost_cap=True,
        )
        # Spec: "final cannot be stronger than HUMAN_REVIEW unless operator
        # explicitly runs --single-verifier."
        assert fv.final == "HUMAN_REVIEW"
        assert fv.secondary_skipped_cost_cap is True

    def test_cost_cap_skip_with_single_verifier_opt_in_preserves_auto_approve(self) -> None:
        det = _gate_pass()
        primary = _ok_verifier_result("AUTO_APPROVE")
        fv = vs.merge_final_verdict(
            det, primary, None,
            single_verifier=True, secondary_skipped_cost_cap=True,
        )
        assert fv.final == "AUTO_APPROVE"
        assert fv.single_verifier is True

    def test_no_verifier_ran_stays_human_review(self) -> None:
        det = _gate_pass()
        fv = vs.merge_final_verdict(
            det, None, None,
            single_verifier=False, secondary_skipped_cost_cap=False,
        )
        assert fv.final == "HUMAN_REVIEW"


# ===========================================================================
# Verification block writer
# ===========================================================================

class TestVerificationBlockWriter:
    def _live_run(self, tmp_path: Path, monkeypatch, primary_verdict: str = "AUTO_APPROVE"):
        _stage_article(tmp_path)
        review = _stage_review(tmp_path, "demo", "2026-04-01-test", _ok_summaries())
        monkeypatch.setenv("OPENAI_API_KEY", "openai-fake")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "anth-fake")

        def fake_post(url, headers, body, timeout):
            if "anthropic.com" in url:
                return 200, 10.0, _anthropic_response_body("AUTO_APPROVE")
            return 200, 10.0, _openai_response_body(primary_verdict)

        monkeypatch.setattr(vs, "_http_post_json", fake_post)
        return review

    def test_write_verification_appends_block(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        review = self._live_run(tmp_path, monkeypatch, "AUTO_APPROVE")
        rc = vs.main([
            "--review-file", str(review),
            "--articles-dir", str(tmp_path / "articles"),
            "--allow-network", "--write-verification",
        ])
        assert rc == 0
        text = review.read_text(encoding="utf-8")
        assert "## Verification" in text
        assert "Verification status: AUTO_APPROVE" in text
        assert "Primary verifier: openai/gpt-5.4-mini — AUTO_APPROVE" in text
        assert "Secondary verifier: anthropic/claude-haiku-4-5-20251001 — AUTO_APPROVE" in text
        assert "Single verifier: false" in text

    def test_write_verification_replaces_existing_block(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        review = self._live_run(tmp_path, monkeypatch, "AUTO_APPROVE")
        # First run.
        rc = vs.main([
            "--review-file", str(review),
            "--articles-dir", str(tmp_path / "articles"),
            "--allow-network", "--write-verification",
        ])
        assert rc == 0
        first = review.read_text(encoding="utf-8")
        first_headings = [
            ln for ln in first.splitlines() if ln.strip() == "## Verification"
        ]
        assert len(first_headings) == 1

        # Second run with a different verdict — block should be replaced,
        # not duplicated.
        def reject_post(url, headers, body, timeout):
            if "anthropic.com" in url:
                return 200, 10.0, _anthropic_response_body("REJECT")
            return 200, 10.0, _openai_response_body("REJECT")

        monkeypatch.setattr(vs, "_http_post_json", reject_post)
        rc = vs.main([
            "--review-file", str(review),
            "--articles-dir", str(tmp_path / "articles"),
            "--allow-network", "--write-verification",
        ])
        assert rc == 0
        second = review.read_text(encoding="utf-8")
        second_headings = [
            ln for ln in second.splitlines() if ln.strip() == "## Verification"
        ]
        assert len(second_headings) == 1
        assert "Verification status: REJECT" in second
        assert "Verification status: AUTO_APPROVE" not in second

    def test_status_draft_remains_unchanged(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        review = self._live_run(tmp_path, monkeypatch, "AUTO_APPROVE")
        rc = vs.main([
            "--review-file", str(review),
            "--articles-dir", str(tmp_path / "articles"),
            "--allow-network", "--write-verification",
        ])
        assert rc == 0
        text = review.read_text(encoding="utf-8")
        assert "Status: draft" in text
        # Tool must never promote draft → approved.
        assert "Status: approved" not in text


# ===========================================================================
# Filesystem safety: no metadata / no article body writes
# ===========================================================================

class TestFilesystemSafety:
    def test_no_metadata_file_is_modified(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        articles_dir = _stage_article(tmp_path)
        meta_path = articles_dir / "2026-04-01-test" / "metadata.json"
        meta_path.write_text(
            json.dumps({"folder": "2026-04-01-test", "title": "Test"}),
            encoding="utf-8",
        )
        meta_before = meta_path.read_text(encoding="utf-8")
        review = _stage_review(tmp_path, "demo", "2026-04-01-test", _ok_summaries())
        monkeypatch.setenv("OPENAI_API_KEY", "openai-fake")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "anth-fake")

        def fake_post(url, headers, body, timeout):
            if "anthropic.com" in url:
                return 200, 10.0, _anthropic_response_body("AUTO_APPROVE")
            return 200, 10.0, _openai_response_body("AUTO_APPROVE")

        monkeypatch.setattr(vs, "_http_post_json", fake_post)
        rc = vs.main([
            "--review-file", str(review),
            "--articles-dir", str(articles_dir),
            "--allow-network", "--write-verification",
        ])
        assert rc == 0
        assert meta_path.read_text(encoding="utf-8") == meta_before

    def test_no_article_body_is_modified(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        articles_dir = _stage_article(tmp_path)
        article_path = articles_dir / "2026-04-01-test" / "article.md"
        body_before = article_path.read_text(encoding="utf-8")
        review = _stage_review(tmp_path, "demo", "2026-04-01-test", _ok_summaries())
        monkeypatch.setenv("OPENAI_API_KEY", "openai-fake")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "anth-fake")

        def fake_post(url, headers, body, timeout):
            if "anthropic.com" in url:
                return 200, 10.0, _anthropic_response_body("AUTO_APPROVE")
            return 200, 10.0, _openai_response_body("AUTO_APPROVE")

        monkeypatch.setattr(vs, "_http_post_json", fake_post)
        rc = vs.main([
            "--review-file", str(review),
            "--articles-dir", str(articles_dir),
            "--allow-network", "--write-verification",
        ])
        assert rc == 0
        assert article_path.read_text(encoding="utf-8") == body_before


# ===========================================================================
# Cost-cap behavior
# ===========================================================================

class TestCostCap:
    def test_cost_cap_skips_secondary_and_downgrades(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Cost cap so tight only the primary fits → secondary skipped → HUMAN_REVIEW."""
        _stage_article(tmp_path)
        review = _stage_review(tmp_path, "demo", "2026-04-01-test", _ok_summaries())
        monkeypatch.setenv("OPENAI_API_KEY", "openai-fake")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "anth-fake")

        calls = {"openai": 0, "anthropic": 0}

        def fake_post(url, headers, body, timeout):
            if "anthropic.com" in url:
                calls["anthropic"] += 1
                return 200, 10.0, _anthropic_response_body("AUTO_APPROVE")
            calls["openai"] += 1
            return 200, 10.0, _openai_response_body("AUTO_APPROVE")

        monkeypatch.setattr(vs, "_http_post_json", fake_post)
        # The Anthropic Haiku verifier's per-call upper-bound estimate is
        # several thousand input tokens * $1.00/M plus 800 out * $5.00/M,
        # comfortably above $0.001. So setting the cap at $0.0008 allows the
        # cheap OpenAI primary through but blocks the Haiku secondary.
        rc = vs.main([
            "--review-file", str(review),
            "--articles-dir", str(tmp_path / "articles"),
            "--allow-network", "--write-verification",
            "--max-verifier-cost-usd", "0.0008",
        ])
        assert rc == 0
        assert calls["openai"] == 1
        assert calls["anthropic"] == 0, "secondary must be cost-capped"
        text = review.read_text(encoding="utf-8")
        assert "Verification status: HUMAN_REVIEW" in text
        assert "skipped (cost cap)" in text


# ===========================================================================
# Single-verifier flag
# ===========================================================================

class TestSingleVerifierFlag:
    def test_single_verifier_runs_only_primary_and_labels_block(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        _stage_article(tmp_path)
        review = _stage_review(tmp_path, "demo", "2026-04-01-test", _ok_summaries())
        monkeypatch.setenv("OPENAI_API_KEY", "openai-fake")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "anth-fake")

        calls = {"openai": 0, "anthropic": 0}

        def fake_post(url, headers, body, timeout):
            if "anthropic.com" in url:
                calls["anthropic"] += 1
                return 200, 10.0, _anthropic_response_body("AUTO_APPROVE")
            calls["openai"] += 1
            return 200, 10.0, _openai_response_body("AUTO_APPROVE")

        monkeypatch.setattr(vs, "_http_post_json", fake_post)
        rc = vs.main([
            "--review-file", str(review),
            "--articles-dir", str(tmp_path / "articles"),
            "--allow-network", "--write-verification",
            "--single-verifier",
        ])
        assert rc == 0
        assert calls["openai"] == 1
        assert calls["anthropic"] == 0
        text = review.read_text(encoding="utf-8")
        assert "Single verifier: true" in text
        assert "Verification status: AUTO_APPROVE" in text


# ===========================================================================
# Deterministic gate failure prevents AUTO_APPROVE end-to-end
# ===========================================================================

class TestGateFailurePreventsAutoApprove:
    def test_undersize_summary_blocks_auto_approve_in_main(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        _stage_article(tmp_path)
        # Medium summary deliberately undersize (only 30 words).
        bad = _ok_summaries(medium_w=30)
        review = _stage_review(tmp_path, "demo", "2026-04-01-test", bad)
        monkeypatch.setenv("OPENAI_API_KEY", "openai-fake")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "anth-fake")

        def fake_post(url, headers, body, timeout):
            # Both verifiers say AUTO_APPROVE — gate must still block.
            if "anthropic.com" in url:
                return 200, 10.0, _anthropic_response_body("AUTO_APPROVE")
            return 200, 10.0, _openai_response_body("AUTO_APPROVE")

        monkeypatch.setattr(vs, "_http_post_json", fake_post)
        rc = vs.main([
            "--review-file", str(review),
            "--articles-dir", str(tmp_path / "articles"),
            "--allow-network", "--write-verification",
        ])
        assert rc == 0
        text = review.read_text(encoding="utf-8")
        # Gate is RETRYABLE for this undersize-medium-only case.
        assert "Deterministic gate: RETRYABLE" in text
        assert "Verification status: HUMAN_REVIEW" in text
        assert "Verification status: AUTO_APPROVE" not in text
