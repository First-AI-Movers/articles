"""Contracts for the repository's canonical Python 3.14 runtime.

Two halves. The first asserts the repository's own state. The second is a set of
negative controls against synthetic repositories, proving the drift guard in
`tools/check_python_runtime_drift.py` actually *fails* when a retired default
returns — a guard that has never been observed failing proves nothing.
"""

from __future__ import annotations

import datetime as dt
import sys
import textwrap
from pathlib import Path

import pytest
import yaml

import check_python_runtime_drift as guard

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_PYTHON = "3.14"
TEMPLATE_ROOT = REPO_ROOT / "cookiecutter-archive-template" / "{{cookiecutter.repo_slug}}"


def _setup_python_steps(workflow_dir: Path) -> list[tuple[Path, dict]]:
    steps: list[tuple[Path, dict]] = []
    for workflow in sorted(workflow_dir.glob("*.y*ml")):
        document = yaml.safe_load(workflow.read_text(encoding="utf-8")) or {}
        for job in (document.get("jobs") or {}).values():
            for step in job.get("steps") or []:
                if str(step.get("uses", "")).startswith("actions/setup-python@"):
                    steps.append((workflow, step))
    return steps


# --------------------------------------------------------------------------
# This repository's declared state
# --------------------------------------------------------------------------


def test_python_version_declaration_is_canonical() -> None:
    declaration = (REPO_ROOT / ".python-version").read_text(encoding="utf-8").strip()
    assert declaration == CANONICAL_PYTHON


def test_test_process_uses_canonical_python() -> None:
    assert sys.version_info[:2] == (3, 14), (
        "the canonical test process must run on Python 3.14; "
        f"got {sys.version_info.major}.{sys.version_info.minor}"
    )


def test_all_setup_python_steps_read_the_declaration() -> None:
    steps = _setup_python_steps(REPO_ROOT / ".github" / "workflows")
    assert steps, "no actions/setup-python steps found"
    for workflow, step in steps:
        selector = step.get("with") or {}
        assert selector.get("python-version-file") == ".python-version", (
            f"{workflow.relative_to(REPO_ROOT)} must read .python-version"
        )
        assert "python-version" not in selector, (
            f"{workflow.relative_to(REPO_ROOT)} must not hardcode python-version"
        )


def test_cookiecutter_template_ships_the_canonical_declaration() -> None:
    """A repo generated from the template must not start on a retired default."""
    declaration = TEMPLATE_ROOT / ".python-version"
    assert declaration.is_file(), "the template must ship a .python-version"
    assert declaration.read_text(encoding="utf-8").strip() == CANONICAL_PYTHON


def test_template_setup_python_steps_read_the_declaration() -> None:
    steps = _setup_python_steps(TEMPLATE_ROOT / ".github" / "workflows")
    assert steps, "no actions/setup-python steps found in the template"
    for workflow, step in steps:
        selector = step.get("with") or {}
        assert selector.get("python-version-file") == ".python-version", (
            f"{workflow.name} must read .python-version"
        )
        assert "python-version" not in selector, (
            f"{workflow.name} must not hardcode python-version"
        )


def test_numpy_is_not_capped_for_the_retired_python_311_baseline() -> None:
    requirements = (REPO_ROOT / "tools" / "requirements.txt").read_text(
        encoding="utf-8"
    )
    numpy_line = next(
        line for line in requirements.splitlines() if line.startswith("numpy")
    )
    assert "<2.5" not in numpy_line
    assert "Python 3.11" not in numpy_line


