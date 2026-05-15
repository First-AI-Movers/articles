"""Workflow-shape tests for the final CI audit cleanup batch (after PR #178/#179).

Two remaining audit items:

1. gitleaks.yml has no scheduled run. A pre-existing secret leaked in a file
   no PR ever touches would never get caught. Add a weekly cron.

2. mcp-server.yml's deploy job spins up a runner + runs `npm ci` on every
   push to main even when MCP_DEPLOY_ENABLED is unset, exits cleanly via an
   internal `if [ ... ]; then exit 0; fi`. Wasteful runner provisioning.
   Gate the job at the workflow `if:` level so no runner spins up unless
   the var is set.
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
# mcp-server — deploy job gated at workflow level
# ----------------------------------------------------------------------------


def test_mcp_deploy_job_gated_by_deploy_enabled_var():
    """The deploy job must check `vars.MCP_DEPLOY_ENABLED` in its `if:` so the
    runner does not spin up when MCP is not configured.

    The internal `if [ ... ]; then exit 0; fi` inside the runner shell step
    is defense in depth, but it still pays the cost of `actions/checkout`,
    `actions/setup-node`, and `npm ci` before deciding to skip. Hoisting the
    check to the job-level conditional avoids those entirely.
    """
    wf = _load("mcp-server.yml")
    deploy_job = wf["jobs"]["deploy"]
    job_if = deploy_job.get("if", "")
    assert "vars.MCP_DEPLOY_ENABLED" in job_if, (
        f"mcp-server.yml `deploy` job `if:` must reference "
        f"`vars.MCP_DEPLOY_ENABLED` so the runner does not spin up "
        f"when MCP deployment is not enabled. Current if: {job_if!r}"
    )
    # Existing safety gates must remain — only deploy on push to main, never PR.
    assert "github.ref == 'refs/heads/main'" in job_if, (
        f"mcp-server.yml `deploy` job lost its main-branch guard: {job_if!r}"
    )
    assert "github.event_name == 'push'" in job_if, (
        f"mcp-server.yml `deploy` job lost its push-event guard: {job_if!r}"
    )


def test_mcp_deploy_still_depends_on_test_and_export_data():
    """The deploy job must still wait for `test` + `export-data` to pass.
    Hoisting MCP_DEPLOY_ENABLED to `if:` must not have collapsed `needs:`.
    """
    wf = _load("mcp-server.yml")
    needs = wf["jobs"]["deploy"].get("needs") or []
    if isinstance(needs, str):
        needs = [needs]
    assert "test" in needs and "export-data" in needs, (
        f"mcp-server.yml `deploy` job must still need both `test` and "
        f"`export-data` jobs, got needs={needs!r}"
    )
