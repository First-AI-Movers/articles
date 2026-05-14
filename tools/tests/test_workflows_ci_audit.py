"""Workflow-shape tests for the CI audit fixes (P0/P1 items).

These tests parse the `.github/workflows/*.yml` files and assert structural
properties that capture three specific changes:

1. IndexNow submission is LIVE (not --dry-run) in build-and-deploy.yml.
2. Both Airtable ingestion workflows declare a `concurrency` block so two
   simultaneous dispatches do not race on the same rebuild artifacts.
3. The heavy "runs on every PR" workflows (e2e, article-quality, geo-audit)
   skip docs-only changes via `paths-ignore`. gitleaks is deliberately NOT
   in this set — secrets can land in any file.

Each test reads the YAML directly. No execution.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"


def _load(name: str) -> dict:
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


# Standard docs-only paths that should NOT trigger heavy CI. Any superset
# satisfies the assertion (e.g., a workflow may also exclude '*.txt'); the
# minimum bar is that markdown docs and ROADMAP changes don't trigger.
DOCS_ONLY_PATTERNS = {"ROADMAP.md", "docs/**", "**.md"}


# ----------------------------------------------------------------------------
# T1 — IndexNow runs live in build-and-deploy.yml
# ----------------------------------------------------------------------------


def test_indexnow_step_does_not_use_dry_run():
    wf = _load("build-and-deploy.yml")
    indexnow_job = wf["jobs"]["indexnow"]
    steps = indexnow_job["steps"]
    indexnow_steps = [s for s in steps if "submit_indexnow.py" in (s.get("run") or "")]
    assert indexnow_steps, "build-and-deploy.yml indexnow job missing submit_indexnow.py call"
    for step in indexnow_steps:
        assert "--dry-run" not in step["run"], (
            f"IndexNow step '{step.get('name')}' still uses --dry-run; should submit live"
        )


def test_indexnow_step_is_non_blocking():
    """Live IndexNow must not fail the workflow if Bing/Yandex transiently errors.

    Either the step has continue-on-error: true, or the whole job does.
    """
    wf = _load("build-and-deploy.yml")
    indexnow_job = wf["jobs"]["indexnow"]
    job_lenient = indexnow_job.get("continue-on-error", False) is True
    step_lenient = any(
        s.get("continue-on-error") is True
        for s in indexnow_job["steps"]
        if "submit_indexnow.py" in (s.get("run") or "")
    )
    assert job_lenient or step_lenient, (
        "Live IndexNow submission must be non-blocking (continue-on-error: true)"
    )


# ----------------------------------------------------------------------------
# T2 — Airtable ingestion workflows declare a concurrency group
# ----------------------------------------------------------------------------


@pytest.mark.parametrize("workflow", [
    "ingest-airtable.yml",
    "ingest-airtable-dispatch.yml",
])
def test_airtable_ingestion_has_concurrency_block(workflow):
    wf = _load(workflow)
    concurrency = wf.get("concurrency")
    assert concurrency is not None, (
        f"{workflow} must declare a top-level concurrency block "
        f"to prevent simultaneous dispatches from racing"
    )
    assert isinstance(concurrency, dict), (
        f"{workflow} concurrency must be an object with `group` and optionally "
        f"`cancel-in-progress` — got {type(concurrency).__name__}"
    )
    assert "group" in concurrency, f"{workflow} concurrency missing `group` key"
    # Don't lock in the exact group string, but it must be deterministic
    # (not a per-run variable) so concurrent runs collide.
    assert "${{" not in str(concurrency["group"]), (
        f"{workflow} concurrency.group must be a static string, not a runtime expression"
    )


# ----------------------------------------------------------------------------
# T3 — Heavy workflows skip docs-only changes via paths-ignore
# ----------------------------------------------------------------------------


@pytest.mark.parametrize("workflow", [
    "e2e.yml",
    "article-quality.yml",
    "geo-audit.yml",
])
def test_heavy_workflow_skips_docs_only_changes(workflow):
    """e2e, article-quality, geo-audit must declare paths-ignore for docs-only PRs.

    These workflows install heavy toolchains (Playwright + Chromium for e2e,
    Vale binary for article-quality, etc.) and provide no signal on a README
    or ROADMAP edit. Skipping them on docs-only changes is the highest-ROI
    CI minutes optimization in the audit.
    """
    wf = _load(workflow)
    # PyYAML parses bare 'on' as the boolean True (YAML 1.1). Accept either.
    on_section = wf.get("on") or wf.get(True)
    assert isinstance(on_section, dict), f"{workflow} `on` section must be a dict"

    # Each of pull_request and push that exists must have a paths-ignore.
    triggers_checked = 0
    for trigger_name in ("pull_request", "push"):
        trigger = on_section.get(trigger_name)
        if trigger is None:
            continue
        triggers_checked += 1
        # `pull_request:` with no value parses to None; coerce.
        trigger = trigger or {}
        paths_ignore = trigger.get("paths-ignore") or []
        ignored = set(paths_ignore)
        missing = DOCS_ONLY_PATTERNS - ignored
        assert not missing, (
            f"{workflow} `{trigger_name}` trigger missing paths-ignore "
            f"entries for docs-only changes: {sorted(missing)}. "
            f"Currently: {sorted(ignored) or 'none'}"
        )
    assert triggers_checked > 0, (
        f"{workflow} has neither `pull_request` nor `push` trigger to gate"
    )


def test_gitleaks_remains_no_paths_ignore():
    """gitleaks must NOT have paths-ignore on push/PR triggers.

    Secrets can land in any file (including docs), so gitleaks deliberately
    stays no-filter. This test pins that decision so a future "consistency"
    refactor does not accidentally weaken secret scanning coverage.
    """
    wf = _load("gitleaks.yml")
    on_section = wf.get("on") or wf.get(True)
    for trigger_name in ("pull_request", "push"):
        trigger = on_section.get(trigger_name)
        if trigger is None:
            continue
        trigger = trigger or {}
        assert "paths-ignore" not in trigger, (
            f"gitleaks.yml must not have paths-ignore on {trigger_name} — "
            f"secrets can land anywhere; full coverage required"
        )
