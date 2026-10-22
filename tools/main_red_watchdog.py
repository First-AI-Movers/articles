#!/usr/bin/env python3
"""Route a red default branch to an accountable repair owner (#489).

Why this exists
---------------
`aeos-merge-ready` is this repository's only required context. A check run that
is *not* required -- `mcp-server`, `og-worker`, every other `paths:`-filtered
surface -- is visible but cannot block a merge, and AGENTS.md's lifecycle is
explicitly "arm auto-merge and do not wait". So a bump or a merge can leave
`main` broken in a surface nothing was gated on, and nothing says so.

That is measured, not hypothetical: #485/#486 left `main` red for about 30 h,
#498/#499 for **six days**. Both were found by a governor sweep. In the second
case the #487 guard failed on `main` and named the conflict precisely, in the
`test` job -- a correct detector with no route to a person.

What it does, and what it deliberately does not
-----------------------------------------------
Scheduled census of the default branch's head: if any check run there has
settled on a failing conclusion, open **one** deduplicated issue naming the
broken surfaces and the commit and pull request that carry them; refresh it in
place while the condition lasts; **close it** as soon as the head is clean
again.

It changes nothing about how merges happen. No branch protection, no
required-context list, no organization policy, no revert, no push. The
`main-smoke` rail keeps its own decisions, which live in the organization-owned
reusable workflow, and this does not duplicate them: `main-smoke` smokes the
deployed site, this reads check-run conclusions.

Closing matters as much as opening (#473). Dedupe bounds the *rate* of a signal;
only a closer bounds its *population*. An issue that outlives its condition is
the stale in-repo status mirror AGENTS.md warns about, and the next reader
cannot tell a current red from a fixed one.

Result vocabulary (stdout, one line, `MAIN_RED_WATCHDOG_RESULT: ...`):
  GREEN    the head has no failed check run; any open incident was closed
  RED      the head is broken; one incident issue is open and current
  SKIP     nothing to judge (no head, or no check run has reported yet)
  ERROR    the watchdog itself could not complete

Environment:
  GH_TOKEN           token with issues:write on this repository
  GITHUB_REPOSITORY  owner/repo
  MAIN_BRANCH        default branch to watch (defaults to `main`)
  GITHUB_SERVER_URL / GITHUB_REPOSITORY / GITHUB_RUN_ID  for the run URL

The `gh` CLI is the integration surface; this script never touches git.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import ci_check_runs

RESULT_PREFIX = "MAIN_RED_WATCHDOG_RESULT:"

# Dedupe key. Stable and exact: the title carries no SHA and no check name, so
# the same condition always finds its own issue instead of opening a second one.
ISSUE_TITLE = "main is red: a check on the default branch is failing"
ISSUE_MARKER = "<!-- main-red-watchdog -->"
ISSUE_LABELS = ("automation", "ci")

# This watchdog's own check-run name, i.e. the `name:` of the job in
# .github/workflows/main-red-watchdog.yml. It is excluded from the census
# because the watchdog cannot judge itself (#489):
#
#   * A `schedule` run attaches its check-runs to the default branch's head, so
#     while the census is executing, `main-red-watchdog` is sitting on that very
#     head as `in_progress`. Requiring a fully settled head would then make
#     every census SKIP forever -- no GREEN, and so no closer, ever.
#   * Self-failure could not be reported either way: the newest check-run under
#     this name is always the currently-executing one, which retires any earlier
#     failed attempt before it could be read.
#
# A broken watchdog is therefore visible in Actions and through the absence of
# its result, not through its own alarm. `test_workflows_main_red_watchdog.py`
# pins this constant to the workflow's job name so a rename cannot silently
# re-include it.
SELF_CHECK_NAME = "main-red-watchdog"


class GhError(RuntimeError):
    pass


def _run_gh(args, *, check=True) -> str:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
    if check and proc.returncode != 0:
        raise GhError(
            f"gh {' '.join(args[:3])}... exited {proc.returncode}: "
            f"{proc.stderr.strip() or proc.stdout.strip()}"
        )
    return proc.stdout


def _api_json(path: str, *extra):
    out = _run_gh(["api", path, *extra])
    return json.loads(out) if out.strip() else None


# --------------------------------------------------------------------------
# Pure functions -- unit-testable without the gh CLI.
# --------------------------------------------------------------------------


def issue_body(
    *,
    branch: str,
    sha: str,
    failed: list[str],
    details: dict[str, str] | None = None,
    commit_subject: str = "",
    pull_request: int | None = None,
) -> str:
    """The incident body: who must repair what, and nothing else.

    Identifiers and URLs only -- no log excerpts, so a public issue cannot
    accidentally carry build output.

    A pure function of the head's state, deliberately: the body is rewritten on
    every census while the red lasts, so anything per-run in here (the
    watchdog's own run URL, a timestamp) would edit the issue every hour of an
    outage for no new information. What a repair owner needs is the failing
    checks' own run links, the head, and the pull request -- all of which are
    properties of the state. The watchdog's run URL belongs in the step summary
    and in the close comment, where it is written once.
    """
    lines = [
        ISSUE_MARKER,
        f"## `{branch}` is red",
        "",
        f"{len(failed)} check run(s) have settled on a failing conclusion at the "
        f"head of `{branch}`.",
        "",
        "### Failing",
        "",
    ]
    for name in failed:
        url = (details or {}).get(name)
        lines.append(f"- **{name}**" + (f" — [run]({url})" if url else ""))
    lines += [
        "",
        "### Head",
        "",
        f"- **Commit:** `{sha[:12]}`" + (f" — {commit_subject}" if commit_subject else ""),
    ]
    if pull_request:
        lines.append(f"- **Merged from:** #{pull_request} — the repair owner starts there")
    lines += [
        "",
        "### Why this needed an issue",
        "",
        "`aeos-merge-ready` is the only required context here, so a failing "
        "surface check does not block a merge and nothing announced this. "
        "#485/#486 left `main` red for about 30 h and #498/#499 for six days, "
        "both found by a sweep rather than an alarm (#489).",
        "",
        "This watchdog only reports. It does not revert, push, or change how "
        "merges happen. It closes this issue by itself once the head is clean, "
        "so an open one always means a current red.",
    ]
    return "\n".join(lines)


def judgeable(check_runs) -> dict[str, dict]:
    """The live check run per name, excluding this watchdog's own (SELF_CHECK_NAME)."""
    return {
        name: run
        for name, run in ci_check_runs.newest_runs_by_name(check_runs).items()
        if name != SELF_CHECK_NAME
    }


def classify(check_runs) -> tuple[str, list[str]]:
    """("RED", names) | ("GREEN", []) | ("SKIP", []) for one head's check runs.

    Order matters, and each branch is load-bearing:

    * **RED wins immediately.** A settled failure is actionable whatever else is
      still running, so it is never held back waiting for the rest of the head.
    * **GREEN requires a fully settled head.** `GREEN` closes an open incident,
      so it must mean "this head is proven clean", not "nothing has failed yet".
      Declaring it on a head whose checks are still queued would close a real
      incident the moment any commit landed on a broken `main`, then reopen it
      an hour later -- a spurious "closed, main is clean" on a branch that was
      never clean.
    * **Everything else is SKIP**, which changes nothing: no alarm, no close.
      A normal head settles in minutes, so the next hourly census judges it.
      If a check run is abandoned in `queued` the head never settles and an open
      incident simply stays open, which is the safe direction for this tool.
    """
    newest = judgeable(check_runs)
    failed = ci_check_runs.failed_check_names(check_runs, exclude={SELF_CHECK_NAME})
    if failed:
        return ("RED", failed)
    if not newest or any(run.get("status") != "completed" for run in newest.values()):
        return ("SKIP", [])
    return ("GREEN", [])


def failing_details(check_runs, failed: list[str]) -> dict[str, str]:
    """Map each failing check name to its newest run's `details_url`."""
    newest = judgeable(check_runs)
    out = {}
    for name in failed:
        url = (newest.get(name) or {}).get("details_url")
        if url:
            out[name] = url
    return out


# --------------------------------------------------------------------------
# gh CLI shell-out.
# --------------------------------------------------------------------------


def head_of(repo: str, branch: str) -> tuple[str, str]:
    """(sha, commit subject) for the tip of `branch`."""
    data = _api_json(f"repos/{repo}/commits/{branch}") or {}
    sha = data.get("sha") or ""
    message = ((data.get("commit") or {}).get("message") or "").strip()
    return sha, message.splitlines()[0] if message else ""


def pull_request_for(repo: str, sha: str) -> int | None:
    """The pull request a commit on the default branch came from, when GitHub
    still associates one -- this is the routing to an accountable owner."""
    try:
        found = _api_json(f"repos/{repo}/commits/{sha}/pulls") or []
    except GhError:
        return None
    for pr in found:
        number = pr.get("number")
        if number:
            return int(number)
    return None


def open_incidents(repo: str) -> list[int]:
    """Open issues whose title is exactly ISSUE_TITLE.

    Plain listing with a local exact-title filter, deliberately not the search
    index: it is eventually consistent and fails open when it lags, which would
    open a second issue for the same condition.
    """
    out = _run_gh(
        [
            "api", "--paginate",
            f"repos/{repo}/issues?state=open&per_page=100",
            "--jq", ".[] | select(.pull_request == null) | [.number, .title] | @json",
        ]
    )
    numbers = []
    for line in out.splitlines():
        if not line.strip():
            continue
        number, title = json.loads(line)
        if title == ISSUE_TITLE:
            numbers.append(int(number))
    return numbers


def issue_body_of(repo: str, number: int) -> str:
    """The issue's current body, or "" when it cannot be read.

    An unreadable body must not suppress the refresh, so the empty string makes
    the comparison in `open_or_refresh` fail open and write.
    """
    try:
        return ((_api_json(f"repos/{repo}/issues/{number}") or {}).get("body") or "")
    except GhError:  # pragma: no cover - network path
        return ""


def open_or_refresh(repo: str, body: str) -> tuple[str, int]:
    """Keep exactly one incident issue current. Returns (action, number).

    Writes nothing when the state has not moved: the body is a pure function of
    the head, so an unchanged body means an unchanged red and there is nothing
    to say. A multi-day outage therefore leaves one issue with one edit per
    actual change, not one per hourly census.
    """
    existing = open_incidents(repo)
    if existing:
        number = existing[0]
        if issue_body_of(repo, number) == body:
            return ("unchanged", number)
        _run_gh(["api", "-X", "PATCH", f"repos/{repo}/issues/{number}", "-f", f"body={body}"])
        if len(existing) > 1:
            print(
                f"::warning::{len(existing)} open watchdog issues; refreshed #{number}",
                file=sys.stderr,
            )
        return ("refreshed", number)
    created = _api_json(
        f"repos/{repo}/issues", "-X", "POST", "-f", f"title={ISSUE_TITLE}", "-f", f"body={body}"
    ) or {}
    number = int(created.get("number") or 0)
    if not number:
        raise GhError("issue creation returned no number")
    for label in ISSUE_LABELS:
        # Best-effort: a missing label must never fail an alarm.
        _run_gh(
            ["api", "-X", "POST", f"repos/{repo}/issues/{number}/labels", "-f", f"labels[]={label}"],
            check=False,
        )
    return ("opened", number)


def close_incidents(repo: str, numbers: list[int], note: str) -> None:
    """Retire the signal once the condition is gone (#473)."""
    for number in numbers:
        try:
            _run_gh(
                ["api", "-X", "POST", f"repos/{repo}/issues/{number}/comments", "-f", f"body={note}"]
            )
            _run_gh(
                ["api", "-X", "PATCH", f"repos/{repo}/issues/{number}", "-f", "state=closed"]
            )
            print(f"[watchdog] closed #{number}")
        except GhError as exc:  # pragma: no cover - network path
            print(f"::warning::could not close #{number}: {exc}", file=sys.stderr)


# --------------------------------------------------------------------------
# Main orchestration.
# --------------------------------------------------------------------------


def _result(code: str, detail: str) -> None:
    print(f"{RESULT_PREFIX} {code}")
    print(detail)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(f"## main-red watchdog\n\n{RESULT_PREFIX} {code}\n\n- {detail}\n")


def _run_url() -> str:
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    return f"{server}/{repo}/actions/runs/{run_id}" if repo and run_id else ""


def main() -> int:
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not repo or "/" not in repo:
        _result("ERROR", "GITHUB_REPOSITORY is not set")
        return 1
    branch = os.environ.get("MAIN_BRANCH", "main").strip() or "main"

    try:
        sha, subject = head_of(repo, branch)
        if not sha:
            _result("SKIP", f"could not resolve the head of {branch!r}")
            return 0
        checks = ci_check_runs.fetch_check_runs(_run_gh, repo, sha)
        verdict, failed = classify(checks)

        if verdict == "SKIP":
            # An unsettled head is not evidence either way, so nothing is
            # opened and -- crucially -- nothing open is closed.
            pending = sorted(
                name
                for name, run in judgeable(checks).items()
                if run.get("status") != "completed"
            )
            detail = (
                f"{sha[:12]} is not settled yet; still running: {', '.join(pending)}"
                if pending
                else f"no check run has reported on {sha[:12]} yet"
            )
            _result("SKIP", detail)
            return 0

        if verdict == "GREEN":
            existing = open_incidents(repo)
            if existing:
                close_incidents(
                    repo,
                    existing,
                    f"Closed automatically: `{branch}` is clean at `{sha[:12]}` — "
                    f"no check run is failing. Watchdog run: {_run_url()}",
                )
                _result("GREEN", f"{branch} is clean at {sha[:12]}; closed {len(existing)} incident(s)")
            else:
                _result("GREEN", f"{branch} is clean at {sha[:12]}")
            return 0

        body = issue_body(
            branch=branch,
            sha=sha,
            failed=failed,
            details=failing_details(checks, failed),
            commit_subject=subject,
            pull_request=pull_request_for(repo, sha),
        )
        action, number = open_or_refresh(repo, body)
    except GhError as exc:
        _result("ERROR", f"gh failed: {exc}")
        return 1

    _result("RED", f"{branch} red at {sha[:12]}: {', '.join(failed)} — {action} #{number}")
    # Exit 0: the watchdog did its job. A red `main` is reported through the
    # issue, not by failing this run -- a permanently red watchdog would be one
    # more broken check nobody is gated on, which is the defect it exists for.
    return 0


if __name__ == "__main__":
    sys.exit(main())
