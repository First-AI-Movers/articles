"""Workflow-shape tests for .github/workflows/summary-auto-apply.yml.

A new workflow gets NO automatic coverage, so this file pins the A8 manual
apply-workflow safety contract by pure YAML parsing (no execution):

  * workflow_dispatch only (no schedule/push/pull_request/workflow_run/
    repository_dispatch);
  * permissions exactly {contents: write, pull-requests: write}, nothing broader;
  * static concurrency.group; no expression spliced into any run: body;
  * mandatory freshness on every runner invocation (--fresh-days,
    --published-after, --limit);
  * apply=false proof path is non-live (no --batch/--allow-network/
    --apply-auto-approved); apply=true live path is gated and carries
    --max-budget-usd + --apply-auto-approved;
  * input validation rejects a published_after on/before the residue edge
    2026-04-25;
  * secrets only under step env:, never in a run: body;
  * scoped add-paths (articles/*/metadata.json, never bare articles/*);
  * count-only public-surface scan; no auto-merge / direct-push step.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
WF_NAME = "summary-auto-apply.yml"
WF_PATH = WORKFLOWS / WF_NAME
JOB = "apply"


def _wf() -> dict:
    return yaml.safe_load(WF_PATH.read_text(encoding="utf-8"))


def _on(wf: dict) -> dict:
    # PyYAML 1.1 parses a bare `on:` key as boolean True.
    return wf.get("on") or wf.get(True)


def _inputs(wf: dict) -> dict:
    return _on(wf)["workflow_dispatch"]["inputs"]


def _steps(wf: dict) -> list:
    return wf["jobs"][JOB]["steps"]


def _run_bodies(wf: dict) -> list:
    return [s["run"] for s in _steps(wf) if "run" in s]


def _step_by_name(wf: dict, substr: str) -> dict:
    matches = [s for s in _steps(wf) if substr.lower() in str(s.get("name", "")).lower()]
    assert len(matches) == 1, f"expected exactly one step matching {substr!r}; got {len(matches)}"
    return matches[0]


def _runner_invocations(wf: dict) -> list:
    return [s for s in _steps(wf)
            if "run" in s and "tools/run_summary_batch.py" in s["run"]]


# --------------------------------------------------------------------------
# Trigger / permissions / concurrency
# --------------------------------------------------------------------------

def test_workflow_file_exists():
    assert WF_PATH.exists()


def test_trigger_is_workflow_dispatch_only():
    on = _on(_wf())
    assert isinstance(on, dict)
    assert "workflow_dispatch" in on
    for forbidden in ("schedule", "push", "pull_request", "workflow_run", "repository_dispatch"):
        assert forbidden not in on, f"must NOT declare a `{forbidden}` trigger"


def test_permissions_exact_minimal():
    perms = _wf().get("permissions") or {}
    assert perms == {"contents": "write", "pull-requests": "write"}, (
        f"permissions must be exactly contents:write + pull-requests:write; got {perms!r}"
    )


def test_no_broader_permission_scopes():
    perms = _wf().get("permissions") or {}
    for scope in ("id-token", "issues", "packages", "deployments", "actions", "checks"):
        assert scope not in perms, f"must not request `{scope}` permission"


def test_static_concurrency_group():
    c = _wf().get("concurrency")
    assert isinstance(c, dict) and c.get("group") == "summary-auto-apply"
    assert "${{" not in str(c["group"]), "concurrency.group must be static"
    assert c.get("cancel-in-progress") is False


def test_single_apply_job_on_ubuntu():
    wf = _wf()
    assert JOB in wf["jobs"]
    assert wf["jobs"][JOB]["runs-on"] == "ubuntu-latest"


# --------------------------------------------------------------------------
# Inputs + decision-lock defaults
# --------------------------------------------------------------------------

def test_inputs_exist():
    inp = _inputs(_wf())
    for name in ("fresh_days", "published_after", "limit", "max_budget_usd", "apply"):
        assert name in inp, f"missing dispatch input {name}"


def test_input_defaults_match_decision_lock():
    inp = _inputs(_wf())
    assert inp["fresh_days"]["default"] == "14"
    assert inp["published_after"]["default"] == "2026-05-01"
    assert inp["limit"]["default"] == "50"
    assert inp["max_budget_usd"]["default"] == "5.00"
    # apply is a boolean defaulting to the safe (no-network proof) path.
    assert inp["apply"]["type"] == "boolean"
    assert inp["apply"]["default"] is False


def test_freshness_inputs_are_required():
    inp = _inputs(_wf())
    for name in ("fresh_days", "published_after", "limit", "max_budget_usd"):
        assert inp[name].get("required") is True, f"{name} must be required"


# --------------------------------------------------------------------------
# Input validation enforces the residue floor
# --------------------------------------------------------------------------

def test_validation_step_enforces_residue_edge():
    step = _step_by_name(_wf(), "Validate inputs")
    body = step["run"]
    assert "2026-04-25" in body, "validation must reject published_after on/before the residue edge"
    assert "published_after" in body
    assert "fresh_days" in body and "limit" in body and "max_budget_usd" in body


# --------------------------------------------------------------------------
# Mandatory freshness on every runner invocation
# --------------------------------------------------------------------------

def test_every_runner_invocation_passes_freshness_and_limit():
    invs = _runner_invocations(_wf())
    assert invs, "expected at least one run_summary_batch.py invocation"
    for s in invs:
        run = s["run"]
        for flag in ("--missing-only", "--fresh-days", "--published-after", "--limit"):
            assert flag in run, f"runner invocation missing {flag}: {s.get('name')}"


# --------------------------------------------------------------------------
# apply=false proof path is non-live
# --------------------------------------------------------------------------

def test_proof_run_is_non_live():
    step = _step_by_name(_wf(), "Candidate proof run")
    run = step["run"]
    for forbidden in ("--batch", "--allow-network", "--apply-auto-approved", "--max-budget-usd"):
        assert forbidden not in run, f"apply=false proof run must not pass {forbidden}"
    assert "--dry-run" in run
    # Gated to the non-apply path.
    assert "inputs.apply" in str(step.get("if", "")) and "!" in str(step.get("if", ""))


def test_proof_run_report_paths_are_out_of_repo():
    run = _step_by_name(_wf(), "Candidate proof run")["run"]
    assert "RUNNER_TEMP" in run, "candidate/report paths must live in the runner temp dir"


# --------------------------------------------------------------------------
# apply=true live path is gated and bounded
# --------------------------------------------------------------------------

def test_allow_network_and_apply_only_on_apply_true():
    for s in _steps(_wf()):
        run = s.get("run", "")
        cond = str(s.get("if", ""))
        if "--allow-network" in run or "--apply-auto-approved" in run:
            assert "inputs.apply" in cond and "!" not in cond, (
                f"live flags must be gated on apply=true: {s.get('name')}"
            )


def test_live_invocation_is_bounded_and_dual_verifier():
    step = _step_by_name(_wf(), "Generate + apply")
    run = step["run"]
    for flag in ("--batch", "--allow-network", "--apply-auto-approved",
                 "--max-budget-usd", "--fresh-days", "--published-after", "--limit"):
        assert flag in run, f"live apply missing {flag}"
    # Repair loop pinned to cycle 1; no gate-weakening flags.
    assert "--max-repair-cycles 1" in " ".join(run.split())
    for weakening in ("--single-verifier", "--max-repair-cycles 2", "--relax", "--no-verify"):
        assert weakening not in run, f"live apply must not weaken the gate: {weakening}"


def test_no_live_run_without_budget():
    # Any step that goes live (--allow-network) must also carry --max-budget-usd.
    for s in _steps(_wf()):
        run = s.get("run", "")
        if "--allow-network" in run:
            assert "--max-budget-usd" in run, f"live run without budget cap: {s.get('name')}"


def test_presence_gate_required_keys_and_optional_deepseek():
    step = _step_by_name(_wf(), "presence gate")
    run = " ".join(step["run"].split())
    assert "tools/check_provider_keys_present.py" in run
    for key in ("MINIMAX_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        assert key in run
    assert "--optional DEEPSEEK_API_KEY" in run
    assert "inputs.apply" in str(step.get("if", "")) and "!" not in str(step.get("if", ""))


# --------------------------------------------------------------------------
# Secret-safety / injection hardening
# --------------------------------------------------------------------------

def test_no_expression_interpolation_in_run_bodies():
    for body in _run_bodies(_wf()):
        assert "${{" not in body, "no GitHub Actions expression may be spliced into a run: body"


def test_secrets_only_in_step_env():
    # secrets.* may appear only in step env: mappings or action with:, never run:.
    for body in _run_bodies(_wf()):
        assert "secrets." not in body, "secrets must never appear in a run: body"
    # Where secrets are bound, it is via env: (the live + presence steps).
    secret_steps = [s for s in _steps(_wf())
                    if any("secrets." in str(v) for v in (s.get("env") or {}).values())]
    assert secret_steps, "expected secrets bound via step env:"
    for s in secret_steps:
        assert "inputs.apply" in str(s.get("if", "")) and "!" not in str(s.get("if", "")), (
            "secret-bearing steps must be gated to apply=true"
        )


def test_no_env_dump():
    for body in _run_bodies(_wf()):
        assert "printenv" not in body
        assert "set -x" not in body
        assert "env | " not in body and "| env" not in body


# --------------------------------------------------------------------------
# PR creation: scoped, value-safe, no auto-merge, no direct push
# --------------------------------------------------------------------------

def _pr_step(wf: dict) -> dict:
    prs = [s for s in _steps(wf)
           if str(s.get("uses", "")).startswith("peter-evans/create-pull-request")]
    assert len(prs) == 1, f"expected exactly one peter-evans PR step; got {len(prs)}"
    return prs[0]


def test_pr_uses_stable_branch_and_no_auto_merge():
    wf = _wf()
    pr = _pr_step(wf)
    assert pr["with"]["branch"] == "summaries/auto-apply"
    assert pr["with"].get("body-path"), "PR body must come from a pre-scanned file"
    # No auto-merge anywhere.
    for s in _steps(wf):
        assert "auto-merge" not in str(s.get("uses", "")).lower()
    joined = "\n".join(_run_bodies(wf))
    for forbidden in ("gh pr merge", "auto_merge", "--auto", "git push", "--merge"):
        assert forbidden not in joined, f"must not `{forbidden}`"


def test_add_paths_are_scoped_no_bare_articles():
    pr = _pr_step(_wf())
    paths = [p.strip() for p in str(pr["with"]["add-paths"]).splitlines() if p.strip()]
    assert "articles/*/metadata.json" in paths
    for p in paths:
        assert p not in ("articles/*", "articles/**", "articles/", "articles"), (
            f"add-paths must not include a bare articles glob: {p}"
        )
        if p.startswith("articles"):
            assert p == "articles/*/metadata.json", f"only metadata.json under articles: {p}"
    # The deterministic artifacts must be committed so the drift check stays green.
    for artifact in ("index.json", "llms-full.txt", "mcp-server/src/generated/archive-data.json"):
        assert artifact in paths, f"missing generated artifact in add-paths: {artifact}"


def test_pr_creation_gated_on_applied_count():
    pr = _pr_step(_wf())
    cond = str(pr.get("if", ""))
    assert "inputs.apply" in cond and "steps.applied.outputs.count" in cond and "'0'" in cond


def test_rebuild_chain_in_order_and_gated():
    step = _step_by_name(_wf(), "Rebuild deterministic artifacts")
    run = step["run"]
    order = ["rebuild_local.py", "export_mcp_data.py", "check_generated_artifacts.py"]
    idxs = [run.index(t) for t in order]
    assert idxs == sorted(idxs), "rebuild chain must run in canonical order"
    cond = str(step.get("if", ""))
    assert "inputs.apply" in cond and "count" in cond


def test_public_surface_scan_is_count_only():
    step = _step_by_name(_wf(), "Compose and scan PR body")
    run = step["run"]
    assert "grep -cEI" in run, "public-surface scan must be count-only (grep -cEI)"
    assert "content withheld" in run, "scan must never print the matched line"


# --------------------------------------------------------------------------
# Codex review hardening (PR #253): optional fallback, finite budget, PR token
# --------------------------------------------------------------------------

def test_fallback_gated_on_deepseek_presence():
    # DeepSeek is optional (D7); --enable-fallback-on-undersize must be enabled
    # only when DEEPSEEK_API_KEY is present (a presence test), never forced --
    # otherwise the runner fails closed on an optional key.
    run = _step_by_name(_wf(), "Generate + apply")["run"]
    assert "--enable-fallback-on-undersize" in run
    assert "DEEPSEEK_API_KEY" in run and "-n " in run, (
        "fallback flag must be gated on a presence test of DEEPSEEK_API_KEY"
    )


def test_validation_rejects_non_finite_budget():
    body = _step_by_name(_wf(), "Validate inputs")["run"]
    assert "isfinite" in body, (
        "budget validation must reject non-finite values (inf/nan/overflow) that "
        "would bypass the cost ceiling"
    )


def test_pr_token_caveat_surfaced():
    body = _step_by_name(_wf(), "Compose and scan PR body")["run"]
    low = body.lower()
    assert "reopen" in low and "close" in low, (
        "PR body must surface the close/reopen caveat for the default-token CI gap"
    )


# --------------------------------------------------------------------------
# Action pins
# --------------------------------------------------------------------------

@pytest.mark.parametrize("prefix,pin", [
    ("actions/checkout", "@v7"),
    ("actions/setup-python", "@v7"),
    ("peter-evans/create-pull-request", "@v8"),
])
def test_action_pins_repo_consistent(prefix, pin):
    for s in _steps(_wf()):
        uses = str(s.get("uses", ""))
        if uses.startswith(prefix):
            assert uses.endswith(pin), f"{prefix} must be pinned {pin}; got {uses}"


def test_setup_python_reads_canonical_declaration():
    for s in _steps(_wf()):
        if str(s.get("uses", "")).startswith("actions/setup-python"):
            selector = s.get("with") or {}
            assert selector.get("python-version-file") == ".python-version"
            assert "python-version" not in selector
            return
    pytest.fail("no setup-python step")
