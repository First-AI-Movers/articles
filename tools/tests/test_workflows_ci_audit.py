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


# Pure-docs paths that should NOT trigger heavy CI on path-filtered
# workflows (article-quality, geo-audit). Any superset satisfies the
# assertion; the minimum bar is that ROADMAP and docs/** changes don't
# trigger.
#
# N6 (2026-05-15) deliberately drops the previous '**.md' blanket entry.
# Article content (`articles/<slug>/article.md`) IS markdown but IS
# content, so it MUST trigger heavy gates.
#
# N6-H (2026-05-15) drops `e2e.yml` from the path-filtered set entirely.
# `e2e.yml` is the SINGLE source of the required `e2e` context (branch
# protection identifies required checks by job name; a sibling
# `e2e-skip.yml` would publish a duplicate `e2e` context on mixed PRs
# and GitHub explicitly warns: "Using the same job name in multiple
# workflows can cause ambiguous status check results and block pull
# requests from being merged"). Instead, `e2e.yml` fires on every PR
# with no `paths-ignore` and uses an internal `classify_change` step
# to skip the heavy Playwright path on pure-docs PRs.
DOCS_ONLY_PATTERNS = {"ROADMAP.md", "docs/**"}


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
    "article-quality.yml",
    "geo-audit.yml",
])
def test_heavy_workflow_skips_docs_only_changes(workflow):
    """article-quality and geo-audit must declare paths-ignore for docs-only PRs.

    These workflows install heavy toolchains (Vale binary, GEO scoring) and
    provide no signal on a README or ROADMAP edit. They are NOT required
    by branch protection, so they can simply not run on pure-docs PRs.

    `e2e.yml` is deliberately NOT in this set (N6-H, 2026-05-15) — it is the
    single source of the required `e2e` context and must fire on every PR
    with no `paths-ignore`; the cheap-vs-heavy decision lives inside the job.
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


def test_no_duplicate_e2e_skip_workflow_file_exists():
    """N6-H (2026-05-15): `.github/workflows/e2e-skip.yml` must NOT exist.

    A separate skip-style workflow with the same `name:` and same
    `jobs.e2e` job name as `e2e.yml` produces duplicate `e2e` required-
    check contexts on mixed PRs. GitHub explicitly warns this can block
    merges via ambiguous status. The single-workflow design in `e2e.yml`
    (no `paths-ignore` + internal `classify_change` step) replaces it.
    """
    skip_path = WORKFLOWS / "e2e-skip.yml"
    assert not skip_path.exists(), (
        "e2e-skip.yml must not exist after N6-H. The required `e2e` check "
        "is the single context published by e2e.yml; a sibling skip "
        "workflow would create the duplicate-context ambiguity GitHub "
        "warns about (about-protected-branches)."
    )


def test_e2e_workflow_fires_on_every_pr_no_paths_ignore():
    """N6-H: `e2e.yml` must NOT use paths-ignore on `pull_request`.

    Since `e2e` is a required check identified by job name and `e2e.yml`
    is its single source, the workflow must fire on every PR. Skipping
    the heavy steps for pure-docs PRs is handled INSIDE the job by the
    `classify_change` step (see test_e2e_workflow_has_classify_change_step).
    """
    wf = _load("e2e.yml")
    on_section = wf.get("on") or wf.get(True)
    assert isinstance(on_section, dict), "e2e.yml `on` must be a dict"
    pr = on_section.get("pull_request") or {}
    assert not pr.get("paths-ignore"), (
        f"e2e.yml pull_request must NOT declare paths-ignore — the heavy/"
        f"skip decision is made inside the job by classify_change. "
        f"Found paths-ignore: {pr.get('paths-ignore')}"
    )
    assert not pr.get("paths"), (
        f"e2e.yml pull_request must NOT declare paths either — the "
        f"workflow must fire on every PR so the required `e2e` check "
        f"always reports. Found paths: {pr.get('paths')}"
    )


def test_e2e_workflow_has_classify_change_step():
    """N6-H: `e2e.yml` must have a `classify_change` step gating heavy work.

    The step must:
      (1) exist with id `classify_change`,
      (2) set output `kind` to either `heavy` or `skip`,
      (3) gate every Playwright-toolchain step on `kind == 'heavy'`.

    Articles/<slug>/article.md is NOT docs-only (it's article content)
    and MUST trigger heavy. Pure-docs is ONLY ROADMAP.md and docs/**.
    """
    wf = _load("e2e.yml")
    job = wf["jobs"]["e2e"]
    steps = job["steps"]

    classify = [s for s in steps if s.get("id") == "classify_change"]
    assert classify, "e2e.yml must declare a step with id `classify_change`"
    classify_step = classify[0]
    run = classify_step.get("run") or ""
    # The classifier must emit a `kind` output and recognize both heavy
    # and skip outcomes.
    assert "kind=heavy" in run and "kind=skip" in run, (
        "classify_change must emit `kind=heavy` and `kind=skip` outputs"
    )
    # Pure-docs detection MUST match ONLY ROADMAP.md and docs/. It must
    # NOT match `articles/` (since articles/**/article.md is content).
    assert "ROADMAP" in run and "docs/" in run, (
        "classify_change must explicitly treat ROADMAP.md and docs/ as "
        "the pure-docs set"
    )
    # Sanity: the classifier must not blanket-ignore '*.md' (would skip
    # heavy on article content edits — the N6 coverage gap).
    assert "*.md" not in run and "**.md" not in run, (
        "classify_change must NOT use '*.md' / '**.md' patterns — "
        "article content (articles/**/article.md) must trigger heavy"
    )

    # Every heavy step MUST be gated on the classify output.
    heavy_indicators = (
        "setup-python",
        "Install Python dependencies",
        "Build static site",
        "setup-node",
        "Install npm dependencies",
        "Install Playwright",
        "Run Playwright",
    )
    for step in steps:
        if step.get("id") == "classify_change":
            continue
        marker = step.get("uses", "") + " " + (step.get("name") or "")
        if any(ind in marker for ind in heavy_indicators):
            cond = step.get("if") or ""
            assert "classify_change.outputs.kind" in cond and "heavy" in cond, (
                f"Heavy step '{step.get('name') or step.get('uses')}' must "
                f"be gated on `classify_change.outputs.kind == 'heavy'`. "
                f"Currently: if={cond!r}"
            )


def test_e2e_workflow_runs_heavy_on_schedule_and_push():
    """N6-H: schedule and push-to-main triggers must always run heavy.

    Skipping the canary on a schedule would silently weaken nightly
    coverage. `classify_change` returns `heavy` for any non-pull_request
    event.
    """
    wf = _load("e2e.yml")
    on_section = wf.get("on") or wf.get(True)
    assert "schedule" in on_section, "e2e.yml must keep the nightly schedule"
    assert "push" in on_section, "e2e.yml must keep the push-to-main trigger"

    classify_step = next(
        s for s in wf["jobs"]["e2e"]["steps"] if s.get("id") == "classify_change"
    )
    run = classify_step.get("run") or ""
    env = classify_step.get("env") or {}
    env_values = " ".join(str(v) for v in env.values())
    # The non-PR branch of the classifier must short-circuit to heavy. `github.event_name`
    # may be referenced inline in the run block OR passed via an env mapping (zizmor
    # template-injection hardening: `EVENT_NAME: ${{ github.event_name }}` + `$EVENT_NAME`);
    # accept either form.
    references_event_name = "github.event_name" in run or "github.event_name" in env_values
    assert references_event_name and "pull_request" in run, (
        "classify_change must distinguish pull_request from other events"
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
