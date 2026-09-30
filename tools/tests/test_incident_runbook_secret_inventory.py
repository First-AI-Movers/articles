"""The incident runbook's rotation list must name the secrets that actually exist (#423 §5).

A responder reaching for this runbook is mid-incident and takes its list of
secrets as the inventory to rotate. Two ways that list can lie, and this
repository had both at once:

  * **It names a secret nothing consumes.** `ARTICLE_INGESTION_PR_TOKEN` was
    replaced by short-lived App authentication in #388 and is read by no
    workflow on `main`, yet the runbook still flagged its leak SEV-1. Rotating
    it accomplishes nothing while the clock runs.
  * **It omits a secret everything depends on.**
    `ARTICLES_AUTOMATION_APP_PRIVATE_KEY` is the live publishing credential --
    the class of credential whose silent invalidity froze the archive for
    weeks in #388 -- and it was absent from the list entirely.

So the list is pinned to the workflows rather than to memory: every secret a
root workflow reads must appear, and every secret named must be one a root
workflow reads. A new provider added to a workflow fails this test until the
runbook learns about it, which is the point.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
RUNBOOK = REPO_ROOT / "docs" / "INCIDENT_RESPONSE_RUNBOOK.md"

# `GITHUB_TOKEN` is minted per run by Actions itself. There is no provider to
# rotate it at and no repository secret to replace, so it is deliberately not
# part of the rotation inventory -- unlike every other name here.
NOT_ROTATABLE = frozenset({"GITHUB_TOKEN"})

# The paragraph that carries the inventory: step 1 of the secret-leak section.
ROTATION_STEP_MARKER = "Rotate at source first"


def _uncommented_lines(text: str) -> list[str]:
    """Drop whole-line YAML comments.

    The workflows explain #388 at length in comments, and those comments quote
    the dead credentials by name (`secrets.PAT`, `ARTICLE_INGESTION_PR_TOKEN`).
    Counting a comment as consumption would make this test assert the opposite
    of what it is for.
    """
    return [line for line in text.splitlines() if not line.lstrip().startswith("#")]


@pytest.fixture(scope="module")
def consumed_secrets() -> set[str]:
    """Every `secrets.NAME` actually read by a root workflow, minus the un-rotatable."""
    found: set[str] = set()
    for workflow in sorted(WORKFLOWS.glob("*.yml")):
        for line in _uncommented_lines(workflow.read_text(encoding="utf-8")):
            found.update(re.findall(r"secrets\.([A-Z0-9_]+)", line))
    assert found, "no workflow reads any secret -- the extractor is broken, not the repo"
    return found - set(NOT_ROTATABLE)


@pytest.fixture(scope="module")
def rotation_paragraph() -> str:
    text = RUNBOOK.read_text(encoding="utf-8")
    matches = [p for p in text.split("\n") if ROTATION_STEP_MARKER in p]
    assert len(matches) == 1, (
        f"expected exactly one {ROTATION_STEP_MARKER!r} step in {RUNBOOK.name}, "
        f"found {len(matches)} -- the rotation inventory moved and this test "
        f"is now reading the wrong paragraph"
    )
    return matches[0]


@pytest.fixture(scope="module")
def listed_secrets(rotation_paragraph: str) -> set[str]:
    """Backticked SCREAMING_SNAKE names in the rotation step.

    `NOT_ROTATABLE` is dropped from this side too: the step names `GITHUB_TOKEN`
    precisely to say it is *not* part of the inventory, and that sentence is
    worth keeping rather than tripping over.
    """
    named = set(re.findall(r"`([A-Z][A-Z0-9_]{3,})`", rotation_paragraph))
    return named - set(NOT_ROTATABLE)


def test_every_live_secret_is_in_the_rotation_list(consumed_secrets, listed_secrets):
    missing = consumed_secrets - listed_secrets
    assert not missing, (
        f"{sorted(missing)} are read by a workflow on `main` but are not named in "
        f"the rotation step of docs/{RUNBOOK.name}. A responder following the runbook "
        f"would leave them un-rotated. Add them (with what they authenticate)."
    )


def test_rotation_list_names_no_dead_secret(consumed_secrets, listed_secrets):
    dead = listed_secrets - consumed_secrets
    assert not dead, (
        f"{sorted(dead)} are named in the rotation step of docs/{RUNBOOK.name} but no "
        f"workflow on `main` reads them. Rotating a dead secret costs incident time and "
        f"implies a dependency that does not exist. Remove them, or the workflow that "
        f"was meant to consume them is missing."
    )


def test_the_live_publishing_credential_is_listed(listed_secrets):
    """#388's specific lesson, pinned so it cannot be dropped by a tidy-up."""
    assert "ARTICLES_AUTOMATION_APP_PRIVATE_KEY" in listed_secrets, (
        "the App private key is the credential that publishes; its silent invalidity "
        "is what froze the archive in #388. It must be in the rotation inventory."
    )


def test_the_dead_pat_is_not_described_as_a_live_dependency():
    """No prose anywhere in the runbook may present the retired PAT as in use."""
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "ARTICLE_INGESTION_PR_TOKEN" not in text, (
        "docs/INCIDENT_RESPONSE_RUNBOOK.md still names ARTICLE_INGESTION_PR_TOKEN. "
        "It was retired in #388 and is read by no workflow on `main`; the runbook "
        "described the ingestion path as depending on it."
    )
