#!/usr/bin/env python3
"""Tests for tools/provider_smoke.py.

All tests are network-free: provider calls are mocked via dependency-
injected http_post stubs, and the harness's HTTP path is never touched.

Six required cases from the PR A spec:
1. Sampler excludes already-summarized articles.
2. Experimental models are excluded unless explicitly requested.
3. Benchmark call budget caps work.
4. Benchmark report redacts secrets.
5. Benchmark report writes outside repo by default.
6. Word-count deterministic gate catches under/over ranges even when
   verifier says pass.

Plus a small set of supporting tests covering the dispatcher, the
deterministic-gate helpers, and the live-call triple gate.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

# tools/ is added to sys.path by tools/tests/conftest.py.
import provider_smoke as ps
import provider_smoke_models as psm


# -------------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------------

def _write_index(repo: Path, articles: list[dict]) -> Path:
    index = {"articles": articles}
    p = repo / "index.json"
    p.write_text(json.dumps(index), encoding="utf-8")
    return p


def _write_metadata(repo: Path, folder: str, *, summary_short: str | None) -> None:
    a_dir = repo / "articles" / folder
    a_dir.mkdir(parents=True, exist_ok=True)
    meta: dict = {"title": folder}
    if summary_short is not None:
        meta["summary_short"] = summary_short
    (a_dir / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
    # Minimal body so classify_article can read something.
    (a_dir / "article.md").write_text("# stub\n\nbody for tests.", encoding="utf-8")


@pytest.fixture
def fake_repo(tmp_path: Path) -> Path:
    """Empty tmp repo skeleton."""
    (tmp_path / "articles").mkdir()
    return tmp_path


# -------------------------------------------------------------------------
# 1. Sampler excludes already-summarized articles
# -------------------------------------------------------------------------

class TestSamplerExcludesSummarized:
    def test_missing_only_filters_summarized(self, fake_repo: Path) -> None:
        index = _write_index(fake_repo, [
            {"slug": "a-1", "folder": "2026-01-01-a", "title": "A"},
            {"slug": "b-1", "folder": "2026-01-02-b", "title": "B"},
            {"slug": "c-1", "folder": "2026-01-03-c", "title": "C"},
        ])
        _write_metadata(fake_repo, "2026-01-01-a", summary_short="already done")
        _write_metadata(fake_repo, "2026-01-02-b", summary_short=None)
        _write_metadata(fake_repo, "2026-01-03-c", summary_short="   ")  # whitespace = empty

        candidates = ps.select_missing_summary_articles(
            ps.load_index(index),
            fake_repo / "articles",
            exclude_folders=frozenset(),
        )
        folders = {c["folder"] for c in candidates}
        # a is already summarised → excluded.
        # b has summary_short=None → included.
        # c has whitespace-only summary_short → included.
        assert folders == {"2026-01-02-b", "2026-01-03-c"}

    def test_batch_001_002_003_folders_always_excluded(self, fake_repo: Path) -> None:
        # Pick one folder from the hard-coded exclude set.
        batch_folder = next(iter(psm.BATCH_001_002_003_FOLDERS))
        index = _write_index(fake_repo, [
            {"slug": "batch", "folder": batch_folder, "title": "Batch"},
            {"slug": "fresh", "folder": "2026-04-01-fresh", "title": "Fresh"},
        ])
        _write_metadata(fake_repo, batch_folder, summary_short=None)
        _write_metadata(fake_repo, "2026-04-01-fresh", summary_short=None)

        candidates = ps.select_missing_summary_articles(
            ps.load_index(index),
            fake_repo / "articles",
        )
        folders = {c["folder"] for c in candidates}
        # batch_folder excluded by hard-coded list even though metadata is empty.
        assert batch_folder not in folders
        assert "2026-04-01-fresh" in folders


# -------------------------------------------------------------------------
# 2. Experimental models excluded unless explicitly requested
# -------------------------------------------------------------------------

class TestExperimentalModelsGated:
    def test_default_resolution_is_defaults_only(self) -> None:
        resolved = psm.resolve_models(None, include_experimental=False)
        ids = [s.model_id for s in resolved.selected]
        for default_id in psm.DEFAULT_MODELS:
            assert default_id in ids
        for exp_id in psm.EXPERIMENTAL_MODELS:
            assert exp_id not in ids

    def test_requesting_experimental_without_opt_in_raises(self) -> None:
        with pytest.raises(ValueError, match="experimental"):
            psm.resolve_models(["deepseek-v4-pro"], include_experimental=False)

    def test_experimental_allowed_with_opt_in(self) -> None:
        resolved = psm.resolve_models(["deepseek-v4-pro"], include_experimental=True)
        assert [s.model_id for s in resolved.selected] == ["deepseek-v4-pro"]
        assert resolved.experimental_requested == ("deepseek-v4-pro",)

    def test_unknown_model_id_raises_with_known_list(self) -> None:
        with pytest.raises(ValueError, match="Unknown model"):
            psm.resolve_models(["not-a-real-model"], include_experimental=True)


# -------------------------------------------------------------------------
# 3. Benchmark call budget caps work
# -------------------------------------------------------------------------

class TestBudgetCaps:
    """The budget cap exits the per-row inner loop early.

    We exercise the loop directly via _run_benchmark with a mock http_post
    that returns a high-cost completion. The harness must halt before
    making every possible (article × model) call.
    """

    def _fake_response(self, spec: ps.ModelSpec) -> ps.CallResult:
        # Produce a valid JSON summary with bands in range so the row is
        # otherwise clean. The high reported usage drives cost up fast.
        summary = {
            "summary_short": "word " * 50,
            "summary_medium": "word " * 200,
            "summary_long": "word " * 500,
        }
        content = json.dumps(summary)
        if spec.provider == "anthropic":
            payload = {
                "content": [{"type": "text", "text": content}],
                "usage": {"input_tokens": 5_000, "output_tokens": 5_000},
                "stop_reason": "end_turn",
            }
        else:
            payload = {
                "choices": [{
                    "message": {"content": content},
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": 5_000, "completion_tokens": 5_000, "total_tokens": 10_000},
            }
        return ps.CallResult(status=200, latency_ms=10.0, body=json.dumps(payload))

    def test_budget_cap_aborts_before_running_every_call(
        self, fake_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # 4 articles × 2 models = 8 calls maximum; budget cap at $0.05 should
        # stop the loop well before then because each call costs ~$0.026
        # (5k input * 1.0 + 5k output * 5.0 = ~$0.03 for haiku;
        # ~$0.0065 for deepseek; ~$0.0075 for minimax).
        folders = [f"2026-04-0{i}-art" for i in range(1, 5)]
        index = _write_index(fake_repo, [
            {"slug": f, "folder": f, "title": f} for f in folders
        ])
        for f in folders:
            _write_metadata(fake_repo, f, summary_short=None)

        # Pretend keys are present so dispatch doesn't short-circuit.
        for var in ("ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY", "MINIMAX_API_KEY"):
            monkeypatch.setenv(var, "fake-key-not-real")

        # Patch the http_post used by the dispatcher to skip the network.
        def fake_http(url, headers, body, timeout=60):  # noqa: ARG001
            # We don't know which provider this is from URL alone in this
            # simple fake; use the haiku-style payload because it gives
            # the highest per-call cost and triggers the cap fastest.
            return self._fake_response(psm.DEFAULT_MODELS["claude-haiku-4-5-20251001"])

        monkeypatch.setattr(ps, "_http_post", fake_http)

        args = ps.build_parser().parse_args([
            "--benchmark",
            "--benchmark-n", "4",
            "--allow-network",
            "--max-budget-usd", "0.05",
            "--max-total-calls", "100",  # call cap intentionally not the bottleneck
            "--sample-strategy", "stratified",
            "--report-path", str(fake_repo.parent / "report.md"),
            "--articles-dir", str(fake_repo / "articles"),
            "--index-path", str(fake_repo / "index.json"),
            "--models", "claude-haiku-4-5-20251001",
        ])

        # repo_root has to point at fake_repo so the report-path check passes
        # AND so resolve_report_path can validate "outside repo".
        monkeypatch.setattr(ps, "REPO_ROOT", fake_repo)

        rc = ps._run_benchmark(
            args,
            psm.resolve_models(["claude-haiku-4-5-20251001"], include_experimental=False),
            is_live=True,
        )
        assert rc == 0

        # 4 articles × 1 model = 4 max calls. Each call costs $0.03 (5k*1 +
        # 5k*5 per million = 5 + 25 / 1_000_000 = 0.030 USD).
        # Budget of $0.05 means after the second call the cumulative cost
        # is $0.06 ≥ $0.05 → halt before the third article runs.
        report_path = fake_repo.parent / "report.md"
        text = report_path.read_text(encoding="utf-8")
        # Count rows whose model column references the model
        rows = [ln for ln in text.splitlines() if "claude-haiku-4-5-20251001" in ln and ln.startswith("|") ]
        assert 0 < len(rows) < 4, f"expected partial run halted by budget, got {len(rows)} rows"


# -------------------------------------------------------------------------
# 4. Benchmark report redacts secrets
# -------------------------------------------------------------------------

class TestReportRedactsSecrets:
    def test_secret_like_strings_are_redacted_in_top_issue(
        self, tmp_path: Path
    ) -> None:
        rows = [{
            "bucket": "normal",
            "folder": "2026-04-01-x",
            "model": "deepseek-v4-flash",
            "latency_ms": 100,
            "estimated_cost_usd": 0.001,
            "json_valid": False,
            "word_counts": None,
            "det_gate": "FAIL",
            "verifier_verdict": None,
            "top_issue": "error: leaked sk-abcdef0123456789ABCDEF0123 in body",
            "final_verdict": "REJECT",
            "production_recommendation": "reject_production",
        }]
        report_path = tmp_path / "report.md"
        ps.write_benchmark_report(
            report_path,
            rows,
            selection_summary={"candidate_count": 1, "selected_count": 1, "by_bucket": {}, "articles": []},
            args_summary={"mode": "benchmark"},
        )
        text = report_path.read_text(encoding="utf-8")
        # Secret prefix must be redacted; placeholder must be present.
        assert "sk-abcdef0123456789ABCDEF0123" not in text
        assert "[REDACTED]" in text

    def test_redact_secret_like_handles_multiple_patterns(self) -> None:
        sample = (
            "Authorization: Bearer abcdef0123456789ABCDEF0123-XYZ\n"
            "DeepL-Auth-Key fake-deepl-key-abcdef0123:fx-extra\n"
            "sk-anthropic-style-1234567890abcdefghij\n"
            "normal text untouched"
        )
        out = ps.redact_secret_like(sample)
        assert "Bearer abcdef" not in out
        assert "DeepL-Auth-Key fake-deepl" not in out
        assert "sk-anthropic-style-1234567890" not in out
        assert "normal text untouched" in out
        assert out.count("[REDACTED]") >= 3


# -------------------------------------------------------------------------
# 5. Report path outside repo by default
# -------------------------------------------------------------------------

class TestReportPathOutsideRepo:
    def test_default_path_is_in_tmp(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(ps, "REPO_ROOT", tmp_path)
        resolved = ps.resolve_report_path(None)
        assert str(resolved).startswith("/tmp/")
        assert "articles-provider-benchmark-" in str(resolved)

    def test_path_inside_repo_raises(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        # Pretend tmp_path is the repo, then ask for a path under it.
        monkeypatch.setattr(ps, "REPO_ROOT", tmp_path)
        bad = tmp_path / "summaries" / "report.md"
        bad.parent.mkdir()
        with pytest.raises(ValueError, match="outside the repository"):
            ps.resolve_report_path(str(bad))

    def test_path_outside_repo_resolves_to_absolute(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # tmp_path acts as the repo; the report goes to a sibling dir.
        monkeypatch.setattr(ps, "REPO_ROOT", tmp_path)
        outside = tmp_path.parent / "scratch" / "report.md"
        outside.parent.mkdir(parents=True, exist_ok=True)
        resolved = ps.resolve_report_path(str(outside))
        assert resolved == outside.resolve()


# -------------------------------------------------------------------------
# 6. Deterministic gate overrides verifier pass
# -------------------------------------------------------------------------

class TestDeterministicGateOverridesVerifier:
    def test_gate_downgrades_auto_approve_when_short_too_short(self) -> None:
        det_pass = False
        det_issues = ["summary_short word_count=30 BELOW minimum 40"]
        final = ps.merge_verdict("AUTO_APPROVE", det_pass, det_issues)
        assert final == "HUMAN_REVIEW"

    def test_gate_downgrades_auto_approve_when_short_too_long(self) -> None:
        det_pass = False
        det_issues = ["summary_short word_count=64 ABOVE maximum 60"]
        final = ps.merge_verdict("AUTO_APPROVE", det_pass, det_issues)
        assert final == "HUMAN_REVIEW"

    def test_gate_keeps_auto_approve_when_bands_clean(self) -> None:
        final = ps.merge_verdict("AUTO_APPROVE", det_pass=True, det_issues=[])
        assert final == "AUTO_APPROVE"

    def test_reject_stays_reject_regardless_of_gate(self) -> None:
        final = ps.merge_verdict("REJECT", det_pass=True, det_issues=[])
        assert final == "REJECT"

    def test_no_verifier_uses_gate_alone(self) -> None:
        assert ps.merge_verdict(None, det_pass=True, det_issues=[]) == "AUTO_APPROVE"
        assert ps.merge_verdict(None, det_pass=False, det_issues=["x"]) == "HUMAN_REVIEW"

    def test_deterministic_gate_detects_band_misses(self) -> None:
        # short: 30 words (BELOW 40), medium: 150 (BELOW 170), long: 600 (ABOVE 570).
        summaries = {
            "summary_short": "word " * 30,
            "summary_medium": "word " * 150,
            "summary_long": "word " * 600,
        }
        passed, issues = ps.deterministic_gate(summaries)
        assert passed is False
        # One issue per offending field.
        issue_text = "\n".join(issues)
        assert "BELOW minimum 40" in issue_text
        assert "BELOW minimum 170" in issue_text
        assert "ABOVE maximum 570" in issue_text

    def test_deterministic_gate_detects_orphan_citation_id(self) -> None:
        summaries = {
            "summary_short": ("word " * 50) + " citation reference S1 unexpected",
            "summary_medium": "word " * 200,
            "summary_long": "word " * 500,
        }
        passed, issues = ps.deterministic_gate(summaries)
        assert passed is False
        assert any("orphan citation" in i for i in issues)

    def test_deterministic_gate_detects_fabricated_faq_heading(self) -> None:
        summaries = {
            "summary_short": "word " * 50,
            "summary_medium": ("word " * 195) + " Frequently Asked Questions inserted",
            "summary_long": "word " * 500,
        }
        passed, issues = ps.deterministic_gate(summaries)
        assert passed is False
        assert any("FAQ" in i for i in issues)

    def test_deterministic_gate_passes_clean_input(self) -> None:
        summaries = {
            "summary_short": "word " * 50,
            "summary_medium": "word " * 200,
            "summary_long": "word " * 500,
        }
        passed, issues = ps.deterministic_gate(summaries)
        assert passed is True
        assert issues == []


# -------------------------------------------------------------------------
# Supporting tests: live-call triple gate
# -------------------------------------------------------------------------

class TestLiveCallGate:
    def _args(self, **overrides) -> object:
        args = ps.build_parser().parse_args([])
        for k, v in overrides.items():
            setattr(args, k, v)
        return args

    def test_default_args_block_live_call(self) -> None:
        args = self._args()
        with pytest.raises(ps.LiveGateError):
            ps.enforce_live_gate(args)

    def test_missing_allow_network_blocks(self) -> None:
        args = self._args(benchmark=True, max_budget_usd=1.0)
        with pytest.raises(ps.LiveGateError, match="--allow-network"):
            ps.enforce_live_gate(args)

    def test_missing_mode_blocks(self) -> None:
        args = self._args(allow_network=True, max_budget_usd=1.0)
        with pytest.raises(ps.LiveGateError, match="--benchmark or --connectivity-only"):
            ps.enforce_live_gate(args)

    def test_missing_budget_blocks(self) -> None:
        args = self._args(benchmark=True, allow_network=True)
        with pytest.raises(ps.LiveGateError, match="--max-budget-usd"):
            ps.enforce_live_gate(args)

    def test_zero_budget_blocks(self) -> None:
        args = self._args(benchmark=True, allow_network=True, max_budget_usd=0.0)
        with pytest.raises(ps.LiveGateError, match="--max-budget-usd"):
            ps.enforce_live_gate(args)

    def test_dry_run_blocks_even_with_full_triple_gate(self) -> None:
        args = self._args(benchmark=True, allow_network=True, max_budget_usd=1.0, dry_run=True)
        with pytest.raises(ps.LiveGateError, match="dry-run"):
            ps.enforce_live_gate(args)

    def test_full_triple_gate_passes(self) -> None:
        args = self._args(benchmark=True, allow_network=True, max_budget_usd=1.0)
        ps.enforce_live_gate(args)  # no raise


# -------------------------------------------------------------------------
# Supporting tests: stratified sampler + classify
# -------------------------------------------------------------------------

class TestClassifyArticle:
    def test_legal_regulatory_classification(self) -> None:
        body = " ".join(["GDPR DORA EU AI Act Article 16 conformity liability copyright"] * 5)
        assert ps.classify_article(body) == "legal_regulatory"

    def test_vendor_pricing_classification(self) -> None:
        body = (
            "Anthropic Claude DeepSeek MiniMax Moonshot pricing $0.30 per million tokens revenue MAU"
            * 3
        )
        assert ps.classify_article(body) == "vendor_pricing"

    def test_technical_classification(self) -> None:
        body = "GitHub Actions CI/CD API SBOM SLSA OpenSSF RAG endpoint deployment " * 3
        assert ps.classify_article(body) == "technical"

    def test_normal_fallback(self) -> None:
        body = "an editorial piece about engineering leadership and product strategy."
        assert ps.classify_article(body) == "normal"


class TestStratifiedSampler:
    def test_sampler_picks_across_buckets_when_possible(self, tmp_path: Path) -> None:
        articles_dir = tmp_path / "articles"
        articles_dir.mkdir()

        def make(folder: str, body: str) -> dict:
            a = articles_dir / folder
            a.mkdir()
            (a / "article.md").write_text(body, encoding="utf-8")
            return {"slug": folder, "folder": folder, "title": folder}

        candidates = [
            make("a-legal", "GDPR DORA EU AI Act Article 5 conformity liability copyright " * 4),
            make("b-vendor", "Anthropic OpenAI DeepSeek MiniMax Moonshot pricing $0.30 revenue MAU per million tokens " * 4),
            make("c-tech", "GitHub Actions CI/CD API SBOM SLSA OpenSSF RAG " * 4),
            make("d-normal", "engineering leadership product strategy piece"),
            make("e-normal-2", "editorial piece for CTO leadership"),
        ]
        selected = ps.stratified_sample(candidates, n=4, articles_dir=articles_dir)
        buckets = {a.get("bucket") for a in selected}
        # All four buckets represented when each has a candidate.
        assert "legal_regulatory" in buckets
        assert "vendor_pricing" in buckets
        assert "technical" in buckets
        assert "normal" in buckets
        assert len(selected) == 4

    def test_sampler_returns_empty_for_zero_n(self) -> None:
        assert ps.stratified_sample([{"folder": "x", "slug": "x", "title": "x"}], 0, Path("/tmp")) == []


# -------------------------------------------------------------------------
# Supporting tests: cost estimation + response parsing
# -------------------------------------------------------------------------

class TestCostEstimation:
    def test_cost_calculation_matches_pricing_table(self) -> None:
        spec = psm.DEFAULT_MODELS["claude-haiku-4-5-20251001"]
        cost = ps.estimate_cost(spec, {"input_tokens": 1_000_000, "output_tokens": 1_000_000})
        # 1M * 1.0 + 1M * 5.0 = $6.00
        assert cost == 6.0

    def test_cost_none_when_no_usage(self) -> None:
        spec = psm.DEFAULT_MODELS["deepseek-v4-flash"]
        assert ps.estimate_cost(spec, {}) is None

    def test_cost_none_when_pricing_unset(self) -> None:
        spec = psm.ModelSpec(
            model_id="x", provider="anthropic",
            endpoint="https://example.invalid",
            env_var="X", default_role="bulk_primary",
        )
        assert ps.estimate_cost(spec, {"input_tokens": 100, "output_tokens": 100}) is None


class TestExtractJsonObject:
    def test_strict_json_parses(self) -> None:
        assert ps.extract_json_object('{"a": 1}') == {"a": 1}

    def test_embedded_json_is_recovered(self) -> None:
        wrapper = "Here is the result:\n{\"key\": \"value\"}\nThanks."
        assert ps.extract_json_object(wrapper) == {"key": "value"}

    def test_no_json_returns_none(self) -> None:
        assert ps.extract_json_object("no json here") is None
        assert ps.extract_json_object("") is None
        assert ps.extract_json_object(None) is None  # type: ignore[arg-type]

    def test_array_at_top_level_returns_none(self) -> None:
        # Harness expects a dict; arrays are not acceptable JSON schemas here.
        assert ps.extract_json_object("[1, 2, 3]") is None
