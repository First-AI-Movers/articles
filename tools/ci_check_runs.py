#!/usr/bin/env python3
"""Read GitHub check runs for a commit and say which surfaces are broken (#489).

Why this is shared
------------------
`aeos-merge-ready` is this repository's only required context, so a check run
that is *not* required -- `mcp-server`, `og-worker`, and every other
`paths:`-filtered surface -- is visible but cannot block a merge. Two owners act
on that same fact and must agree about what "red" means:

  * `tools/arm_dependabot_auto_merge.py` withholds arming for a head that is
    already red (prevention).
  * `tools/main_red_watchdog.py` routes a red default branch to an accountable
    owner (detection).

One definition, one place. A surface that one of them counts as red and the
other does not would be worse than either alone.
"""

from __future__ import annotations

import json

# Check-run conclusions that mean "this surface is broken at this commit".
# Deliberately tight: `skipped` is the normal conclusion for every
# `paths:`-filtered workflow that did not apply and for the unarmed
# `main-smoke` revert legs, `neutral` and `stale` are not verdicts, and
# `cancelled` is usually a superseded run rather than a result. Only a settled,
# self-reported failure counts.
BLOCKING_CONCLUSIONS = frozenset({"failure", "timed_out", "action_required"})


def newest_runs_by_name(check_runs) -> dict[str, dict]:
    """The live check run for each name on one commit.

    One check name can legitimately appear several times on a commit, always
    from distinct workflow runs -- a re-run, or a scheduled workflow that runs
    again on an unchanged `main`. Check-run ids increase with creation, so the
    highest id is the newest verdict for that name and it retires any earlier
    one: a red surface that is re-run green stops counting as red.
    """
    newest: dict[str, dict] = {}
    for run in check_runs or ():
        if not isinstance(run, dict):
            continue
        name = (run.get("name") or "").strip()
        if not name:
            continue
        current = newest.get(name)
        if current is None or (run.get("id") or 0) >= (current.get("id") or 0):
            newest[name] = run
    return newest


def has_failed(run) -> bool:
    """Whether one check run is a settled failure.

    The single predicate. Both consumers ask this rather than re-deriving
    "completed and in BLOCKING_CONCLUSIONS", so a change to what counts as a
    settled failure cannot land in one of them and not the other.
    """
    return (run or {}).get("status") == "completed" and (
        ((run or {}).get("conclusion") or "").lower() in BLOCKING_CONCLUSIONS
    )


def failed_check_names(check_runs, *, exclude=()) -> list[str]:
    """Names of check runs whose newest attempt on this commit failed.

    `exclude` drops names from consideration entirely -- a scheduled watchdog
    passes its own job name, because its run sits on the very head it reads.

    Sorted, so a caller that puts the list in a comment or an issue body
    produces the same text for the same state.
    """
    excluded = frozenset(exclude)
    return sorted(
        name
        for name, run in newest_runs_by_name(check_runs).items()
        if name not in excluded and has_failed(run)
    )


def fetch_check_runs(run_gh, repo: str, ref: str) -> list[dict]:
    """Every check run GitHub has recorded against `ref`.

    `run_gh` is the caller's `gh` shell-out, so this stays testable without a
    network and each caller keeps its own error handling.
    """
    if not ref:
        return []
    out = run_gh(
        [
            "api", "--paginate", f"repos/{repo}/commits/{ref}/check-runs?per_page=100",
            "--jq", ".check_runs[]",
        ]
    )
    return [json.loads(line) for line in out.splitlines() if line.strip()]
