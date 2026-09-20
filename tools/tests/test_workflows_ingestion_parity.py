"""Parity guard: all three ingestion workflows honour the generated-artifact contract.

The daily cron (ingest-airtable.yml), the record dispatch
(ingest-airtable-dispatch.yml), and the external push (ingest-article.yml) all
open a PR that adds an article and must therefore run the SAME deterministic
rebuild chain and ship the SAME tracked generated artifacts — otherwise the
Generated artifacts `check` job fails on drift for whichever path skipped a step.

`check_generated_artifacts.ARTIFACTS` tracks `llms-index.txt` and
`mcp-server/src/generated/archive-data.json` (among others); the latter is
produced by `export_mcp_data.py`, so every ingestion path must run the rebuild
chain and list both in `add-paths`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"

INGESTION_WORKFLOWS = [
    "ingest-airtable.yml",
    "ingest-airtable-dispatch.yml",
    "ingest-article.yml",
]


def _wf(name: str) -> dict:
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


def _steps(wf: dict) -> list[dict]:
    return wf["jobs"]["ingest"]["steps"]


def _run_blob(wf: dict) -> str:
    return "\n".join(str(s.get("run", "")) for s in _steps(wf))


def _add_paths(wf: dict) -> str:
    for s in _steps(wf):
        if "peter-evans/create-pull-request" in str(s.get("uses", "")):
            return str((s.get("with") or {}).get("add-paths", ""))
    return ""


@pytest.mark.parametrize("wf_name", INGESTION_WORKFLOWS)
def test_ingestion_runs_full_rebuild_chain(wf_name):
    blob = _run_blob(_wf(wf_name))
    for tool in ("rebuild_local.py", "export_mcp_data.py"):
        assert tool in blob, (
            f"{wf_name}'s ingest job must run {tool} so its PR's generated "
            f"artifacts stay in lockstep with check_generated_artifacts.py "
            f"(else the Generated artifacts `check` job fails on drift)."
        )


@pytest.mark.parametrize("wf_name", INGESTION_WORKFLOWS)
def test_ingestion_add_paths_cover_tracked_artifacts(wf_name):
    add_paths = _add_paths(_wf(wf_name))
    for path in ("llms-index.txt", "mcp-server/src/generated/archive-data.json"):
        assert path in add_paths, (
            f"{wf_name}'s create-pull-request `add-paths:` must include {path}; "
            f"it is tracked by check_generated_artifacts.ARTIFACTS, so omitting "
            f"it lands stale committed artifacts and fails the drift check."
        )


@pytest.mark.parametrize("wf_name", INGESTION_WORKFLOWS)
def test_ingestion_shares_concurrency_group(wf_name):
    conc = _wf(wf_name).get("concurrency")
    assert isinstance(conc, dict) and conc.get("group") == "ingest-airtable", (
        f"{wf_name} must share the `ingest-airtable` concurrency group so the "
        f"three ingestion paths cannot run concurrently and race on the shared "
        f"rebuild output; got {conc!r}."
    )


GATE_WORKFLOWS = [
    "ingest-airtable.yml",
    "audit-airtable-reconciliation.yml",
    "recover-airtable-backlog.yml",
]
GATE_EXPR = "${{ vars.ARCHIVE_ELIGIBILITY_GATE || 'status' }}"
# A per-run dispatch override is allowed ONLY on a read-only workflow that declares the
# input: it exists so the receipt delta can be measured without flipping the repository
# variable, and it must never reach a workflow that can write to the archive.
GATE_EXPR_WITH_OVERRIDE = "${{ inputs.eligibility_gate || vars.ARCHIVE_ELIGIBILITY_GATE || 'status' }}"


def _on(wf: dict) -> dict:
    return wf.get("on") or wf.get(True) or {}   # PyYAML reads a bare `on:` key as True


def _is_read_only(wf: dict) -> bool:
    perms = wf.get("permissions") or {}
    writes_content = perms.get("contents") == "write" or perms.get("pull-requests") == "write"
    publishes = any(
        "create-pull-request" in str(s.get("uses") or "")
        for job in (wf.get("jobs") or {}).values()
        for s in (job.get("steps") or [])
    )
    return not writes_content and not publishes


@pytest.mark.parametrize("wf_name", GATE_WORKFLOWS)
def test_eligibility_gate_is_passed_identically_to_every_tool(wf_name):
    """The three tools decide eligibility through one shared function that reads
    ARCHIVE_ELIGIBILITY_GATE. If one workflow forgot to pass the repository variable,
    that tool would silently run the `status` gate while the others ran `receipt`
    -- the reconciler and the ingestion path would disagree about the same record.
    The default is `status` on purpose (ADR: the rollback position), so flipping the
    repository variable is the only cut-over and unsetting it is the rollback. The
    read-only reconciliation may additionally take a per-run dispatch override; a
    workflow that can publish may not."""
    wf = _wf(wf_name)
    env = wf.get("env") or {}
    got = env.get("ARCHIVE_ELIGIBILITY_GATE")
    inputs = ((_on(wf).get("workflow_dispatch") or {}) or {}).get("inputs") or {}
    if "eligibility_gate" in inputs:
        assert _is_read_only(wf), (
            f"{wf_name} declares an eligibility_gate override but can write to the archive; "
            "an override is only ever allowed on a read-only report"
        )
        assert got == GATE_EXPR_WITH_OVERRIDE, (
            f"{wf_name} declares the override input, so it must read it first: "
            f"expected {GATE_EXPR_WITH_OVERRIDE!r}, got {got!r}"
        )
    else:
        assert got == GATE_EXPR, (
            f"{wf_name} must pass ARCHIVE_ELIGIBILITY_GATE at workflow level as {GATE_EXPR!r}; "
            f"got {got!r}"
        )
