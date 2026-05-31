"""Workflow + tooling shape tests for the CI audit follow-up (Epic A + B).

Epic A — clean up ingest-article.yml:
- No dead Node/npm setup (only used by Playwright via e2e.yml, not here)
- No misleading dry-run-then-write redundancy

Epic B — close drift / branch-protection / auto-merge gaps:
- check_generated_artifacts.py must track ROADMAP.md (the cron ingestion
  patches it via update_docs.py — drift here is the same class of bug that
  required commit 75ca5fa in PR #178)
- BRANCH_PROTECTION.md required-checks list must match the auto-merge
  script's REQUIRED_CHECKS (source of truth)
- auto_merge_ingestion_pr.py:HEAD_BRANCH_PREFIX must be specific enough
  that it cannot accidentally match E20b dispatch PRs
  (ingest/airtable-record-recXXX)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"


def _load_yaml(name: str) -> dict:
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


# ----------------------------------------------------------------------------
# Epic A — ingest-article.yml cleanup
# ----------------------------------------------------------------------------


def test_ingest_article_does_not_install_node():
    """No tools/ingest_article.py path calls node/npm — these steps are dead."""
    wf = _load_yaml("ingest-article.yml")
    steps = wf["jobs"]["ingest"]["steps"]

    setup_node_steps = [
        s for s in steps if isinstance(s.get("uses"), str) and "setup-node" in s["uses"]
    ]
    assert not setup_node_steps, (
        f"ingest-article.yml must not invoke actions/setup-node — verified dead "
        f"(no node/npm callers in tools/ingest_article.py, rebuild_local.py, "
        f"normalize_tags.py, check_duplicate_titles.py). Found: {setup_node_steps}"
    )

    npm_steps = [s for s in steps if "npm ci" in (s.get("run") or "")]
    assert not npm_steps, (
        f"ingest-article.yml must not run `npm ci` — no JS dependencies are "
        f"consumed by the ingestion pipeline. Found: {[s.get('name') for s in npm_steps]}"
    )


def test_ingest_article_has_no_dry_run_redundancy():
    """The dry-run-then-write pattern wastes a runner pass with no captured output.

    Allow either: exactly one ingest_article.py call (the write), OR a
    workflow_dispatch-gated dry-run for debug (with an `if:` condition).
    Reject: unconditional --dry-run immediately followed by --write.
    """
    wf = _load_yaml("ingest-article.yml")
    steps = wf["jobs"]["ingest"]["steps"]
    ingest_steps = [
        s for s in steps if "tools/ingest_article.py" in (s.get("run") or "")
    ]
    dry_runs = [s for s in ingest_steps if "--dry-run" in s["run"]]
    writes = [s for s in ingest_steps if "--write" in s["run"]]

    # Always require exactly one write step.
    assert len(writes) == 1, (
        f"Expected exactly one --write ingest_article.py call, got {len(writes)}"
    )

    # Dry-run is allowed only if it is conditional (e.g., gated by a
    # workflow_dispatch debug flag). An unconditional dry-run preceding the
    # write is the dead-runner pattern we are removing.
    for dr in dry_runs:
        assert dr.get("if"), (
            f"Dry-run step '{dr.get('name')}' is unconditional — it always runs "
            f"before --write, discarding its output. Either gate it behind `if:` "
            f"or remove the step entirely."
        )


def test_ingest_article_dispatch_payload_uses_env_var_not_shell_interpolation():
    """The repository_dispatch payload must not be interpolated into a
    shell command string.

    The historical pattern was:

        python3 -c "import json,sys; json.dump(${{ toJson(...) }}, ...)"

    A crafted client_payload containing shell-significant characters (`, ", $, ;)
    could break out of the bash double-quoted string and execute on the runner.
    The hardened shape passes the payload through an env var and parses it
    inside Python via os.environ; a single-quoted heredoc prevents the shell
    from expanding the Python body.
    """
    wf_text = (WORKFLOWS / "ingest-article.yml").read_text(encoding="utf-8")
    wf = _load_yaml("ingest-article.yml")
    steps = wf["jobs"]["ingest"]["steps"]

    # The exact unsafe interpolation must not appear in any step's run body.
    run_bodies = " ".join((s.get("run") or "") for s in steps)
    assert "${{ toJson(github.event.client_payload) }}" not in run_bodies, (
        "client_payload toJson(...) must not appear in any step's run: body; "
        "it belongs in env: so the payload never reaches the shell."
    )
    assert "json.dump(${{" not in wf_text, (
        "ingest-article.yml must not interpolate ${{ ... }} into a Python "
        "shell command — that is a workflow-injection vector."
    )

    # Locate the repository_dispatch payload-writing step.
    dispatch_steps = [
        s for s in steps
        if "repository_dispatch" in (s.get("if") or "")
        and "payload" in (s.get("name", "").lower())
    ]
    assert len(dispatch_steps) == 1, (
        "Expected exactly one repository_dispatch payload-writing step; "
        f"found {len(dispatch_steps)}"
    )
    step = dispatch_steps[0]

    # The payload must be handed off via env: bound to toJson(client_payload).
    step_env = step.get("env") or {}
    assert any(
        "toJson(github.event.client_payload)" in str(v)
        for v in step_env.values()
    ), (
        "Dispatch payload-writing step must declare an env: var bound to "
        f"toJson(github.event.client_payload); got: {step_env!r}"
    )

    # The run body must read from os.environ and still write PAYLOAD_FILE so
    # the downstream `ingest_article.py --payload-file` contract is preserved.
    run_body = step.get("run") or ""
    assert "os.environ" in run_body, (
        "Dispatch payload-writing step must read the payload from os.environ, "
        "not from a shell-interpolated literal."
    )
    assert "PAYLOAD_FILE" in run_body, (
        "Dispatch payload-writing step must still write to PAYLOAD_FILE so "
        "downstream `ingest_article.py --payload-file` keeps working."
    )
    # A quoted heredoc disables shell expansion of $, `, and \ inside the body.
    assert "<<'PY'" in run_body or '<<"PY"' in run_body, (
        "Python heredoc must be quoted (e.g. <<'PY') so the shell performs "
        "no parameter or backtick expansion on the body."
    )


# ----------------------------------------------------------------------------
# Epic B — drift detector + branch protection + auto-merge prefix
# ----------------------------------------------------------------------------


def _check_artifacts_module():
    """Import path-agnostic load of tools/check_generated_artifacts.py."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "check_generated_artifacts",
        REPO_ROOT / "tools" / "check_generated_artifacts.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _auto_merge_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "auto_merge_ingestion_pr",
        REPO_ROOT / "tools" / "auto_merge_ingestion_pr.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_drift_check_tracks_roadmap():
    """ROADMAP.md is patched by tools/update_docs.py during ingestion.

    Without tracking it in ARTIFACTS, a desync between the article count
    and ROADMAP's auto:operational-state block can land silently — exactly
    the failure mode that produced commit 75ca5fa in PR #178.
    """
    mod = _check_artifacts_module()
    assert "ROADMAP.md" in mod.ARTIFACTS, (
        "check_generated_artifacts.py ARTIFACTS must include 'ROADMAP.md' so the "
        "drift check catches stale auto:operational-state blocks"
    )


def test_branch_protection_lists_all_required_checks():
    """docs/BRANCH_PROTECTION.md must match auto_merge_ingestion_pr.py:REQUIRED_CHECKS.

    The auto-merge script is the source of truth for what the auto-merger
    will block on. The doc currently lists 3 checks; the script enforces 8.
    """
    auto_merge = _auto_merge_module()
    expected = set(auto_merge.REQUIRED_CHECKS)
    doc_text = (REPO_ROOT / "docs" / "BRANCH_PROTECTION.md").read_text(encoding="utf-8")

    missing = [name for name in sorted(expected) if f"`{name}`" not in doc_text]
    assert not missing, (
        f"docs/BRANCH_PROTECTION.md missing required-check names: {missing}. "
        f"The doc must list every name in auto_merge_ingestion_pr.py:REQUIRED_CHECKS "
        f"({sorted(expected)})."
    )


def test_auto_merge_prefix_excludes_e20b_dispatch_branches():
    """HEAD_BRANCH_PREFIX must not accidentally match E20b dispatch PR branches.

    E20b (ingest-airtable-dispatch.yml) opens PRs on
    `ingest/airtable-record-<rec-id>` branches; those PRs are reviewed
    individually and must not be auto-merged by the cron's auto-merge step
    if someone flips AUTO_MERGE_INGESTION_PRS=1 with the wrong head branch
    set. Defense in depth even though title-match also gates this.
    """
    mod = _auto_merge_module()
    prefix = mod.HEAD_BRANCH_PREFIX
    # The cron branch is exactly 'ingest/airtable-articles'. The dispatch
    # branches look like 'ingest/airtable-record-recXXXXXXXXXXXXXX'.
    sample_dispatch = "ingest/airtable-record-recABCDEFGHIJKLMN"
    assert not sample_dispatch.startswith(prefix), (
        f"HEAD_BRANCH_PREFIX='{prefix}' would match E20b dispatch branch "
        f"'{sample_dispatch}'. Tighten the prefix to 'ingest/airtable-articles' "
        f"so only the cron workflow's PR can satisfy branch_matches()."
    )
    # And the legitimate cron branch must still match.
    assert "ingest/airtable-articles".startswith(prefix), (
        f"HEAD_BRANCH_PREFIX='{prefix}' must still match the cron's branch "
        f"'ingest/airtable-articles'"
    )


def test_ingest_airtable_exports_mcp_archive_data_before_pr():
    """The cron ingest workflow must rebuild
    `mcp-server/src/generated/archive-data.json` and include it in the
    PR before peter-evans/create-pull-request runs. Otherwise the
    Generated artifacts CI job fails on a real drift on every ingest
    PR (because `tools/check_generated_artifacts.py` runs
    `tools/export_mcp_data.py` and treats archive-data.json as one of
    the tracked artifacts), and `tools/auto_merge_ingestion_pr.py`
    blocks on `check=FAILURE` every cron run — the E41 doom loop.
    """
    wf = _load_yaml("ingest-airtable.yml")
    steps = wf["jobs"]["ingest"]["steps"]

    # 1. There is an explicit export step that runs tools/export_mcp_data.py.
    export_steps = [
        s for s in steps
        if "tools/export_mcp_data.py" in (s.get("run") or "")
    ]
    assert len(export_steps) == 1, (
        "ingest-airtable.yml must contain exactly one step that runs "
        f"`python3 tools/export_mcp_data.py`; found {len(export_steps)}"
    )
    export_step = export_steps[0]

    # 2. It is gated on the same write-mode + non-zero-created predicate as
    #    the rest of the rebuild pipeline. Otherwise dry-run cron runs or
    #    zero-created runs would invoke it pointlessly (and could mask a
    #    real archive-data drift that was actually present before the cron).
    condition = export_step.get("if") or ""
    assert "env.INGEST_DRY_RUN != '1'" in condition, (
        "Export-MCP step must be skipped in dry-run mode; got if: "
        + repr(condition)
    )
    assert "steps.ingest_summary.outputs.created != '0'" in condition, (
        "Export-MCP step must be skipped when no records were created; "
        "got if: " + repr(condition)
    )

    # 3. Ordering: the export step must come AFTER rebuild_local.py and
    #    update_docs.py (which feed it transitively via index.json) and
    #    BEFORE the `peter-evans/create-pull-request` PR-create step.
    step_names = [s.get("name") or s.get("uses") or "" for s in steps]

    def _index(predicate):
        for i, s in enumerate(steps):
            if predicate(s):
                return i
        return -1

    rebuild_idx = _index(
        lambda s: "tools/rebuild_local.py" in (s.get("run") or "")
    )
    update_docs_idx = _index(
        lambda s: "tools/update_docs.py" in (s.get("run") or "")
    )
    export_idx = steps.index(export_step)
    pr_idx = _index(
        lambda s: "peter-evans/create-pull-request" in (s.get("uses") or "")
    )

    assert rebuild_idx >= 0 and update_docs_idx >= 0 and pr_idx >= 0, (
        "ingest-airtable.yml must still contain rebuild_local.py, "
        "update_docs.py, and the peter-evans/create-pull-request step. "
        f"step names: {step_names}"
    )
    assert rebuild_idx < export_idx < pr_idx, (
        "Export-MCP step must run AFTER rebuild_local.py and BEFORE "
        f"peter-evans/create-pull-request. Got indices: rebuild={rebuild_idx}, "
        f"update_docs={update_docs_idx}, export_mcp={export_idx}, "
        f"create_pr={pr_idx}."
    )
    assert update_docs_idx < export_idx, (
        "Export-MCP step must run AFTER update_docs.py so the auto-state "
        "block in ROADMAP.md is current before the snapshot is taken. "
        f"Got indices: update_docs={update_docs_idx}, export_mcp={export_idx}."
    )

    # 4. The PR's add-paths list must include the generated archive-data.json
    #    so the file actually lands on the PR (otherwise the rebuild is run
    #    but the diff omits it and the Generated artifacts check still fails).
    pr_step = steps[pr_idx]
    add_paths_raw = (pr_step.get("with") or {}).get("add-paths") or ""
    add_paths = [line.strip() for line in str(add_paths_raw).splitlines() if line.strip()]
    assert "mcp-server/src/generated/archive-data.json" in add_paths, (
        "peter-evans/create-pull-request `add-paths:` must include "
        "`mcp-server/src/generated/archive-data.json` so the regenerated "
        f"MCP snapshot reaches the PR. Got: {add_paths!r}"
    )


def test_ingest_airtable_has_success_path_incident_cleanup():
    """A successful schedule-triggered cron-write run must close any open
    `E41 cron ingestion incident:` issues left by prior failed runs.

    Pairs with the existing failure-path "Open incident issue on cron-write
    failure" step. The cleanup step must be gated tightly enough that:
    - dry-run cron runs do not close anything (no archive impact);
    - workflow_dispatch runs do not close anything (operator-led
      investigation should resolve incidents manually);
    - failed runs do not close anything (success() gate);
    - only issues with the exact title prefix used by the failure-path step
      are eligible, so unrelated issues mentioning the phrase elsewhere are
      never touched.
    """
    wf = _load_yaml("ingest-airtable.yml")
    steps = wf["jobs"]["ingest"]["steps"]
    cleanup_steps = [
        s for s in steps
        if "Close" in s.get("name", "") and "incident" in s.get("name", "")
    ]
    assert len(cleanup_steps) == 1, (
        "ingest-airtable.yml must contain exactly one success-path incident "
        f"cleanup step; found {len(cleanup_steps)}"
    )
    step = cleanup_steps[0]
    condition = step.get("if", "")
    assert "success()" in condition, (
        f"cleanup step must be gated on success(); got: {condition!r}"
    )
    assert "schedule" in condition, (
        f"cleanup step must be restricted to schedule events; got: {condition!r}"
    )
    assert "INGEST_DRY_RUN" in condition, (
        f"cleanup step must skip dry-run mode; got: {condition!r}"
    )
    run_body = step.get("run") or ""
    assert "E41 cron ingestion incident:" in run_body, (
        "cleanup step must reference the exact failure-path title prefix so "
        "it cannot close unrelated issues"
    )
    assert "gh issue close" in run_body, (
        "cleanup step must use `gh issue close`"
    )

    # Token-scope tolerance — close-with-comment is preferred but the
    # cron token has been observed without `addComment` scope (run
    # 26708845288 on 2026-05-31). The cleanup step MUST fall back to a
    # bare close so the loop still drains the stale-issue backlog.
    assert "--comment" in run_body, (
        "cleanup step should prefer close-with-comment so the closing run "
        "is linked in-context"
    )
    bare_close_marker = 'gh issue close "$n" --repo "${GITHUB_REPOSITORY}"'
    assert bare_close_marker in run_body, (
        "cleanup step must have a bare `gh issue close` fallback for issues "
        "where the token cannot call addComment; expected literal "
        f"'{bare_close_marker}' but not found in the step body. See run "
        "26708845288 for the regression that motivates this fallback."
    )

    # Per-issue failures must be logged as warnings rather than propagated.
    assert "WARN:" in run_body, (
        "cleanup step must log warnings for per-issue close failures so the "
        "operator can sweep manually; expected at least one 'WARN:' marker."
    )

    # Step must always exit 0 — a cleanup-only failure must never turn a
    # successful cron into a failed cron and re-spawn the doom loop.
    assert run_body.rstrip().endswith("exit 0"), (
        "cleanup step must end with `exit 0` so a stale-issue close failure "
        "cannot cascade into `failure()` and trigger the failure-path "
        "incident step (the doom loop this cleanup is supposed to break). "
        "Got trailing: " + repr(run_body.rstrip()[-80:])
    )

    # Workflow permissions remain narrow. The cleanup step uses gh CLI with
    # the same PAT-or-GITHUB_TOKEN fallback as the failure-path step; we do
    # NOT widen workflow permissions to grant issues:write to GITHUB_TOKEN
    # — the operator owns the PAT scope decision separately.
    wf_perms = wf.get("permissions") or {}
    assert "issues" not in wf_perms, (
        "Workflow `permissions:` must not gain an `issues:` entry as part of "
        "the cleanup-step token-scope hardening; the fix is to tolerate "
        f"missing comment scope, not to widen workflow permissions. Got: {wf_perms!r}"
    )
