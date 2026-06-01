#!/usr/bin/env python3
"""Tests for tools/run_summary_batch.py — the automated batch runner.

All tests are network-free. The MiniMax generator's HTTP transport and the
two verifier transports are monkeypatched in-process, so no real outbound
request ever leaves these tests.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

# tools/ is on sys.path via tools/tests/conftest.py.
import build_summaries as bs
import run_summary_batch as rsb
import verify_summaries as vs
from summary_quality import GateStatus


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _stage_repo(tmp_path: Path, articles: list[dict]) -> Path:
    """Create a fake repo layout under tmp_path with N articles.

    Returns the tmp_path itself (treated as REPO_ROOT for the batch runner).
    Each entry in ``articles`` is a dict with keys folder/slug/title and
    optional ``summary_short`` (set if the article is "already summarised").
    """
    (tmp_path / "articles").mkdir(exist_ok=True)
    (tmp_path / "summaries").mkdir(exist_ok=True)
    index_entries = []
    for a in articles:
        folder = a["folder"]
        slug = a["slug"]
        title = a.get("title", folder)
        canonical = a.get("canonical_url", f"https://example.com/{slug}")
        (tmp_path / "articles" / folder).mkdir(parents=True, exist_ok=True)
        (tmp_path / "articles" / folder / "article.md").write_text(
            "# " + title + "\n\nBody text for " + folder + ".\n",
            encoding="utf-8",
        )
        meta = {
            "folder": folder,
            "slug": slug,
            "title": title,
            "published_date": "2026-04-01",
            "canonical_url": canonical,
        }
        if a.get("summary_short"):
            meta["summary_short"] = a["summary_short"]
        (tmp_path / "articles" / folder / "metadata.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )
        index_entries.append({k: v for k, v in meta.items() if k != "published_date"})
    (tmp_path / "index.json").write_text(
        json.dumps({"articles": index_entries}), encoding="utf-8"
    )
    return tmp_path


def _wire_module_roots(monkeypatch, root: Path) -> None:
    """Point the runner + its delegates at the fake repo."""
    monkeypatch.setattr(rsb, "REPO_ROOT", root)
    monkeypatch.setattr(rsb, "ARTICLES_DIR", root / "articles")
    monkeypatch.setattr(rsb, "INDEX_PATH", root / "index.json")
    monkeypatch.setattr(rsb, "DEFAULT_SUMMARIES_DIR", root / "summaries")
    monkeypatch.setattr(bs, "REPO_ROOT", root)
    monkeypatch.setattr(bs, "ARTICLES_DIR", root / "articles")
    monkeypatch.setattr(bs, "INDEX_PATH", root / "index.json")
    monkeypatch.setattr(vs, "REPO_ROOT", root)
    monkeypatch.setattr(vs, "ARTICLES_DIR", root / "articles")
    monkeypatch.setattr(vs, "SUMMARIES_DIR", root / "summaries")


def _minimax_envelope(short_w=50, medium_w=200, long_w=500) -> str:
    summaries = {
        "summary_short": "alpha " * short_w,
        "summary_medium": "beta " * medium_w,
        "summary_long": "gamma " * long_w,
    }
    return json.dumps({
        "id": "test-id",
        "choices": [{
            "finish_reason": "stop",
            "index": 0,
            "message": {"role": "assistant", "content": json.dumps(summaries)},
        }],
        "usage": {"prompt_tokens": 4000, "completion_tokens": 1500},
    })


def _openai_verdict_envelope(verdict: str = "AUTO_APPROVE", top_issue: str = "") -> str:
    body = {
        "verdict": verdict,
        "scores": {"faithfulness": 5, "durability": 5,
                   "volatile_facts_handling": 5, "fabrication_check": 5,
                   "voice_match": 5},
        "top_issue": top_issue,
        "notes": ["fine"],
    }
    return json.dumps({
        "id": "chatcmpl-x",
        "choices": [{
            "index": 0,
            "finish_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps(body)},
        }],
        "usage": {"prompt_tokens": 4000, "completion_tokens": 250},
    })


def _anthropic_verdict_envelope(verdict: str = "AUTO_APPROVE") -> str:
    body = {
        "verdict": verdict,
        "scores": {"faithfulness": 5, "durability": 5,
                   "volatile_facts_handling": 5, "fabrication_check": 5,
                   "voice_match": 5},
        "top_issue": "",
        "notes": [],
    }
    return json.dumps({
        "id": "msg_x",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": json.dumps(body)}],
        "usage": {"input_tokens": 4200, "output_tokens": 280},
    })


def _wire_live_http(
    monkeypatch,
    *,
    primary_verdict: str = "AUTO_APPROVE",
    secondary_verdict: str = "AUTO_APPROVE",
    minimax_summaries_kwargs: dict | None = None,
    minimax_status: int = 200,
    minimax_body: str | None = None,
    track: dict | None = None,
) -> None:
    """Wire MiniMax + OpenAI + Anthropic HTTP shims to deterministic payloads."""
    mk = minimax_summaries_kwargs or {}

    def fake_minimax(url, headers, body, timeout):
        if track is not None:
            track.setdefault("minimax", []).append({
                "url": url, "headers": dict(headers), "body": body,
            })
        if minimax_body is not None:
            return minimax_status, 10.0, minimax_body
        return minimax_status, 10.0, _minimax_envelope(**mk)

    def fake_verifier(url, headers, body, timeout):
        if track is not None:
            track.setdefault("verifier", []).append({
                "url": url, "headers": dict(headers), "body": body,
            })
        if "anthropic.com" in url:
            return 200, 10.0, _anthropic_verdict_envelope(secondary_verdict)
        return 200, 10.0, _openai_verdict_envelope(primary_verdict)

    monkeypatch.setattr(bs, "_http_post_json", fake_minimax)
    monkeypatch.setattr(vs, "_http_post_json", fake_verifier)


def _set_keys(monkeypatch) -> None:
    monkeypatch.setenv("MINIMAX_API_KEY", "fake-minimax-key")
    monkeypatch.setenv("OPENAI_API_KEY", "fake-openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-anthropic-key")


# ===========================================================================
# Article selection + dry-run
# ===========================================================================

class TestSelectionAndDryRun:
    def test_select_missing_only_excludes_summarized(self, tmp_path):
        _stage_repo(tmp_path, [
            {"folder": "f1", "slug": "s1", "summary_short": "already"},
            {"folder": "f2", "slug": "s2"},
        ])
        sel = rsb.select_articles(
            tmp_path / "index.json",
            tmp_path / "articles",
            missing_only=True, slug=None, limit=10,
        )
        assert [a["folder"] for a in sel] == ["f2"]

    def test_select_respects_limit(self, tmp_path):
        _stage_repo(tmp_path, [
            {"folder": f"f{i}", "slug": f"s{i}"} for i in range(5)
        ])
        sel = rsb.select_articles(
            tmp_path / "index.json", tmp_path / "articles",
            missing_only=True, slug=None, limit=3,
        )
        assert len(sel) == 3

    def test_dry_run_default_makes_no_network_call(
        self, tmp_path, monkeypatch
    ):
        _stage_repo(tmp_path, [{"folder": "f1", "slug": "s1"}])
        _wire_module_roots(monkeypatch, tmp_path)

        def trip_wire(*a, **kw):  # pragma: no cover - must not run
            raise AssertionError("dry-run must not call network")

        monkeypatch.setattr(bs, "_http_post_json", trip_wire)
        monkeypatch.setattr(vs, "_http_post_json", trip_wire)

        report_dir = tmp_path / "reports"  # outside repo for the test? See note.
        # Use /tmp explicitly so resolve_report_path does not reject.
        report = Path("/tmp") / f"batch-test-dryrun-{tmp_path.name}.md"
        rc = rsb.main([
            "--limit", "3",
            "--articles-dir", str(tmp_path / "articles"),
            "--index-path", str(tmp_path / "index.json"),
            "--summaries-dir", str(tmp_path / "summaries"),
            "--report-path", str(report),
        ])
        assert rc == 0
        # No review files written.
        assert list((tmp_path / "summaries").glob("*.review.md")) == []
        # Report DOES exist (dry-run still writes a plan).
        assert report.exists()
        assert "Per-article results" in report.read_text(encoding="utf-8")

    def test_live_requires_all_three_gates(self, tmp_path, monkeypatch, capsys):
        """Without one of --batch/--allow-network/--max-budget-usd, no calls."""
        _stage_repo(tmp_path, [{"folder": "f1", "slug": "s1"}])
        _wire_module_roots(monkeypatch, tmp_path)
        _set_keys(monkeypatch)

        def trip_wire(*a, **kw):  # pragma: no cover
            raise AssertionError("missing gate must block network")

        monkeypatch.setattr(bs, "_http_post_json", trip_wire)
        monkeypatch.setattr(vs, "_http_post_json", trip_wire)

        report = Path("/tmp") / f"batch-test-no-gates-{tmp_path.name}.md"
        # Missing --batch
        rc = rsb.main([
            "--allow-network", "--max-budget-usd", "0.05",
            "--articles-dir", str(tmp_path / "articles"),
            "--index-path", str(tmp_path / "index.json"),
            "--summaries-dir", str(tmp_path / "summaries"),
            "--report-path", str(report),
        ])
        assert rc == 0  # dry-run path; no exception
        # Missing --allow-network
        rc = rsb.main([
            "--batch", "--max-budget-usd", "0.05",
            "--articles-dir", str(tmp_path / "articles"),
            "--index-path", str(tmp_path / "index.json"),
            "--summaries-dir", str(tmp_path / "summaries"),
            "--report-path", str(report),
        ])
        assert rc == 0
        # max-budget 0 still counts as no live mode
        rc = rsb.main([
            "--batch", "--allow-network", "--max-budget-usd", "0",
            "--articles-dir", str(tmp_path / "articles"),
            "--index-path", str(tmp_path / "index.json"),
            "--summaries-dir", str(tmp_path / "summaries"),
            "--report-path", str(report),
        ])
        assert rc == 0


# ===========================================================================
# --apply-auto-approved gate
# ===========================================================================

class TestApplyAutoApprovedGate:
    def test_apply_in_dry_run_is_rejected(self, tmp_path, monkeypatch, capsys):
        _stage_repo(tmp_path, [{"folder": "f1", "slug": "s1"}])
        _wire_module_roots(monkeypatch, tmp_path)
        report = Path("/tmp") / f"batch-test-apply-dryrun-{tmp_path.name}.md"
        rc = rsb.main([
            "--apply-auto-approved",
            "--articles-dir", str(tmp_path / "articles"),
            "--index-path", str(tmp_path / "index.json"),
            "--summaries-dir", str(tmp_path / "summaries"),
            "--report-path", str(report),
        ])
        assert rc == 2
        captured = capsys.readouterr()
        assert "--apply-auto-approved" in captured.err

    def test_apply_promotes_only_auto_approve_with_dual_verifier(
        self, tmp_path, monkeypatch
    ):
        _stage_repo(tmp_path, [{"folder": "f1", "slug": "s1"}])
        _wire_module_roots(monkeypatch, tmp_path)
        _set_keys(monkeypatch)
        _wire_live_http(monkeypatch,
                        primary_verdict="AUTO_APPROVE",
                        secondary_verdict="AUTO_APPROVE")
        report = Path("/tmp") / f"batch-test-apply-aa-{tmp_path.name}.md"
        rc = rsb.main([
            "--batch", "--allow-network",
            "--max-budget-usd", "1.00",
            "--apply-auto-approved",
            "--articles-dir", str(tmp_path / "articles"),
            "--index-path", str(tmp_path / "index.json"),
            "--summaries-dir", str(tmp_path / "summaries"),
            "--report-path", str(report),
        ])
        assert rc == 0
        meta = json.loads(
            (tmp_path / "articles" / "f1" / "metadata.json").read_text()
        )
        assert "summary_short" in meta
        assert "summary_reviewed_at" in meta
        # Review file flipped to approved during the apply.
        review = (tmp_path / "summaries" / "s1.review.md").read_text()
        assert "Status: approved" in review

    def test_human_review_is_not_applied(self, tmp_path, monkeypatch):
        _stage_repo(tmp_path, [{"folder": "f1", "slug": "s1"}])
        _wire_module_roots(monkeypatch, tmp_path)
        _set_keys(monkeypatch)
        _wire_live_http(monkeypatch,
                        primary_verdict="HUMAN_REVIEW",
                        secondary_verdict="AUTO_APPROVE")
        report = Path("/tmp") / f"batch-test-hr-{tmp_path.name}.md"
        rc = rsb.main([
            "--batch", "--allow-network", "--max-budget-usd", "1.00",
            "--apply-auto-approved",
            "--articles-dir", str(tmp_path / "articles"),
            "--index-path", str(tmp_path / "index.json"),
            "--summaries-dir", str(tmp_path / "summaries"),
            "--report-path", str(report),
        ])
        assert rc == 0
        meta = json.loads(
            (tmp_path / "articles" / "f1" / "metadata.json").read_text()
        )
        assert "summary_short" not in meta
        # Review file stays draft.
        review = (tmp_path / "summaries" / "s1.review.md").read_text()
        assert "Status: draft" in review
        assert "Status: approved" not in review

    def test_reject_is_not_applied(self, tmp_path, monkeypatch):
        _stage_repo(tmp_path, [{"folder": "f1", "slug": "s1"}])
        _wire_module_roots(monkeypatch, tmp_path)
        _set_keys(monkeypatch)
        _wire_live_http(monkeypatch,
                        primary_verdict="REJECT",
                        secondary_verdict="REJECT")
        report = Path("/tmp") / f"batch-test-rej-{tmp_path.name}.md"
        rc = rsb.main([
            "--batch", "--allow-network", "--max-budget-usd", "1.00",
            "--apply-auto-approved",
            "--articles-dir", str(tmp_path / "articles"),
            "--index-path", str(tmp_path / "index.json"),
            "--summaries-dir", str(tmp_path / "summaries"),
            "--report-path", str(report),
        ])
        assert rc == 0
        meta = json.loads(
            (tmp_path / "articles" / "f1" / "metadata.json").read_text()
        )
        assert "summary_short" not in meta

    def test_missing_verifier_result_is_not_applied(self, tmp_path, monkeypatch):
        """Generation succeeds, verifier disabled → no apply."""
        _stage_repo(tmp_path, [{"folder": "f1", "slug": "s1"}])
        _wire_module_roots(monkeypatch, tmp_path)
        _set_keys(monkeypatch)
        _wire_live_http(monkeypatch)  # default verdicts unused
        report = Path("/tmp") / f"batch-test-noverify-{tmp_path.name}.md"
        rc = rsb.main([
            "--batch", "--allow-network", "--max-budget-usd", "1.00",
            "--no-verify",
            "--apply-auto-approved",
            "--articles-dir", str(tmp_path / "articles"),
            "--index-path", str(tmp_path / "index.json"),
            "--summaries-dir", str(tmp_path / "summaries"),
            "--report-path", str(report),
        ])
        assert rc == 0
        meta = json.loads(
            (tmp_path / "articles" / "f1" / "metadata.json").read_text()
        )
        assert "summary_short" not in meta


class TestCanAutoApply:
    """Unit tests on the auto-apply eligibility rule itself."""

    def _final(self, verdict="AUTO_APPROVE", single=False, secondary_skipped=False):
        return vs.FinalVerdict(
            final=verdict,
            det_status=GateStatus.PASS,
            primary=None, secondary=None,
            single_verifier=single,
            secondary_skipped_cost_cap=secondary_skipped,
            total_cost_usd=0.001,
        )

    def test_no_final_is_not_eligible(self):
        ok, _ = rsb.can_auto_apply(None)
        assert ok is False

    def test_auto_approve_dual_verifier_eligible(self):
        ok, _ = rsb.can_auto_apply(self._final())
        assert ok is True

    def test_single_verifier_not_eligible(self):
        ok, reason = rsb.can_auto_apply(self._final(single=True))
        assert ok is False
        assert "single" in reason.lower()

    def test_secondary_skipped_cost_cap_not_eligible(self):
        ok, reason = rsb.can_auto_apply(self._final(secondary_skipped=True))
        assert ok is False
        assert "cost" in reason.lower()

    def test_human_review_not_eligible(self):
        ok, _ = rsb.can_auto_apply(self._final(verdict="HUMAN_REVIEW"))
        assert ok is False

    def test_reject_not_eligible(self):
        ok, _ = rsb.can_auto_apply(self._final(verdict="REJECT"))
        assert ok is False


# ===========================================================================
# Budget cap
# ===========================================================================

class TestBudgetCap:
    def test_budget_cap_stops_before_next_article(self, tmp_path, monkeypatch):
        """Two articles staged, budget covers only one — second must halt."""
        _stage_repo(tmp_path, [
            {"folder": "f1", "slug": "s1"},
            {"folder": "f2", "slug": "s2"},
        ])
        _wire_module_roots(monkeypatch, tmp_path)
        _set_keys(monkeypatch)
        _wire_live_http(monkeypatch)
        report = Path("/tmp") / f"batch-test-budget-{tmp_path.name}.md"

        # One full pipeline pass through the stubs costs ~$0.00375
        # (MiniMax envelope $0.0024 + OpenAI + Anthropic verifier $0.00135).
        # Setting the budget at $0.003 means f1 alone overshoots the cap;
        # the runner must skip f2 with action=skipped_cost_cap.
        rc = rsb.main([
            "--batch", "--allow-network", "--max-budget-usd", "0.003",
            "--articles-dir", str(tmp_path / "articles"),
            "--index-path", str(tmp_path / "index.json"),
            "--summaries-dir", str(tmp_path / "summaries"),
            "--report-path", str(report),
        ])
        assert rc == 0
        text = report.read_text(encoding="utf-8")
        # f1 should have been processed; f2 should be a skipped_cost_cap row.
        assert "skipped_cost_cap" in text


# ===========================================================================
# Report safety
# ===========================================================================

class TestReportSafety:
    def test_default_report_is_outside_repo(self, tmp_path, monkeypatch):
        _stage_repo(tmp_path, [{"folder": "f1", "slug": "s1"}])
        _wire_module_roots(monkeypatch, tmp_path)
        report = rsb.resolve_report_path(None)
        assert str(report).startswith("/tmp/")

    def test_repo_internal_report_path_is_rejected(self, tmp_path, monkeypatch):
        _stage_repo(tmp_path, [{"folder": "f1", "slug": "s1"}])
        _wire_module_roots(monkeypatch, tmp_path)
        inside = tmp_path / "summaries" / "leaked-report.md"
        with pytest.raises(ValueError, match="must be outside the repository"):
            rsb.resolve_report_path(str(inside), repo_root=tmp_path)

    def test_secrets_redacted_in_report(self, tmp_path, monkeypatch):
        # Construct the fixture from pieces so the source line itself does not
        # carry a regex-matchable `sk-{20,}` literal that local pre-commit
        # secret scanners would flag.
        fake_openai = "sk-" + ("FIXTURE" + "0123456789ABCDEF")
        fake_bearer = "Bearer " + ("abcdefghij" + "0123456789-X")
        text = f"leaked {fake_bearer} and {fake_openai} again"
        red = rsb.redact(text)
        assert fake_bearer not in red
        assert fake_openai not in red
        assert "[REDACTED]" in red

    def test_secrets_not_printed_to_report_from_top_issue(
        self, tmp_path, monkeypatch
    ):
        _stage_repo(tmp_path, [{"folder": "f1", "slug": "s1"}])
        _wire_module_roots(monkeypatch, tmp_path)
        _set_keys(monkeypatch)
        # Verifier returns a top_issue containing a fake "Bearer" string —
        # the runner must redact it before writing to the report.
        sensitive_issue = "leaked Bearer FAKE-VALUE-MUST-NOT-LEAK-1234567890 detail"

        def fake_minimax(url, headers, body, timeout):
            return 200, 10.0, _minimax_envelope()

        def fake_verifier(url, headers, body, timeout):
            if "anthropic.com" in url:
                return 200, 10.0, _anthropic_verdict_envelope("HUMAN_REVIEW")
            return 200, 10.0, _openai_verdict_envelope(
                "HUMAN_REVIEW", top_issue=sensitive_issue,
            )

        monkeypatch.setattr(bs, "_http_post_json", fake_minimax)
        monkeypatch.setattr(vs, "_http_post_json", fake_verifier)

        report = Path("/tmp") / f"batch-test-redact-{tmp_path.name}.md"
        rc = rsb.main([
            "--batch", "--allow-network", "--max-budget-usd", "1.00",
            "--articles-dir", str(tmp_path / "articles"),
            "--index-path", str(tmp_path / "index.json"),
            "--summaries-dir", str(tmp_path / "summaries"),
            "--report-path", str(report),
        ])
        assert rc == 0
        report_text = report.read_text(encoding="utf-8")
        assert "FAKE-VALUE-MUST-NOT-LEAK-1234567890" not in report_text
        assert "[REDACTED]" in report_text


# ===========================================================================
# Filesystem invariants
# ===========================================================================

class TestFilesystemInvariants:
    def test_draft_preserved_when_apply_off(self, tmp_path, monkeypatch):
        _stage_repo(tmp_path, [{"folder": "f1", "slug": "s1"}])
        _wire_module_roots(monkeypatch, tmp_path)
        _set_keys(monkeypatch)
        _wire_live_http(monkeypatch)
        report = Path("/tmp") / f"batch-test-draft-{tmp_path.name}.md"
        rc = rsb.main([
            "--batch", "--allow-network", "--max-budget-usd", "1.00",
            "--articles-dir", str(tmp_path / "articles"),
            "--index-path", str(tmp_path / "index.json"),
            "--summaries-dir", str(tmp_path / "summaries"),
            "--report-path", str(report),
            # NOTE: no --apply-auto-approved
        ])
        assert rc == 0
        review = (tmp_path / "summaries" / "s1.review.md").read_text()
        assert "Status: draft" in review
        assert "Status: approved" not in review

    def test_article_body_unmodified(self, tmp_path, monkeypatch):
        _stage_repo(tmp_path, [{"folder": "f1", "slug": "s1"}])
        _wire_module_roots(monkeypatch, tmp_path)
        _set_keys(monkeypatch)
        _wire_live_http(monkeypatch)
        body_path = tmp_path / "articles" / "f1" / "article.md"
        before = body_path.read_text(encoding="utf-8")
        report = Path("/tmp") / f"batch-test-body-{tmp_path.name}.md"
        rc = rsb.main([
            "--batch", "--allow-network", "--max-budget-usd", "1.00",
            "--apply-auto-approved",
            "--articles-dir", str(tmp_path / "articles"),
            "--index-path", str(tmp_path / "index.json"),
            "--summaries-dir", str(tmp_path / "summaries"),
            "--report-path", str(report),
        ])
        assert rc == 0
        assert body_path.read_text(encoding="utf-8") == before

    def test_artifacts_not_rebuilt_without_flag(
        self, tmp_path, monkeypatch, capsys
    ):
        """--rebuild-artifacts is a hint flag in PR F; no subprocess.run hit."""
        _stage_repo(tmp_path, [{"folder": "f1", "slug": "s1"}])
        _wire_module_roots(monkeypatch, tmp_path)
        _set_keys(monkeypatch)
        _wire_live_http(monkeypatch)

        # Block subprocess.run for tools other than git rev-parse so we
        # detect an accidental rebuild.
        import subprocess as _sp
        real_run = _sp.run

        def gate(args, *a, **kw):
            argv = " ".join(args) if isinstance(args, (list, tuple)) else str(args)
            assert "rebuild_local" not in argv, "rebuild must not run automatically"
            assert "update_docs" not in argv, "update_docs must not run automatically"
            return real_run(args, *a, **kw)

        monkeypatch.setattr(_sp, "run", gate)

        report = Path("/tmp") / f"batch-test-rebuild-{tmp_path.name}.md"
        rc = rsb.main([
            "--batch", "--allow-network", "--max-budget-usd", "1.00",
            "--rebuild-artifacts",  # flag-only — should NOT actually rebuild
            "--articles-dir", str(tmp_path / "articles"),
            "--index-path", str(tmp_path / "index.json"),
            "--summaries-dir", str(tmp_path / "summaries"),
            "--report-path", str(report),
        ])
        assert rc == 0
        captured = capsys.readouterr()
        assert "flag-only" in captured.out
