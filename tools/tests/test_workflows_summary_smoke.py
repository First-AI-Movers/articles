"""Workflow-shape tests for .github/workflows/summary-automation-smoke.yml.

A new workflow gets NO automatic coverage — the existing test_workflows_ci_audit*
files are filename-pinned and none iterate WORKFLOWS.glob("*.yml") — so this file
pins the Envelope-2 smoke workflow's safety contract:

  * manual `workflow_dispatch` only (no schedule/push/pull_request/workflow_run/
    repository_dispatch);
  * top-level `permissions: contents: read` only, no elevated scopes;
  * NO `secrets.*` reference anywhere (decision D1 = no keys in CI);
  * static `concurrency.group`, no runtime expression spliced into a `run:` body;
  * a fail-closed presence gate with OpenAI REQUIRED and DeepSeek OPTIONAL (D7);
  * a no-network / no-write dry-run shape check that can never go live;
  * no PR/push/add-paths/artifact-upload/env-dump steps.

Pure YAML parsing — no execution.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
WF_NAME = "summary-automation-smoke.yml"
WF_PATH = WORKFLOWS / WF_NAME


def _load(name: str) -> dict:
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


def _wf() -> dict:
    return _load(WF_NAME)


def _on(wf: dict) -> dict:
    # PyYAML 1.1 parses a bare `on:` key as boolean True.
    return wf.get("on") or wf.get(True)


def _steps(wf: dict) -> list:
    return wf["jobs"]["smoke"]["steps"]


def _run_bodies(wf: dict) -> list:
    return [s["run"] for s in _steps(wf) if "run" in s]


def _norm(run: str) -> str:
    """Collapse shell line-continuations + whitespace into a single spaced line."""
    return " ".join(run.replace("\\", " ").split())


def _tokens_between(norm: str, start: str, *stops: str) -> list:
    parts = norm.split()
    if start not in parts:
        return []
    out = []
    i = parts.index(start) + 1
    while i < len(parts) and parts[i] not in stops:
        out.append(parts[i])
        i += 1
    return out


# --------------------------------------------------------------------------
# Trigger / permissions / concurrency
# --------------------------------------------------------------------------


def test_workflow_file_exists():
    assert WF_PATH.exists(), f"{WF_NAME} must exist"


def test_trigger_is_workflow_dispatch_only():
    on = _on(_wf())
    assert isinstance(on, dict), "`on` must parse to a dict"
    assert "workflow_dispatch" in on, "smoke must be operator-dispatchable"
    for forbidden in ("schedule", "push", "pull_request", "workflow_run", "repository_dispatch"):
        assert forbidden not in on, f"smoke must NOT declare a `{forbidden}` trigger"


def test_permissions_are_contents_read_only():
    perms = _wf().get("permissions") or {}
    assert perms == {"contents": "read"}, (
        f"top-level permissions must be exactly {{contents: read}}; got {perms!r}"
    )


def test_no_elevated_permission_scopes():
    perms = _wf().get("permissions") or {}
    for scope in ("pull-requests", "issues", "id-token", "packages", "deployments", "actions"):
        assert scope not in perms, f"smoke must not request `{scope}` permission"
    assert perms.get("contents") != "write", "smoke must never request contents: write"


def test_static_concurrency_group():
    c = _wf().get("concurrency")
    assert isinstance(c, dict) and "group" in c, "smoke must declare a concurrency.group"
    assert "${{" not in str(c["group"]), "concurrency.group must be a static string"
    assert c.get("cancel-in-progress") is False, "cancel-in-progress must be false"


def test_single_smoke_job_on_ubuntu():
    wf = _wf()
    assert "smoke" in wf["jobs"], "expected a `smoke` job"
    assert wf["jobs"]["smoke"]["runs-on"] == "ubuntu-latest"


# --------------------------------------------------------------------------
# Secret-safety / injection hardening
# --------------------------------------------------------------------------


def test_no_secrets_referenced_anywhere():
    # D1 = no-keys-in-CI: the smoke must not REFERENCE any GitHub Actions secret.
    # (Documentation prose may mention the word "secret"; the test targets the
    # actual reference form `${{ secrets... }}` and any env: that sources one.)
    text = WF_PATH.read_text(encoding="utf-8")
    assert "${{ secrets" not in text and "${{secrets" not in text, (
        "smoke must not reference any GitHub Actions secret expression (D1)"
    )
    for step in _steps(_wf()):
        for value in (step.get("env") or {}).values():
            assert "secrets." not in str(value), (
                f"step env: must not source a GitHub Actions secret; got {value!r}"
            )


def test_no_expression_interpolation_in_run_bodies():
    joined = "\n".join(_run_bodies(_wf()))
    assert "${{" not in joined, "no GitHub Actions expression may be spliced into a run: body"


def test_no_env_dump_steps():
    for body in _run_bodies(_wf()):
        assert not re.search(r"(^|\s|;|&&|\|)(printenv|env)(\s|$)", body), f"no env dump: {body!r}"
        assert "set -x" not in body, f"no `set -x` env echo: {body!r}"
        assert "env | " not in body and "| env" not in body, f"no env pipe: {body!r}"


def test_no_pr_push_or_add_paths():
    wf = _wf()
    for step in _steps(wf):
        assert not str(step.get("uses", "")).startswith("peter-evans/create-pull-request"), (
            "smoke must not open a pull request"
        )
    joined = "\n".join(_run_bodies(wf))
    for forbidden in ("git add", "git commit", "git push", "--add-paths"):
        assert forbidden not in joined, f"smoke must not `{forbidden}`"


def test_no_artifact_upload():
    # A2 decision: no artifact upload by default.
    for step in _steps(_wf()):
        assert not str(step.get("uses", "")).startswith("actions/upload-artifact"), (
            "A2 smoke uploads no artifact by default"
        )


# --------------------------------------------------------------------------
# Action pins / runtime
# --------------------------------------------------------------------------


@pytest.mark.parametrize("prefix,pin", [
    ("actions/checkout", "@v7"),
    ("actions/setup-python", "@v7"),
    ("actions/upload-artifact", "@v7"),  # vacuously true if absent (it is, per above)
])
def test_action_pins_are_repo_consistent(prefix, pin):
    for step in _steps(_wf()):
        uses = str(step.get("uses", ""))
        if uses.startswith(prefix):
            assert uses.endswith(pin), f"{prefix} must be pinned {pin}; got {uses}"


def test_setup_python_reads_canonical_declaration():
    for step in _steps(_wf()):
        if str(step.get("uses", "")).startswith("actions/setup-python"):
            selector = step.get("with") or {}
            assert selector.get("python-version-file") == ".python-version"
            assert "python-version" not in selector
            return
    pytest.fail("no actions/setup-python step found")


# --------------------------------------------------------------------------
# Step A — presence gate
# --------------------------------------------------------------------------


def _presence_run(wf: dict) -> str:
    runs = [r for r in _run_bodies(wf) if "tools/check_provider_keys_present.py" in r]
    assert len(runs) == 1, f"expected exactly one presence-helper invocation; got {len(runs)}"
    return _norm(runs[0])


def test_presence_helper_requires_the_three_keys_incl_openai():
    required = _tokens_between(_presence_run(_wf()), "--required", "--optional")
    for key in ("MINIMAX_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        assert key in required, f"{key} must be in the helper's --required set"


def test_presence_helper_treats_deepseek_as_optional():
    run = _presence_run(_wf())
    required = _tokens_between(run, "--required", "--optional")
    optional = _tokens_between(run, "--optional")
    assert "DEEPSEEK_API_KEY" not in required, "DeepSeek must NOT be required (D7: optional)"
    assert "DEEPSEEK_API_KEY" in optional, "DeepSeek must be reported as an optional key"


# --------------------------------------------------------------------------
# Step B — dry-run shape (non-live, non-mutating)
# --------------------------------------------------------------------------


def _runner_run(wf: dict) -> str:
    runs = [r for r in _run_bodies(wf) if "tools/run_summary_batch.py" in r]
    assert len(runs) == 1, f"expected exactly one run_summary_batch.py invocation; got {len(runs)}"
    return runs[0]


def test_runner_invocation_is_non_live():
    run = _runner_run(_wf())
    for forbidden in ("--allow-network", "--apply-auto-approved", "--max-budget-usd"):
        assert forbidden not in run, f"dry-run shape must not pass {forbidden}"


def test_runner_invocation_passes_dry_run():
    assert "--dry-run" in _runner_run(_wf()), (
        "runner must be invoked with --dry-run (belt-and-suspenders non-live)"
    )


def test_runner_report_path_is_out_of_repo():
    run = _runner_run(_wf())
    assert "--report-path" in run, "runner must set an explicit --report-path"
    assert "RUNNER_TEMP" in run or "runner.temp" in run, (
        "report path must be the runner temp dir (outside the repo working tree)"
    )
