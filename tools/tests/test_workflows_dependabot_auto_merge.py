"""Workflow-shape tests for dependabot-auto-merge.yml (#432).

The workflow is the one step of the ordinary PR lifecycle Dependabot never
performs -- arming squash auto-merge under `aeos-merge-ready`. These tests pin
the properties that make it safe and keep it attached:

  * it hooks `workflow_run` on a workflow that actually runs for every
    pull_request head (tests.yml, no path filter) -- renaming that workflow
    would otherwise detach the trigger silently;
  * it never uses `pull_request_target`, declares bounded permissions, pins
    its only third-party action, and binds every event value to `env:`;
  * the arming runs on the App token (an App identity fires `push: main`
    workflows after the merge; the default GITHUB_TOKEN would not), gated on
    Dependabot being the actor of the triggering run.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
WF = WORKFLOWS / "dependabot-auto-merge.yml"
# Until a principal holding the `workflows` permission renames it, the workflow rides
# beside the code it runs: the machine principal that authored it cannot write under
# .github/workflows/ (#432). A file parked here is inert -- GitHub runs nothing outside
# .github/workflows/ -- so every shape rule below is enforced at whichever path holds it,
# and `test_workflow_is_installed_or_explicitly_pending` keeps the two states honest.
PENDING = REPO_ROOT / ".github" / "pending-workflows" / "dependabot-auto-merge.yml"
RUNBOOK = REPO_ROOT / "docs" / "OPERATIONS.md"
SHA_PIN_RE = re.compile(r"^[0-9a-f]{40}$")


def _wf_path() -> Path:
    return WF if WF.exists() else PENDING


def _load(path: Path | None = None) -> dict:
    return yaml.safe_load((path or _wf_path()).read_text(encoding="utf-8"))


def test_workflow_is_installed_or_explicitly_pending():
    """The workflow exists at exactly one of the two paths, and the runbook says which.

    While it is pending the runbook must name it, so the repository explains its own
    half-finished state instead of carrying a silent orphan. Deliberately NOT the
    converse: the remaining step must stay a single file rename a maintainer can do in
    the GitHub UI without also editing prose, so the installed state asserts only that
    no copy lingers behind. Removing the runbook's pending paragraph is the follow-up
    the same Issue carries (#432).
    """
    assert WF.exists() ^ PENDING.exists(), (
        f"expected the workflow at exactly one of {WF.relative_to(REPO_ROOT)} or "
        f"{PENDING.relative_to(REPO_ROOT)}; installed={WF.exists()} pending={PENDING.exists()}"
    )
    if not WF.exists():
        assert "pending-workflows/dependabot-auto-merge.yml" in RUNBOOK.read_text(encoding="utf-8"), (
            "while the workflow is parked outside .github/workflows/ it does not run; "
            "docs/OPERATIONS.md must say so and name the remaining step"
        )


def _job() -> dict:
    jobs = _load()["jobs"]
    assert list(jobs) == ["arm"], f"expected the single `arm` job, got {list(jobs)}"
    return jobs["arm"]


def _steps() -> list[dict]:
    return _job()["steps"]


def test_trigger_is_workflow_run_on_a_workflow_every_pr_runs():
    """The hook must be a workflow that runs on every pull_request with no path
    filter, so it is requested for every Dependabot head in every ecosystem."""
    on = _load()[True] if True in _load() else _load()["on"]
    assert set(on) == {"workflow_run"}, f"the only trigger must be workflow_run; got {sorted(on)}"
    hooked = on["workflow_run"]["workflows"]
    assert set(on["workflow_run"]["types"]) == {"requested", "completed"}
    names = {}
    for path in sorted(WORKFLOWS.glob("*.yml")):
        doc = _load(path)
        names[doc.get("name")] = doc
    for name in hooked:
        assert name in names, f"workflow_run hooks {name!r}, but no workflow in .github/workflows has that name"
        doc = names[name]
        triggers = doc[True] if True in doc else doc["on"]
        pr = triggers.get("pull_request") if isinstance(triggers, dict) else None
        assert "pull_request" in triggers, f"{name!r} must run on pull_request"
        assert not (isinstance(pr, dict) and (pr.get("paths") or pr.get("paths-ignore"))), (
            f"{name!r} filters pull_request by path, so it would not be requested for every "
            f"Dependabot head; hook a workflow with no path filter"
        )


def test_no_privileged_trigger_and_bounded_permissions():
    doc = _load()
    triggers = doc[True] if True in doc else doc["on"]
    assert "pull_request_target" not in triggers
    assert doc.get("permissions") == {"contents": "read"}, (
        f"GITHUB_TOKEN only checks out main; the arming uses the App token. Got {doc.get('permissions')!r}"
    )
    assert _job().get("permissions") is None


def test_third_party_actions_are_sha_pinned():
    for step in _steps():
        uses = step.get("uses")
        if not isinstance(uses, str):
            continue
        target, _, rev = uses.rpartition("@")
        owner = target.split("/", 1)[0]
        if owner in ("actions", "github"):
            continue
        assert SHA_PIN_RE.match(rev), f"third-party `uses: {uses}` must be pinned to a 40-hex commit"


def test_job_is_gated_on_dependabot_pull_request_runs():
    cond = " ".join(str(_job().get("if", "")).split())
    assert "github.event.workflow_run.event == 'pull_request'" in cond
    assert "github.event.workflow_run.actor.login == 'dependabot[bot]'" in cond
    assert "github.event.workflow_run.head_repository.full_name == github.repository" in cond
    assert "startsWith(github.event.workflow_run.head_branch, 'dependabot/')" in cond


def test_arming_runs_on_the_app_token_with_env_bound_inputs():
    mint = [s for s in _steps() if str(s.get("uses", "")).startswith("actions/create-github-app-token@")]
    assert len(mint) == 1 and mint[0].get("id") == "app_token"
    assert mint[0]["with"]["app-id"] == "${{ vars.ARTICLES_AUTOMATION_APP_ID }}"
    assert mint[0]["with"]["private-key"] == "${{ secrets.ARTICLES_AUTOMATION_APP_PRIVATE_KEY }}"

    arm = [s for s in _steps() if "arm_dependabot_auto_merge.py" in str(s.get("run", ""))]
    assert len(arm) == 1, "exactly one step runs tools/arm_dependabot_auto_merge.py"
    env = arm[0]["env"]
    assert env["GH_TOKEN"] == "${{ steps.app_token.outputs.token }}", (
        "the arming must use the App token: auto-merge armed with GITHUB_TOKEN merges without "
        "firing the push: main workflows"
    )
    for key in ("DEPENDABOT_PR_NUMBER", "DEPENDABOT_HEAD_BRANCH", "DEPENDABOT_HEAD_SHA"):
        assert key in env, f"{key} must be bound through env:"
    assert arm[0]["run"].strip() == "python3 tools/arm_dependabot_auto_merge.py"
    for step in _steps():
        run = step.get("run")
        if isinstance(run, str):
            assert "${{" not in run, f"no expression may be interpolated into a run: body; got {run!r}"


def test_script_exists_and_reports_the_typed_vocabulary():
    script = REPO_ROOT / "tools" / "arm_dependabot_auto_merge.py"
    text = script.read_text(encoding="utf-8")
    assert "DEPENDABOT_AUTO_MERGE_RESULT:" in text
    for code in ("ARMED", "MERGED", "SKIP", "REFUSED"):
        assert f'"{code}"' in text
