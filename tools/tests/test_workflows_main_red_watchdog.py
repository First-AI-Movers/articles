#!/usr/bin/env python3
"""Guard: the main-red watchdog workflow stays report-only and minimally scoped (#489).

The watchdog exists because a non-required check cannot block a merge. It must
never grow into something that changes how merges happen -- a revert, a push, a
branch-protection edit -- so the properties that keep it report-only are pinned
here rather than left to review.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "main-red-watchdog.yml"
SHA_PIN_RE = re.compile(r"^[0-9a-f]{40}$")


@pytest.fixture(scope="module")
def raw() -> str:
    assert WORKFLOW.is_file(), f"{WORKFLOW.name} is missing"
    return WORKFLOW.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def document(raw) -> dict:
    return yaml.safe_load(raw) or {}


@pytest.fixture(scope="module")
def executable(document) -> str:
    """The workflow's executable content, with comments dropped.

    The header comments explain what the file must NOT contain (`pip install`,
    `${{ secrets.* }}`), so a raw-text scan for those strings would match the
    prose that forbids them. Re-serialising the parsed document keeps the
    prohibitions checkable against what actually runs.
    """
    return yaml.safe_dump(document, default_flow_style=False)


def _steps(document: dict) -> list[dict]:
    return [
        step
        for job in (document.get("jobs") or {}).values()
        if isinstance(job, dict)
        for step in (job.get("steps") or [])
        if isinstance(step, dict)
    ]


def test_triggers_are_schedule_and_dispatch_only(document):
    """`push: main` would always census a head whose checks have not reported."""
    # PyYAML parses a bare `on:` key as the boolean True.
    triggers = document.get("on") or document.get(True) or {}
    assert set(triggers) == {"schedule", "workflow_dispatch"}, triggers


def test_no_privileged_trigger(document):
    triggers = document.get("on") or document.get(True) or {}
    assert "pull_request_target" not in triggers


def test_cron_is_hourly_and_avoids_the_busy_window(document):
    triggers = document.get("on") or document.get(True) or {}
    crons = [entry["cron"] for entry in triggers["schedule"]]
    assert crons == ["25 * * * *"], crons
    minute = crons[0].split()[0]
    assert minute not in {"0", "17"}, "avoid the 06:00 e2e / 06:17 ingest minutes"


def test_permissions_are_exactly_read_contents_and_write_issues(document):
    assert document.get("permissions") == {"contents": "read", "issues": "write"}


def test_no_broader_permission_scopes(document):
    """It opens an issue. It must not be able to write code, a PR, or an action."""
    for scope in ("pull-requests", "actions", "checks", "deployments", "packages", "id-token"):
        assert scope not in (document.get("permissions") or {})
    assert document.get("permissions") != "write-all"


def test_static_concurrency_group(document):
    concurrency = document.get("concurrency") or {}
    assert concurrency.get("group") == "main-red-watchdog"
    assert concurrency.get("cancel-in-progress") is False
    assert "${{" not in str(concurrency.get("group")), "a static group serializes the censuses"


def test_single_job_on_ubuntu_with_a_timeout(document):
    jobs = document.get("jobs") or {}
    assert list(jobs) == ["watchdog"]
    assert jobs["watchdog"]["runs-on"] == "ubuntu-latest"
    assert jobs["watchdog"]["timeout-minutes"] <= 10


def test_the_job_name_matches_the_self_exclusion_constant():
    """The script excludes its own check-run by name, because a scheduled run
    attaches it to the very head being censused. The check-run's name is this
    job's `name:`, so a rename here would silently re-include it and make every
    census SKIP forever."""
    import importlib
    import sys

    sys.path.insert(0, str(REPO_ROOT / "tools"))
    watchdog = importlib.import_module("main_red_watchdog")
    document = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8")) or {}
    assert document["jobs"]["watchdog"]["name"] == watchdog.SELF_CHECK_NAME


def test_every_action_is_sha_pinned(document):
    """AGENTS.md: every non-local `uses:` is pinned to a 40-hex commit SHA."""
    for step in _steps(document):
        uses = step.get("uses")
        if not uses or uses.startswith("./"):
            continue
        _, _, ref = uses.rpartition("@")
        assert SHA_PIN_RE.match(ref), f"{uses} is not SHA-pinned"


def test_no_secret_expressions(executable):
    assert "secrets." not in executable, "the default GITHUB_TOKEN is the only credential"


def test_no_expression_interpolation_in_run_bodies(document):
    """Event data reaches the script as an env var, never as script text."""
    for step in _steps(document):
        assert "${{" not in (step.get("run") or "")


def test_the_only_run_step_invokes_the_watchdog(document):
    runs = [step["run"].strip() for step in _steps(document) if step.get("run")]
    assert runs == ["python3 tools/main_red_watchdog.py"]


def test_it_cannot_revert_push_or_merge(executable):
    """Report-only: the failure mode to prevent is this growing a write path."""
    for forbidden in ("git push", "git revert", "gh pr merge", "gh pr create", "--auto"):
        assert forbidden not in executable, f"{forbidden!r} must not appear in a report-only watchdog"


def test_checkout_does_not_persist_credentials(document):
    checkout = [s for s in _steps(document) if (s.get("uses") or "").startswith("actions/checkout")]
    assert checkout, "the workflow must check out the repository to run the script"
    assert checkout[0].get("with", {}).get("persist-credentials") is False


def test_no_pip_install(executable):
    """Standard library only, so a dependency resolution failure -- the very
    breakage this watchdog reports -- cannot also take the watchdog down."""
    assert "pip install" not in executable


def test_script_exists_and_reports_the_typed_vocabulary():
    script = REPO_ROOT / "tools" / "main_red_watchdog.py"
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert "MAIN_RED_WATCHDOG_RESULT:" in text
    for code in ("GREEN", "RED", "SKIP", "ERROR"):
        assert code in text
