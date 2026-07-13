"""Parity guard: all three ingestion workflows honour the generated-artifact contract.

The daily cron (ingest-airtable.yml), the record dispatch
(ingest-airtable-dispatch.yml), and the external push (ingest-article.yml) all
open a PR that adds an article and must therefore run the SAME deterministic
rebuild chain and ship the SAME tracked generated artifacts — otherwise the
Generated artifacts `check` job fails on drift for whichever path skipped a step.

`check_generated_artifacts.ARTIFACTS` tracks `ROADMAP.md`, `llms-index.txt`, and
`mcp-server/src/generated/archive-data.json` (among others); those are produced
by `update_docs.py` (ROADMAP) and `export_mcp_data.py` (archive-data.json), so
every ingestion path must run both and list all three in `add-paths`.
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
    for tool in ("rebuild_local.py", "update_docs.py", "export_mcp_data.py"):
        assert tool in blob, (
            f"{wf_name}'s ingest job must run {tool} so its PR's generated "
            f"artifacts stay in lockstep with check_generated_artifacts.py "
            f"(else the Generated artifacts `check` job fails on drift)."
        )


@pytest.mark.parametrize("wf_name", INGESTION_WORKFLOWS)
def test_ingestion_add_paths_cover_tracked_artifacts(wf_name):
    add_paths = _add_paths(_wf(wf_name))
    for path in ("ROADMAP.md", "llms-index.txt", "mcp-server/src/generated/archive-data.json"):
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
