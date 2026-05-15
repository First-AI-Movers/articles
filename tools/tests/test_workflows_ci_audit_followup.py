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
