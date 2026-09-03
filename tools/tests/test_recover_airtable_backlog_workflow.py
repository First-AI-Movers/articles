#!/usr/bin/env python3
"""Shape/invariant tests for .github/workflows/recover-airtable-backlog.yml.

Pins the guarantees that make the backlog-recovery workflow safe on a public
repo: dispatch-only, full rebuild chain (artifact parity), tracked-artifact
add-paths, a public-surface secret scan, and — critically — NO auto-merge and
NO summary generation.
"""

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

WF_PATH = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "recover-airtable-backlog.yml"


@pytest.fixture(scope="module")
def wf():
    return yaml.safe_load(WF_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def text():
    return WF_PATH.read_text(encoding="utf-8")


def _on(wf):
    # PyYAML parses the bare `on:` key as the boolean True.
    return wf.get("on") or wf.get(True)


def test_dispatch_only_no_schedule(wf):
    on = _on(wf)
    assert "workflow_dispatch" in on
    assert "schedule" not in on, "recovery is operator/AI-driven; no cron"
    inputs = on["workflow_dispatch"]["inputs"]
    assert {"batch_number", "batch_size", "apply"} <= set(inputs)
    assert inputs["apply"]["default"] == "false", "must default to dry-run"


def test_permissions(wf):
    """GITHUB_TOKEN is checkout-only here; the branch push and PR use the App token (#388)."""
    perms = wf.get("permissions", {})
    assert perms.get("contents") == "read", (
        f"GITHUB_TOKEN needs only `contents: read` — checkout runs with "
        f"`persist-credentials: false` and create-pull-request uses the App token. Got {perms!r}"
    )
    assert perms.get("pull-requests") != "write", (
        f"GITHUB_TOKEN must not hold `pull-requests: write`; the App token opens the PR. "
        f"Got {perms!r}"
    )


def test_concurrency_serialized(wf):
    assert wf.get("concurrency", {}).get("group")


def _steps(wf):
    return wf["jobs"]["recover"]["steps"]


def test_runs_recovery_tool(text):
    assert "tools/recover_airtable_backlog.py" in text


def test_full_rebuild_chain_present(text):
    for tool in (
        "tools/normalize_tags.py",
        "tools/check_duplicate_titles.py",
        "tools/rebuild_local.py",
        "tools/update_docs.py",
        "tools/export_mcp_data.py",
    ):
        assert tool in text, f"rebuild chain missing {tool}"


def test_add_paths_cover_tracked_artifacts(text):
    for art in (
        "articles/*",
        "index.json",
        "sitemap.xml",
        "llms-index.txt",
        "ROADMAP.md",
        "mcp-server/src/generated/archive-data.json",
    ):
        assert art in text, f"add-paths missing {art}"


def test_opens_pr_with_token_fallback(text):
    assert "peter-evans/create-pull-request@v8" in text
    assert "ARTICLE_INGESTION_PR_TOKEN" in text and "GITHUB_TOKEN" in text


def test_branch_and_title_use_batch_number(text):
    assert "backfill/airtable-posted-batch-${{ inputs.batch_number }}" in text
    assert "recover missed Airtable batch ${{ inputs.batch_number }}" in text


def test_public_surface_scan_present(text):
    assert "Public-surface safety scan" in text
    assert "AIRTABLE_BASE_ID" in text and "grep -rqIF" in text


def test_no_auto_merge(text):
    assert "auto_merge_ingestion_pr" not in text, "recovery must not auto-merge"
    assert "gh pr merge" not in text
    assert "--auto" not in text


def test_no_summary_generation(text):
    for banned in ("summary_apply", "generate_summaries", "summarize", "summary-auto"):
        assert banned not in text, f"recovery must not generate summaries ({banned})"


def test_dry_run_and_apply_are_mutually_gated(text):
    assert "inputs.apply != 'true'" in text  # dry-run step
    assert "inputs.apply == 'true'" in text  # apply step
