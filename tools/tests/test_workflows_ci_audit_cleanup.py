"""Workflow-shape tests for the final CI audit cleanup batch (after PR #178/#179).

Two remaining audit items:

1. gitleaks.yml has no scheduled run. A pre-existing secret leaked in a file
   no PR ever touches would never get caught. Add a weekly cron.

2. mcp-server.yml's deploy job runs in the `mcp-deploy` environment and gates
   its steps on the presence of the Cloudflare inputs (a job-level `if:` cannot
   read secrets), so with no inputs the job ends green and calls nothing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"


def _load(name: str) -> dict:
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


# ----------------------------------------------------------------------------
# gitleaks — weekly cron
# ----------------------------------------------------------------------------


def test_gitleaks_has_weekly_schedule():
    """gitleaks.yml must run on schedule, not only on PR/push.

    Without a cron, a leak introduced via a workflow bypass (force-push,
    admin override, repo-import) or sitting in a file no PR touches will
    never be caught. The audit flagged this as P1; we are closing it.
    """
    wf = _load("gitleaks.yml")
    on_section = wf.get("on") or wf.get(True)
    assert isinstance(on_section, dict), "gitleaks.yml `on` section must be a dict"

    schedule = on_section.get("schedule")
    assert schedule, (
        "gitleaks.yml must declare a `schedule:` trigger for defense-in-depth "
        "against pre-existing leaks in files no PR ever touches"
    )
    assert isinstance(schedule, list) and schedule, (
        f"gitleaks.yml `schedule` must be a non-empty list, got {schedule!r}"
    )
    # Each entry must be a {cron: "..."} mapping.
    for entry in schedule:
        assert isinstance(entry, dict) and "cron" in entry, (
            f"gitleaks.yml schedule entries must have a `cron` key, got {entry!r}"
        )


def test_gitleaks_workflow_dispatch_for_on_demand_scans():
    """Manual dispatch lets the operator trigger a full-history scan ad-hoc
    (e.g., after rotating a token, after an external repo import). Cheap to
    include and removes friction during incident response."""
    wf = _load("gitleaks.yml")
    on_section = wf.get("on") or wf.get(True)
    assert "workflow_dispatch" in on_section, (
        "gitleaks.yml should accept workflow_dispatch for on-demand operator scans"
    )


# ----------------------------------------------------------------------------
# mcp-server — deploy job scoped to an environment, gated on input presence
# ----------------------------------------------------------------------------


def _deploy_job() -> dict:
    return _load("mcp-server.yml")["jobs"]["deploy"]


def test_mcp_deploy_job_runs_in_the_mcp_deploy_environment():
    """The deploy job names the `mcp-deploy` environment, so the Cloudflare
    inputs are environment secrets rather than repository secrets."""
    assert _deploy_job().get("environment") == "mcp-deploy"


def test_mcp_deploy_job_if_keeps_main_push_guards_and_drops_the_variable_switch():
    """`MCP_DEPLOY_ENABLED` is retired as the switch. A job-level `if:` cannot
    read `secrets.*`, so the job-level condition is only the main-ref guard
    over two events: a push to main, or a manual dispatch of main (#508).

    Pinned as the exact expression. A substring check would accept the ref
    guard ORed with the events, which deploys a dispatch of any branch."""
    job_if = _deploy_job().get("if", "")
    assert "MCP_DEPLOY_ENABLED" not in job_if
    assert "secrets." not in job_if
    assert " ".join(job_if.split()) == (
        "github.ref == 'refs/heads/main' && "
        "(github.event_name == 'push' || github.event_name == 'workflow_dispatch')"
    ), f"deploy job condition changed: {job_if!r}"
    assert "MCP_DEPLOY_ENABLED" not in (WORKFLOWS / "mcp-server.yml").read_text(encoding="utf-8")


def test_mcp_deploy_guard_step_runs_first_and_exposes_only_a_boolean():
    """With no environment secrets the guard step reports `present=false`, and
    it never receives a credential value."""
    steps = _deploy_job()["steps"]
    guard = steps[0]
    assert guard.get("id") == "inputs"
    assert "if" not in guard, "the guard step must always run"
    env = guard.get("env", {})
    assert set(env) == {"INPUTS_PRESENT"}
    expr = env["INPUTS_PRESENT"]
    assert "secrets.CLOUDFLARE_API_TOKEN" in expr
    assert "secrets.CLOUDFLARE_ACCOUNT_ID" in expr
    # The guard's own working directory must exist before checkout.
    assert guard.get("working-directory") == "."
    assert "Deploy inputs absent" in guard["run"]
    assert "exit 1" not in guard["run"], "an absent input ends the job green"


def test_mcp_deploy_every_step_after_the_guard_is_skipped_when_inputs_are_absent():
    """No checkout, install or Cloudflare call happens unless the guard said so."""
    steps = _deploy_job()["steps"][1:]
    assert steps, "deploy steps are missing"
    for step in steps:
        assert step.get("if") == "steps.inputs.outputs.present == 'true'", step


def test_mcp_deploy_credentials_reach_only_the_deploy_step():
    """The Cloudflare secrets are mapped into the one step that deploys, not the
    job, so `npm ci` never sees them."""
    job = _deploy_job()
    assert "env" not in job
    carrying = [
        s for s in job["steps"]
        if "CLOUDFLARE_API_TOKEN" in s.get("env", {})
    ]
    assert [s.get("run") for s in carrying] == ["npm run deploy"]
    assert set(carrying[0]["env"]) == {"CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID"}


def test_mcp_deploy_still_depends_on_test_and_export_data():
    """The deploy job must still wait for the build + `export-data` jobs to pass.
    Scoping the job to an environment must not have collapsed `needs:`.
    The build job id is `mcp-server` (renamed from `test` to disambiguate its
    check-run context from tests.yml's required `test` context).
    """
    wf = _load("mcp-server.yml")
    needs = wf["jobs"]["deploy"].get("needs") or []
    if isinstance(needs, str):
        needs = [needs]
    assert "mcp-server" in needs and "export-data" in needs, (
        f"mcp-server.yml `deploy` job must still need both the `mcp-server` build "
        f"job and `export-data` job, got needs={needs!r}"
    )
