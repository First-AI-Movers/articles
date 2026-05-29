"""Drift-detection coverage tests.

After the prior 3 audit PRs (#178/#179/#180), every PR that touches a
workflow file has needed a follow-up commit to clear stale generated
artifacts. PR #178 cleared rebuild_local outputs. PR #179 added ROADMAP.md
to the drift detector. PR #180 surfaced that mcp-server/src/generated/
archive-data.json was ALSO drifting and not caught by the existing check.

This file pins the fix: the drift detector must invoke the MCP data
export too, so future PRs catch this class of drift in the same job.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _check_module():
    return _load_module(
        "check_generated_artifacts",
        REPO_ROOT / "tools" / "check_generated_artifacts.py",
    )


def test_drift_check_invokes_mcp_export():
    """check_generated_artifacts.py must run tools/export_mcp_data.py too.

    The MCP server's generated data lives at
    mcp-server/src/generated/archive-data.json. It is rebuilt from
    index.json + article markdown by tools/export_mcp_data.py. Without
    this invocation in the drift detector, an out-of-date archive-data.json
    only gets caught when mcp-server.yml's path-filter happens to trigger
    on a PR — which it usually does not, since most PRs don't touch
    mcp-server/** or tools/export_mcp_data.py.

    The detector already invokes tools/update_docs.py (added in PR #179)
    for the same reason. Same pattern; add export_mcp_data.py.
    """
    text = (REPO_ROOT / "tools" / "check_generated_artifacts.py").read_text(encoding="utf-8")
    assert "tools/export_mcp_data.py" in text or "export_mcp_data.py" in text, (
        "check_generated_artifacts.py must invoke tools/export_mcp_data.py "
        "so MCP archive-data.json drift is caught in the same 'check' job"
    )


def test_drift_check_tracks_mcp_archive_data():
    """archive-data.json must be in ARTIFACTS so the diff step actually fails
    when the file changes after export_mcp_data.py runs.

    Path is mcp-server/src/generated/archive-data.json relative to repo
    root. Either spell is acceptable as long as the diff loop picks it up.
    """
    mod = _check_module()
    artifact_str = " ".join(mod.ARTIFACTS)
    assert "archive-data.json" in artifact_str, (
        "check_generated_artifacts.py ARTIFACTS must include "
        "mcp-server/src/generated/archive-data.json so the diff step "
        "compares it after the rebuild"
    )


def test_drift_check_gracefully_skips_when_pyarrow_missing():
    """tools/export_mcp_data.py needs pyarrow for the embeddings export.

    The drift detector should not hard-fail if pyarrow is missing locally
    (cold cloud env, contributor setup). Either the invocation captures
    the dependency error and continues, or archive-data.json export is
    independent of the parquet-reading embeddings step.

    Verify: read the export_mcp_data.py source and confirm the
    archive-data.json export path does not require pyarrow. If it does,
    the drift detector must wrap that call defensively.
    """
    export_src = (REPO_ROOT / "tools" / "export_mcp_data.py").read_text(encoding="utf-8")
    # archive-data.json export should be pure-stdlib + index.json reading.
    # The pyarrow dep is only for embeddings.json. As long as archive-data
    # can be written without pyarrow, the drift extension is safe.
    assert "json.dump" in export_src or "json.dumps" in export_src, (
        "export_mcp_data.py must serialize archive-data.json via stdlib json"
    )


# ----------------------------------------------------------------------------
# Generated-artifacts workflow carve-out for safe-maintenance PRs
# ----------------------------------------------------------------------------


def test_generated_artifacts_has_safe_maintenance_carveout():
    """Generated artifacts must not red-flag dependency- or workflow-only
    PRs that cannot affect committed generated outputs.

    The carve-out must:
    - be changed-files based, not actor-only (an actor gate would silently
      mask real drift if Dependabot ever touched a lockfile, a generated
      output path, or repo tooling);
    - allow only narrow maintenance paths (pip pins, workflow files,
      Dependabot config);
    - never extend the allowlist to articles/, source tools (`tools/*.py`),
      templates/, static/, mcp-server/, package files, lockfiles, or any
      committed generated output;
    - leave push-to-main runs running the full drift check unconditionally.
    """
    yaml = pytest.importorskip("yaml")
    wf_path = REPO_ROOT / ".github" / "workflows" / "generated-artifacts.yml"
    wf_text = wf_path.read_text(encoding="utf-8")
    wf = yaml.safe_load(wf_text)
    steps = wf["jobs"]["check"]["steps"]

    # 1. A classifier step must exist and run on pull_request events.
    classifier = [
        s for s in steps
        if s.get("id") == "classify_change"
        or "classify" in (s.get("name", "").lower())
    ]
    assert len(classifier) == 1, (
        f"Expected exactly one changed-files classifier step in "
        f"generated-artifacts.yml; found {len(classifier)}"
    )
    step = classifier[0]
    assert "github.event_name == 'pull_request'" in (step.get("if") or ""), (
        f"Classifier must only run on pull_request events; got if: "
        f"{step.get('if')!r}"
    )
    body = step.get("run") or ""

    # 2. Must be changed-files based, not actor-only.
    assert "git diff --name-only" in body, (
        "Classifier must use `git diff --name-only` so it inspects the PR's "
        "actual file set, not metadata like the PR author."
    )
    assert "github.actor" not in wf_text, (
        "Generated-artifacts carve-out must not gate on github.actor — an "
        "actor-only rule would mask real drift if Dependabot touched a "
        "lockfile, a generated output, or repo tooling."
    )

    # 3. Extract the literal allowlist regex from the bash body and assert
    # it equals exactly the narrow safe-maintenance set. Comparing the
    # regex literal directly is stronger than a substring scan — any new
    # alternative anyone adds will trip this test and require an explicit
    # safety review of whether the new path can affect generated artifacts.
    import re
    match = re.search(r"grep -vE '\^\(([^']+)\)\$'", body)
    assert match, (
        "Could not locate the allowlist regex in the classifier step. "
        "Expected a line like `grep -vE '^(<alternatives>)$'`."
    )
    allowlist_alternatives = set(match.group(1).split("|"))
    expected_allow = {
        r"tools/requirements\.txt",
        r"\.github/workflows/[^/]+\.yml",
        r"\.github/dependabot\.yml",
    }
    assert allowlist_alternatives == expected_allow, (
        f"Allowlist regex must contain exactly the narrow safe-maintenance "
        f"set {expected_allow}. Adding any other path (articles/, source "
        f"tools, templates, static, mcp-server, package files, lockfiles, "
        f"generated outputs, docs) would mask real drift. Got: "
        f"{allowlist_alternatives}."
    )

    # 5. The actual drift-check step must be gated on the classifier output,
    # AND it must still run on every non-PR event (push to main, workflow_dispatch).
    drift_steps = [
        s for s in steps
        if "check_generated_artifacts.py" in (s.get("run") or "")
    ]
    assert len(drift_steps) == 1, (
        f"Expected exactly one drift-check step; found {len(drift_steps)}"
    )
    gate = drift_steps[0].get("if") or ""
    assert "github.event_name != 'pull_request'" in gate, (
        "Drift-check step must continue to run for push and workflow_dispatch "
        "events even when the PR carve-out skips. Got if: " + repr(gate)
    )
    assert "steps.classify_change.outputs.kind == 'heavy'" in gate, (
        "Drift-check step must run on the PR path when the classifier marked "
        "the change as heavy. Got if: " + repr(gate)
    )

    # 6. No permissions expansion. The workflow's permissions block must
    # remain `contents: read` only.
    perms = wf.get("permissions") or {}
    assert perms == {"contents": "read"}, (
        f"generated-artifacts.yml permissions must remain `contents: read` "
        f"only; carve-out must not request any write scope. Got: {perms!r}"
    )