def test_dependabot_does_not_ignore_current_numpy_releases() -> None:
    dependabot = yaml.safe_load(
        (REPO_ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    )
    pip_updates = next(
        update
        for update in dependabot["updates"]
        if update.get("package-ecosystem") == "pip"
    )
    ignored = {
        item.get("dependency-name") for item in (pip_updates.get("ignore") or [])
    }
    assert "numpy" not in ignored


def test_drift_guard_is_clean_on_this_repository() -> None:
    findings = guard.check(REPO_ROOT)
    assert findings == [], "\n".join(str(f) for f in findings)


# --------------------------------------------------------------------------
# Negative controls — each lane must be observed failing
# --------------------------------------------------------------------------


def _synthetic_repo(root: Path, workflow: str) -> Path:
    """A minimal repo the guard passes, so each mutation below is the only change."""
    (root / ".python-version").write_text("3.14\n", encoding="utf-8")
    workflows = root / ".github" / "workflows"
    workflows.mkdir(parents=True, exist_ok=True)
    (workflows / "ci.yml").write_text(textwrap.dedent(workflow), encoding="utf-8")
    return root


_CLEAN_WORKFLOW = """\
name: ci
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v7
        with:
          python-version-file: .python-version
"""


def test_control_a_clean_synthetic_repo_passes(tmp_path: Path) -> None:
    """The baseline must pass, or every mutation below would be a false positive."""
    _synthetic_repo(tmp_path, _CLEAN_WORKFLOW)
    assert guard.check(tmp_path) == []


def test_control_b_missing_declaration_is_caught(tmp_path: Path) -> None:
    _synthetic_repo(tmp_path, _CLEAN_WORKFLOW)
    (tmp_path / ".python-version").unlink()
    lanes = {f.lane for f in guard.check(tmp_path)}
    assert "declaration" in lanes


@pytest.mark.parametrize("retired", ["3.11", "3.12", "3.13"])
def test_control_c_inline_pin_is_caught(tmp_path: Path, retired: str) -> None:
    """A workflow that bypasses the declaration must fail, for every retired series."""
    _synthetic_repo(
        tmp_path,
        f"""\
        name: ci
        on: [push]
        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/setup-python@v7
                with:
                  python-version: '{retired}'
        """,
    )
    findings = guard.check(tmp_path)
    lanes = {f.lane for f in findings}
    assert "workflow-selector" in lanes, findings
    assert "retired-literal" in lanes, findings


def test_control_d_setup_python_v6_cannot_silently_return(tmp_path: Path) -> None:
    """An older action that omits the selector entirely must not pass."""
    _synthetic_repo(
        tmp_path,
        """\
        name: ci
        on: [push]
        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/setup-python@v6
        """,
    )
    findings = guard.check(tmp_path)
    assert any(f.lane == "workflow-selector" for f in findings), findings


def test_control_e_retired_literal_in_tooling_is_caught(tmp_path: Path) -> None:
    _synthetic_repo(tmp_path, _CLEAN_WORKFLOW)
    tools = tmp_path / "tools"
    tools.mkdir()
    (tools / "run.py").write_text(
        'CMD = ["python3.11", "-m", "pytest"]\n', encoding="utf-8"
    )
    findings = guard.check(tmp_path)
    assert any(f.lane == "retired-literal" for f in findings), findings


def test_control_f_contributor_directive_is_caught(tmp_path: Path) -> None:
    _synthetic_repo(tmp_path, _CLEAN_WORKFLOW)
    (tmp_path / "CONTRIBUTING.md").write_text(
        "## Setup\n\nInstall Python 3.11 before creating the virtual environment.\n",
        encoding="utf-8",
    )
    findings = guard.check(tmp_path)
    assert any(f.lane == "contributor-directive" for f in findings), findings


def test_control_f2_stale_docs_directive_is_caught(tmp_path: Path) -> None:
    """A stale operations doc still telling a contributor to use 3.12 must fail."""
    _synthetic_repo(tmp_path, _CLEAN_WORKFLOW)
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "OPERATIONS.md").write_text(
        "Install Python 3.12 to run the pipeline.\n", encoding="utf-8"
    )
    findings = guard.check(tmp_path)
    assert any(
        f.lane == "contributor-directive" and f.path.startswith("docs/")
        for f in findings
    ), findings


def test_control_f3_historical_evidence_under_docs_is_exempt(tmp_path: Path) -> None:
    """Changelogs and decision records legitimately name the retired default."""
    _synthetic_repo(tmp_path, _CLEAN_WORKFLOW)
    decisions = tmp_path / "docs" / "decisions"
    decisions.mkdir(parents=True)
    (decisions / "adr-001.md").write_text(
        "Rejected: keep Python 3.11 as the default.\n", encoding="utf-8"
    )
    (tmp_path / "docs" / "CHANGELOG.md").write_text(
        "- fix(deps): hold numpy <2.5 on the Python 3.11 baseline\n", encoding="utf-8"
    )
    assert guard.check(tmp_path) == []


def test_control_g_article_prose_is_never_scanned(tmp_path: Path) -> None:
    """Prose is content, not configuration. It must not fail the guard."""
    _synthetic_repo(tmp_path, _CLEAN_WORKFLOW)
    for prose_dir in ("articles", "summaries", "translations"):
        directory = tmp_path / prose_dir / "2026-01-01-post"
        directory.mkdir(parents=True)
        (directory / "article.md").write_text(
            "Teams should install Python 3.11 and use python3.11 for this tutorial.\n",
            encoding="utf-8",
        )
    assert guard.check(tmp_path) == []


def test_control_h_allow_pragma_permits_an_intentional_mention(tmp_path: Path) -> None:
    _synthetic_repo(tmp_path, _CLEAN_WORKFLOW)
    tools = tmp_path / "tools"
    tools.mkdir()
    (tools / "notes.txt").write_text(
        "python3.11 was the previous baseline  # py-runtime-allow: historical record\n",
        encoding="utf-8",
    )
    assert guard.check(tmp_path) == []


def test_control_i_named_bounded_rollback_is_permitted(tmp_path: Path) -> None:
    _synthetic_repo(tmp_path, _CLEAN_WORKFLOW)
    tools = tmp_path / "tools"
    tools.mkdir()
    (tools / "rollback.txt").write_text(
        "python3.12 fallback  # py-runtime-rollback: owner=archive-maintainers "
        "expiry=2999-01-01\n",
        encoding="utf-8",
    )
    assert guard.check(tmp_path) == []


def test_control_j_expired_rollback_is_a_violation(tmp_path: Path) -> None:
    """A rollback lane must not be able to become a permanent exception."""
    _synthetic_repo(tmp_path, _CLEAN_WORKFLOW)
    tools = tmp_path / "tools"
    tools.mkdir()
    (tools / "rollback.txt").write_text(
        "python3.12 fallback  # py-runtime-rollback: owner=archive-maintainers "
        "expiry=2020-01-01\n",
        encoding="utf-8",
    )
    findings = guard.check(tmp_path, today=dt.date(2026, 7, 29))
    assert findings, "an expired rollback must be reported"
    assert any("expired" in f.detail for f in findings), findings


def test_control_k_guard_fails_without_pyyaml(tmp_path: Path, monkeypatch) -> None:
    """Missing PyYAML must fail closed, never pass vacuously."""
    _synthetic_repo(tmp_path, _CLEAN_WORKFLOW)
    monkeypatch.setitem(sys.modules, "yaml", None)
    findings = guard.check(tmp_path)
    assert findings, "a missing YAML parser must not yield a clean result"
