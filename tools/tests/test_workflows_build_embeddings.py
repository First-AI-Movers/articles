"""Workflow-shape tests for build-embeddings.yml.

The weekly embeddings refresh ran red 11/11 with no signal: it declared
`permissions: contents: read` but runs peter-evans/create-pull-request,
which needs write on contents + pull-requests. These tests pin the repair
so the regression cannot recur silently.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
WF = REPO_ROOT / ".github" / "workflows" / "build-embeddings.yml"


def _load() -> dict:
    return yaml.safe_load(WF.read_text(encoding="utf-8"))


def _steps() -> list[dict]:
    return _load()["jobs"]["build"]["steps"]


def test_permissions_allow_pr_creation():
    perms = _load().get("permissions") or {}
    assert perms.get("contents") == "write", (
        f"build-embeddings.yml must grant `contents: write` for "
        f"create-pull-request to push a branch; got {perms!r}"
    )
    assert perms.get("pull-requests") == "write", (
        f"build-embeddings.yml must grant `pull-requests: write` for "
        f"create-pull-request to open the PR; got {perms!r}"
    )


def test_has_concurrency_group():
    conc = _load().get("concurrency")
    assert isinstance(conc, dict) and conc.get("group"), (
        f"build-embeddings.yml must declare a concurrency group so scheduled "
        f"and manual runs do not race the shared refresh branch; got {conc!r}"
    )


def test_pr_step_uses_ci_triggering_token():
    """The create-pull-request step must prefer ARTICLE_INGESTION_PR_TOKEN so
    the opened PR triggers downstream CI (the default GITHUB_TOKEN suppresses it)."""
    pr_steps = [
        s for s in _steps()
        if isinstance(s.get("uses"), str) and s["uses"].startswith("peter-evans/create-pull-request")
    ]
    assert len(pr_steps) == 1, f"expected exactly one create-pull-request step, got {len(pr_steps)}"
    token = str(pr_steps[0].get("with", {}).get("token", ""))
    assert "ARTICLE_INGESTION_PR_TOKEN" in token, (
        f"create-pull-request token must prefer ARTICLE_INGESTION_PR_TOKEN so "
        f"the PR triggers CI; got {token!r}"
    )


def test_pr_add_paths_scoped_to_embeddings():
    pr_steps = [
        s for s in _steps()
        if isinstance(s.get("uses"), str) and s["uses"].startswith("peter-evans/create-pull-request")
    ]
    add_paths = str(pr_steps[0].get("with", {}).get("add-paths", ""))
    assert "embeddings.parquet" in add_paths, (
        f"create-pull-request add-paths must scope the commit to embeddings.parquet; "
        f"got {add_paths!r}"
    )


def test_scheduled_failure_opens_incident():
    """A scheduled failure must open an operator-visible incident (the prior
    silent-red state had no signal). The step must be gated on failure()."""
    incident_steps = [
        s for s in _steps()
        if "failure()" in str(s.get("if", "")) and "gh issue create" in str(s.get("run", ""))
    ]
    assert incident_steps, (
        "build-embeddings.yml must open a deduplicated incident issue on "
        "scheduled failure so a silent weekly breakage is surfaced"
    )
    assert "schedule" in str(incident_steps[0].get("if", "")), (
        "the incident step should fire only on scheduled failures "
        "(manual dispatch failures are left for the triggering operator)"
    )
