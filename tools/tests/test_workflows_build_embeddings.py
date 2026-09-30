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
    """GITHUB_TOKEN neither pushes the branch nor opens the PR, so it needs no write there.

    Rewritten for #388. Both operations now use a short-lived App installation token, so the
    default token's job is checkout plus the incident-issue path. Asserting `contents: write`
    here would re-require a scope nothing uses — the workflow would still pass while carrying
    a permission it does not need, which is the shape of finding this suite exists to catch.
    """
    perms = _load().get("permissions") or {}
    assert perms.get("contents") == "read", (
        f"build-embeddings.yml must grant GITHUB_TOKEN only `contents: read`; the branch push "
        f"and PR use the App token minted in-workflow. Got {perms!r}"
    )
    assert perms.get("pull-requests") != "write", (
        f"GITHUB_TOKEN must not hold `pull-requests: write`; create-pull-request uses the App "
        f"token. Got {perms!r}"
    )
    assert perms.get("issues") == "write", (
        f"the incident-issue step runs on GITHUB_TOKEN and cannot file without `issues: write`; "
        f"got {perms!r}"
    )


def test_has_concurrency_group():
    conc = _load().get("concurrency")
    assert isinstance(conc, dict) and conc.get("group"), (
        f"build-embeddings.yml must declare a concurrency group so scheduled "
        f"and manual runs do not race the shared refresh branch; got {conc!r}"
    )


def test_pr_step_uses_ci_triggering_token():
    """The PR must be opened with a token that lets CI run on it — stated as a property.

    Rewritten for #388. This used to require the literal `ARTICLE_INGESTION_PR_TOKEN`, which
    pinned an INSTANCE rather than the requirement, so replacing that long-lived PAT with a
    short-lived App token failed a test whose actual concern was fully satisfied.

    The requirement is mechanical: GitHub suppresses workflow runs on a PR created with the
    default GITHUB_TOKEN, to prevent recursion. Such a PR would never run `aeos-merge-ready`,
    the organization's only required check, and so could never merge. Any non-GITHUB_TOKEN
    identity satisfies it; the App token does, with an hour-long lifetime instead of a year's.
    """
    pr_steps = [
        s for s in _steps()
        if isinstance(s.get("uses"), str) and s["uses"].startswith("peter-evans/create-pull-request")
    ]
    assert len(pr_steps) == 1, f"expected exactly one create-pull-request step, got {len(pr_steps)}"
    token = str(pr_steps[0].get("with", {}).get("token", ""))
    assert token.strip(), "create-pull-request must be given an explicit token"
    assert "secrets.GITHUB_TOKEN" not in token, (
        f"create-pull-request must NOT use the default GITHUB_TOKEN: PRs it creates do not "
        f"trigger workflow runs, so `aeos-merge-ready` would never run and the PR could never "
        f"merge. Got {token!r}"
    )
    assert "app_token" in token, (
        f"the PR token should be the short-lived App installation token minted in-workflow "
        f"(#388 replaced a long-lived PAT); got {token!r}"
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


# ---------------------------------------------------------------------------
# The incident family must be bounded at both ends (#473).
# ---------------------------------------------------------------------------

def _named_step(fragment: str) -> dict:
    matches = [s for s in _steps() if fragment in (s.get("name") or "")]
    assert len(matches) == 1, (
        f"expected exactly one step whose name contains {fragment!r}, found {len(matches)}"
    )
    return matches[0]


def _command_lines(run: str) -> str:
    """The step body without whole-line shell comments.

    Both steps *explain* why they avoid the search index, and prose naming a
    flag is not a use of it.
    """
    return "\n".join(l for l in run.splitlines() if not l.lstrip().startswith("#"))


def test_a_successful_scheduled_refresh_closes_the_incident():
    """Dedupe bounds the rate; only a closer bounds the population.

    #402 sat open 2026-09-06 -> 2026-09-20 and was closed by hand, long after
    the weekly refresh had recovered.
    """
    closer = _named_step("Close the embeddings incident")
    cond = closer["if"]
    assert "success()" in cond, f"the closer must run on a green refresh; got {cond!r}"
    assert "github.event_name == 'schedule'" in cond, (
        "only a scheduled run establishes that the weekly refresh is healthy again; "
        f"a dispatch or push must not close the incident. got {cond!r}"
    )
    run = closer["run"]
    assert "gh issue close" in run, "the closer must actually close the issue"
    assert "gh issue comment" not in run, (
        "the closer must close, not comment: a bare `gh issue comment` means a path "
        "reports success while the issue stays open"
    )


def test_alarm_and_closer_cover_both_outcomes():
    alarm = _named_step("Open incident issue on scheduled failure")["if"]
    closer = _named_step("Close the embeddings incident")["if"]
    assert "failure()" in alarm and "success()" in closer, (
        "a scheduled run must have an owner whether it passes or fails.\n"
        f"  alarm:  {alarm}\n  closer: {closer}"
    )


def test_neither_incident_step_dedupes_through_the_search_index():
    """`--search` fails open when the index lags, and files a duplicate (#462)."""
    for fragment in ("Open incident issue on scheduled failure", "Close the embeddings incident"):
        run = _command_lines(_named_step(fragment)["run"])
        assert "--search" not in run, (
            f"{fragment!r} must not use `gh issue list --search`: the search index is "
            "eventually consistent, and when it lags the dedupe fails open and files a "
            "duplicate. Use a plain listing with a local title filter."
        )


def test_closer_is_best_effort():
    run = _named_step("Close the embeddings incident")["run"]
    assert "set +e" in run and run.rstrip().endswith("exit 0"), (
        "incident bookkeeping must never turn a green refresh red"
    )
