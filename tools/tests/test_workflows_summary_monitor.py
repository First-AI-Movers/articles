"""Workflow-shape tests for .github/workflows/summary-fresh-monitor.yml.

Pins the A13 notify-only monitor's safety contract by pure YAML parsing:

  * schedule (0 14 * * *, outside the 06:00-06:30 UTC busy window) + workflow_dispatch only;
  * permissions exactly {contents: read, issues: write} -- no contents:write, no
    pull-requests:write, no id-token;
  * NO provider keys / secrets / --batch / --allow-network / --apply-auto-approved;
  * the selector is invoked --dry-run with mandatory freshness flags;
  * selected=0 opens no issue; selected>0 opens/updates ONE deduplicated issue;
  * no summary-PR creation, no auto-merge, no git push;
  * value-safe issue body + count-only public-surface scan.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
WF_NAME = "summary-fresh-monitor.yml"
WF_PATH = WORKFLOWS / WF_NAME
JOB = "monitor"

PROVIDER_KEYS = ("MINIMAX_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY")


def _wf() -> dict:
    return yaml.safe_load(WF_PATH.read_text(encoding="utf-8"))


def _on(wf: dict) -> dict:
    return wf.get("on") or wf.get(True)


def _steps(wf: dict) -> list:
    return wf["jobs"][JOB]["steps"]


def _run_bodies(wf: dict) -> list:
    return [s["run"] for s in _steps(wf) if "run" in s]


def _step_by_name(wf: dict, substr: str) -> dict:
    m = [s for s in _steps(wf) if substr.lower() in str(s.get("name", "")).lower()]
    assert len(m) == 1, f"expected exactly one step matching {substr!r}; got {len(m)}"
    return m[0]


def _text() -> str:
    return WF_PATH.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Triggers / permissions / concurrency
# --------------------------------------------------------------------------

def test_workflow_exists():
    assert WF_PATH.exists()


def test_triggers_are_schedule_and_dispatch_only():
    on = _on(_wf())
    assert "workflow_dispatch" in on
    assert "schedule" in on
    for forbidden in ("workflow_run", "push", "pull_request", "repository_dispatch"):
        assert forbidden not in on, f"monitor must not declare `{forbidden}`"


def test_cron_is_daily_1400_and_avoids_busy_window():
    sched = _on(_wf())["schedule"]
    crons = [s["cron"] for s in sched]
    assert crons == ["0 14 * * *"], f"expected only 0 14 * * *; got {crons}"
    minute, hour = crons[0].split()[0], crons[0].split()[1]
    assert hour != "6", "cron must avoid the 06:00-06:30 UTC ingest/e2e busy window"
    assert (minute, hour) == ("0", "14")


def test_permissions_exact_contents_read_issues_write():
    perms = _wf().get("permissions") or {}
    assert perms == {"contents": "read", "issues": "write"}, (
        f"permissions must be exactly contents:read + issues:write; got {perms!r}"
    )


def test_no_broader_permissions():
    perms = _wf().get("permissions") or {}
    assert perms.get("contents") != "write"
    for scope in ("pull-requests", "id-token", "packages", "deployments", "actions"):
        assert scope not in perms, f"monitor must not request `{scope}`"


def test_static_concurrency_group():
    c = _wf().get("concurrency")
    assert isinstance(c, dict) and c.get("group") == "summary-fresh-monitor"
    assert "${{" not in str(c["group"])
    assert c.get("cancel-in-progress") is False


def test_single_monitor_job_on_ubuntu():
    wf = _wf()
    assert JOB in wf["jobs"]
    assert wf["jobs"][JOB]["runs-on"] == "ubuntu-latest"


# --------------------------------------------------------------------------
# No providers / no secrets / no apply
# --------------------------------------------------------------------------

def test_no_provider_keys_anywhere():
    text = _text()
    for key in PROVIDER_KEYS:
        assert key not in text, f"monitor must not reference provider key {key}"


def test_no_secret_expressions():
    # The monitor uses ${{ github.token }} for issue ops, never a `secrets.*` ref.
    assert "${{ secrets" not in _text() and "${{secrets" not in _text()


def test_no_live_or_apply_flags():
    joined = "\n".join(_run_bodies(_wf()))
    for forbidden in ("--batch", "--allow-network", "--apply-auto-approved"):
        assert forbidden not in joined, f"monitor must never pass {forbidden}"


def test_no_env_dump():
    for body in _run_bodies(_wf()):
        assert "printenv" not in body and "set -x" not in body
        assert "env | " not in body and "| env" not in body


# --------------------------------------------------------------------------
# Selector invocation (no-network dry-run with mandatory freshness)
# --------------------------------------------------------------------------

def _detect_run(wf: dict) -> str:
    runs = [r for r in _run_bodies(wf) if "tools/run_summary_batch.py" in r]
    assert len(runs) == 1, f"expected one selector invocation; got {len(runs)}"
    return runs[0]


def test_selector_is_dry_run_with_freshness():
    run = _detect_run(_wf())
    for flag in ("--missing-only", "--fresh-days", "--published-after", "--limit",
                 "--dry-run", "--candidate-report"):
        assert flag in run, f"selector invocation missing {flag}"


def test_validation_enforces_residue_floor():
    body = _step_by_name(_wf(), "Detect fresh candidates")["run"]
    assert "2026-04-25" in body
    assert "fresh_days" in body and "published_after" in body and "limit" in body


def test_selector_failure_is_preserved_not_masked():
    # A selector crash must fail the step (-> incident issue), never be masked
    # into a silent selected=0. The step captures the exit code explicitly and
    # sets pipefail; it must not pipe the selector into `tee`.
    body = _step_by_name(_wf(), "Detect fresh candidates")["run"]
    assert "set -eo pipefail" in body
    assert "|| rc=$?" in body and 'exit "${rc}"' in body
    assert "run_summary_batch.py" in body and "| tee" not in body


def test_input_defaults():
    inp = _on(_wf())["workflow_dispatch"]["inputs"]
    assert inp["fresh_days"]["default"] == "14"
    assert inp["published_after"]["default"] == "2026-05-01"
    assert inp["limit"]["default"] == "50"
    # schedule path must fall back to the same defaults.
    detect_env = _step_by_name(_wf(), "Detect fresh candidates").get("env") or {}
    assert "'14'" in str(detect_env.get("FRESH_DAYS"))
    assert "'2026-05-01'" in str(detect_env.get("PUBLISHED_AFTER"))
    assert "'50'" in str(detect_env.get("LIMIT"))


# --------------------------------------------------------------------------
# Issue behaviour: no-op at 0, deduplicated notify at >0, never a summary PR
# --------------------------------------------------------------------------

def test_selected_zero_opens_no_issue():
    noop = _step_by_name(_wf(), "No fresh candidates")
    assert "steps.detect.outputs.selected == '0'" in str(noop.get("if"))
    assert "gh issue create" not in noop["run"] and "gh issue comment" not in noop["run"]


def test_selected_positive_opens_or_updates_one_dedup_issue():
    notify = _step_by_name(_wf(), "Notify via deduplicated issue")
    assert "selected != '0'" in str(notify.get("if"))
    run = notify["run"]
    assert "gh issue list" in run, "must dedup-search before creating"
    assert "gh issue create" in run and "gh issue edit" in run, (
        "must create a new issue OR edit (refresh) the existing deduplicated one"
    )


def test_no_summary_pr_or_automerge_or_push():
    wf = _wf()
    for s in _steps(wf):
        assert not str(s.get("uses", "")).startswith("peter-evans/create-pull-request")
    joined = "\n".join(_run_bodies(wf))
    for forbidden in ("git push", "git commit", "--add-paths", "gh pr merge",
                      "gh pr create", "auto_merge", "--auto", "--merge"):
        assert forbidden not in joined, f"monitor must not `{forbidden}`"


def test_issue_body_value_safe_and_scanned():
    notify = _step_by_name(_wf(), "Notify via deduplicated issue")["run"]
    # No article body file is read into the issue.
    assert "article.md" not in notify
    # Count-only public-surface scan, content withheld.
    assert "grep -cEI" in notify and "content withheld" in notify


def test_incident_issue_gated_on_failure():
    inc = _step_by_name(_wf(), "Incident issue on monitor failure")
    assert "failure()" in str(inc.get("if"))
    assert "gh issue" in inc["run"]


# --------------------------------------------------------------------------
# Action pins
# --------------------------------------------------------------------------

@pytest.mark.parametrize("prefix,pin", [
    ("actions/checkout", "@v6"),
    ("actions/setup-python", "@v6"),
])
def test_action_pins(prefix, pin):
    for s in _steps(_wf()):
        uses = str(s.get("uses", ""))
        if uses.startswith(prefix):
            assert uses.endswith(pin)
