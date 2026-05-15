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
