"""Guard: the cookiecutter template's action pins follow this repository's convention (#362).

`.github/dependabot.yml`'s `github-actions` entry watches `.github/workflows/` at the
repository root. The workflows shipped inside
`cookiecutter-archive-template/{{cookiecutter.repo_slug}}/.github/workflows/` are a
second, unwatched copy of the same surface: nothing bumped them and no test read them,
so they drifted three majors behind (`checkout@v4`, `upload-pages-artifact@v3`,
`deploy-pages@v4`) and every repository generated from the template started there.

Dependabot coverage keeps the pins current; this guard is the part that cannot silently
stop working. It is deliberately a *comparison against the root workflows* rather than a
hardcoded version table: a table would itself go stale, and the contract is that a
repository generated from the template starts where this repository already is.

The governed-pin policy is `@vN` for first-party actions (not a commit SHA) — see
`docs/decisions/` and the root workflows — so the pins are compared by their major tag.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT_WORKFLOWS = REPO_ROOT / ".github" / "workflows"
TEMPLATE_WORKFLOWS = (
    REPO_ROOT / "cookiecutter-archive-template" / "{{cookiecutter.repo_slug}}" / ".github" / "workflows"
)
VERSION_TAG_RE = re.compile(r"^v[0-9]+(\.[0-9]+)*$")
SHA_PIN_RE = re.compile(r"^[0-9a-f]{40}$")


def _uses(directory: Path) -> dict[str, set[str]]:
    """Map action name -> the set of refs it is pinned to across `directory`."""
    found: dict[str, set[str]] = {}
    for wf in sorted(directory.glob("*.y*ml")):
        document = yaml.safe_load(wf.read_text(encoding="utf-8")) or {}
        for job in (document.get("jobs") or {}).values():
            if not isinstance(job, dict):
                continue
            for step in job.get("steps") or []:
                uses = (step or {}).get("uses")
                if not isinstance(uses, str) or uses.startswith("./") or uses.startswith("docker://"):
                    continue
                name, _, ref = uses.rpartition("@")
                found.setdefault(name, set()).add(ref)
    return found


def test_template_ships_workflows_to_govern():
    assert TEMPLATE_WORKFLOWS.is_dir(), f"{TEMPLATE_WORKFLOWS} is missing"
    assert _uses(TEMPLATE_WORKFLOWS), "the template's workflows reference no actions to pin"


def test_template_pins_are_governed_version_tags():
    """No floating ref (`@main`, `@master`, a branch) in the template.

    The convention for first-party `actions/*` is a governed `@vN` tag plus Dependabot,
    never a SHA-forced pin; a third-party action would take a commit SHA, and the
    template ships none today.
    """
    offenders = {
        f"{name}@{ref}"
        for name, refs in _uses(TEMPLATE_WORKFLOWS).items()
        for ref in refs
        if not (VERSION_TAG_RE.match(ref) or SHA_PIN_RE.match(ref))
    }
    assert not offenders, (
        f"template actions must be pinned to a governed version tag (or a commit SHA for a "
        f"third party); floating refs found: {sorted(offenders)}"
    )


def test_template_pins_match_the_root_convention():
    """Every action the template shares with the root workflows is pinned the same.

    This is the drift alarm #362 asks for: a bump at the root that skips the template
    fails here instead of waiting for a reader to notice months later.
    """
    root = _uses(ROOT_WORKFLOWS)
    template = _uses(TEMPLATE_WORKFLOWS)
    shared = sorted(set(root) & set(template))
    assert shared, "expected the template to share actions with the root workflows"
    drift = {
        name: {"root": sorted(root[name]), "template": sorted(template[name])}
        for name in shared
        if template[name] != root[name]
    }
    assert not drift, (
        f"the cookiecutter template must ship the same action pins as this repository's own "
        f"workflows, so a generated repository starts where this one is (#362). Drift: {drift}"
    )


def test_every_template_action_is_shared_with_the_root():
    """An action only the template uses has no root pin to be compared against, so the
    guard above would not see it drift. Today there are none; if one is added, either the
    root grows the same action or this guard needs an explicit, argued exception."""
    only_template = sorted(set(_uses(TEMPLATE_WORKFLOWS)) - set(_uses(ROOT_WORKFLOWS)))
    assert not only_template, (
        f"these template actions appear in no root workflow, so nothing pins their version: "
        f"{only_template}. Add the action at the root too, or extend this guard deliberately."
    )
