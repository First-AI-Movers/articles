#!/usr/bin/env python3
"""Arm squash auto-merge on a Dependabot pull request (#432).

Why this exists
---------------
Under the AUTONOMOUS-MAIN lifecycle (AGENTS.md § PR lifecycle) an ordinary PR
reaches `main` because its author arms squash auto-merge while the one
required check, `aeos-merge-ready`, is still pending. Dependabot opens PRs
but never arms auto-merge, so every dependency bump sat green in the
operator's queue until somebody clicked (#432: six of them). This script is
the missing "author arms auto-merge" step for that one class of PR. It is
the same mechanism every other PR uses -- GitHub native squash auto-merge
under the organization gate -- and not a second merge controller: it reads
no test results, weakens nothing, and `gh pr merge --squash --auto` is the
only write it performs on an eligible PR. (`gh` merges immediately when the
PR is already mergeable, because GitHub refuses to *arm* a PR in clean
status; both outcomes are the ordinary lifecycle end state.)

Run by `.github/workflows/dependabot-auto-merge.yml` on `workflow_run`, in
the default-branch context, with the repository's Articles Automation App
token -- the credential the ingestion workflows already use for PR
operations. A Dependabot-triggered `pull_request` run cannot do this itself:
it receives no repository secrets, and auto-merge armed with the default
GITHUB_TOKEN would merge without firing the `push: main` workflows (deploy,
main-smoke), which is the same recursion rule that keeps the ingestion PRs
on the App token.

Eligibility (fail-closed; every exit prints one typed result line):
  1. The PR exists, is open, is not a draft, and targets `main`.
  2. Its author is `dependabot[bot]` (a Bot) and its head branch starts
     with `dependabot/`.
  3. Its head is exactly the SHA the triggering event reported.
  4. Every changed path is a manifest or lockfile of an ecosystem/directory
     `.github/dependabot.yml` configures (ALLOWED_PATHS, WORKFLOW_ROOTS). A
     workflow file is allowed only as the `github-actions` ecosystem's manifest,
     under a directory that file configures; the organization gate's workflow
     policy judges those bytes, not this script.
  5. No check run on that head has already failed (BLOCKING_CONCLUSIONS).

Why clause 5 exists (#489)
--------------------------
`aeos-merge-ready` is this repository's only required context, so a check run
that is *not* required -- `mcp-server`, `og-worker`, and every other
`paths:`-filtered surface -- is visible but cannot block a merge. Three times
(#451/#452, #485/#486, #498/#499) a bump merged with its own surface red and
left `main` broken for days: the last of those for six, with the #487 guard
naming the conflict correctly in a `test` job nobody was gated on.

Clause 5 is the half of that remedy this repository owns. It does not touch
branch protection, the required-context list, or the organization gate -- it
withholds *this script's* arming, so a bump whose surface is already red stays
open for a person instead of auto-merging. A PR with checks still running is
not red: arming while the gate is pending is the ordinary lifecycle, and only a
settled failure refuses. Human PRs are unaffected, by construction.

Result vocabulary (stdout, one line, `DEPENDABOT_AUTO_MERGE_RESULT: ...`):
  ARMED      auto-merge is now enabled on the PR
  MERGED     the PR was already mergeable and has been squash-merged
  SKIP       nothing to do (not a Dependabot PR, already armed/merged, or the
             PR is not in an armable state YET -- see RETRYABLE_GH_FAILURES)
  REFUSED    a Dependabot PR that must not be armed; the reason is posted on
             the PR so it carries its own routing state, and the run fails
             so the refusal is visible in Actions.

Environment:
  GH_TOKEN                 App installation token (contents + pull requests).
  GITHUB_REPOSITORY        owner/repo.
  DEPENDABOT_PR_NUMBER     PR number from the event, when GitHub supplied it.
  DEPENDABOT_HEAD_BRANCH   the run's head branch (used to find the PR).
  DEPENDABOT_HEAD_SHA      the run's head SHA (the exact head to act on).

The `gh` CLI is the integration surface; this script never touches git.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

RESULT_PREFIX = "DEPENDABOT_AUTO_MERGE_RESULT:"

DEPENDABOT_LOGIN = "dependabot[bot]"
HEAD_BRANCH_PREFIX = "dependabot/"
BASE_BRANCH = "main"

# Every manifest/lockfile Dependabot is configured to touch, per
# `.github/dependabot.yml` (pip: /tools; npm: /, /mcp-server, /og-worker;
# github-actions: /). `tools/tests/test_arm_dependabot_auto_merge.py` derives
# the expected set from that file so the two cannot drift apart silently.
ALLOWED_PATHS = frozenset(
    {
        "package.json",
        "package-lock.json",
        "mcp-server/package.json",
        "mcp-server/package-lock.json",
        "og-worker/package.json",
        "og-worker/package-lock.json",
        "tools/requirements.txt",
    }
)
# Directories whose `.github/workflows/` the `github-actions` ecosystem watches, as
# `.github/dependabot.yml` configures them: the repository root, and the cookiecutter
# template, whose workflows are a second copy of the same surface (#362). A github-actions
# bump edits workflow files; the organization gate's workflow policy judges those bytes.
WORKFLOW_ROOTS = ("", "cookiecutter-archive-template/{{cookiecutter.repo_slug}}/")
WORKFLOW_DIR = ".github/workflows/"
WORKFLOW_SUFFIXES = (".yml", ".yaml")

REFUSAL_MARKER = "<!-- dependabot-auto-merge: REFUSED -->"

# Check-run conclusions that mean "this surface is broken at this head" (#489).
# Deliberately tight: `skipped` is the normal conclusion for every
# `paths:`-filtered workflow that did not apply and for the unarmed
# `main-smoke` revert legs, `neutral` and `stale` are not verdicts, and
# `cancelled` is usually a superseded run rather than a result. Only a settled,
# self-reported failure withholds arming.
BLOCKING_CONCLUSIONS = frozenset({"failure", "timed_out", "action_required"})

# Opening of the clause-5 refusal reason, so the posted comment can recognise
# its own case and route it (#489) without parsing a sentence.
FAILING_CHECKS_REASON = "check run(s) already failing"


# --------------------------------------------------------------------------
# Pure functions -- unit-testable without the gh CLI.
# --------------------------------------------------------------------------


def is_path_allowed(path: str) -> bool:
    """True when `path` is a manifest/lockfile Dependabot may change here.

    Workflow files match only as direct children of `.github/workflows/`
    with a YAML suffix: no nested directories, no `.github/actions/`, no
    other file type.
    """
    if not path or "\x00" in path or path.startswith("/") or ".." in path.split("/"):
        return False
    if path in ALLOWED_PATHS:
        return True
    for root in WORKFLOW_ROOTS:
        prefix = f"{root}{WORKFLOW_DIR}"
        if path.startswith(prefix):
            name = path[len(prefix):]
            return bool(name) and "/" not in name and name.endswith(WORKFLOW_SUFFIXES)
    return False


def first_disallowed_path(paths) -> str | None:
    for p in paths:
        if not is_path_allowed(p):
            return p
    return None


def failed_check_names(check_runs) -> list[str]:
    """Names of check runs whose newest attempt on this head failed (#489).

    One check name can legitimately appear several times on a head, always from
    distinct workflow runs -- a re-run, or a scheduled workflow that runs again
    on an unchanged `main`. Check-run ids increase with creation, so the highest
    id is the newest verdict for that name and it retires any earlier one: a red
    surface that is re-run green does not keep refusing.

    Returns a sorted list so the refusal reason is stable for the
    one-comment-per-reason dedupe in `post_refusal`.
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
    return sorted(
        name
        for name, run in newest.items()
        if run.get("status") == "completed"
        and (run.get("conclusion") or "").lower() in BLOCKING_CONCLUSIONS
    )


def classify(pr: dict | None, files, expected_head_sha: str, check_runs=()) -> tuple[str, str]:
    """Decide what to do with the PR: ("ARM" | "SKIP" | "REFUSED", reason).

    SKIP is "not a job for this script" (no PR, already handled, not a
    Dependabot PR at all). REFUSED is "a Dependabot PR this script must not
    arm" -- an author or content property that makes it ineligible.
    """
    if not pr:
        return ("SKIP", "no open pull request for this head")
    if pr.get("state") != "open":
        return ("SKIP", f"pull request is {pr.get('state')!r}, not open")
    if pr.get("merged"):
        return ("SKIP", "pull request is already merged")
    if pr.get("auto_merge"):
        return ("SKIP", "auto-merge is already armed")

    user = pr.get("user") or {}
    if user.get("login") != DEPENDABOT_LOGIN or user.get("type") != "Bot":
        return ("SKIP", f"author {user.get('login')!r} ({user.get('type')!r}) is not Dependabot")

    head = pr.get("head") or {}
    head_ref = head.get("ref") or ""
    if not head_ref.startswith(HEAD_BRANCH_PREFIX):
        return ("REFUSED", f"head branch {head_ref!r} is not a {HEAD_BRANCH_PREFIX!r} branch")
    if pr.get("draft"):
        return ("REFUSED", "pull request is a draft")
    base_ref = (pr.get("base") or {}).get("ref")
    if base_ref != BASE_BRANCH:
        return ("REFUSED", f"base branch is {base_ref!r}, not {BASE_BRANCH!r}")
    head_sha = head.get("sha") or ""
    if not expected_head_sha or head_sha != expected_head_sha:
        return (
            "SKIP",
            f"head moved: event reported {expected_head_sha[:12] or '?'}, "
            f"pull request is at {head_sha[:12] or '?'} (a later run will see the new head)",
        )

    paths = [f.get("filename") or "" for f in (files or [])]
    if not paths:
        return ("REFUSED", "pull request changes no files")
    bad = first_disallowed_path(paths)
    if bad is not None:
        return ("REFUSED", f"changed path {bad!r} is not a dependency manifest or lockfile")

    failed = failed_check_names(check_runs)
    if failed:
        return (
            "REFUSED",
            f"{FAILING_CHECKS_REASON} at {head_sha[:12]}: {', '.join(failed)}",
        )
    return ("ARM", f"{len(paths)} dependency file(s) changed by Dependabot at {head_sha[:12]}")


def refusal_comment(reason: str, run_url: str) -> str:
    lines = [
        REFUSAL_MARKER,
        "## Dependabot auto-merge not armed",
        "",
        f"**Reason:** {reason}",
        "",
        f"- **Run:** {run_url}",
        "",
        "This PR stays open for a person to decide. The arming step only arms squash "
        "auto-merge on a Dependabot PR whose every changed path is a dependency manifest "
        "or lockfile; nothing here bypasses `aeos-merge-ready`. See #432.",
    ]
    if reason.startswith(FAILING_CHECKS_REASON):
        lines += [
            "",
            "That check is not a required context, so it would not have stopped this merge "
            "by itself -- which is exactly how #451/#452, #485/#486 and #498/#499 left `main` "
            "broken. Withholding arming is the half of the remedy this repository owns; the "
            "required-context list and branch protection are unchanged (#489).",
            "",
            "**To proceed:** push a fix to this branch -- that re-runs `Run tests`, and the "
            "arming listens to it, so a head whose surfaces are green is armed normally. "
            "A newer green run of the same check retires the red, but re-running *only* the "
            "failing workflow fires no arming event (this step is triggered by `Run tests`, "
            "and `requested` does not fire on a re-run): re-run `Run tests` afterwards to be "
            "picked up. Merging it red stays a deliberate choice for a person with repository "
            "access, not something this step will do.",
        ]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# gh CLI shell-out.
# --------------------------------------------------------------------------


# GitHub rejections that mean "not in an armable state YET", not "must not be
# armed". The `requested` activity type fires within seconds of Dependabot
# opening a PR, long before its checks settle, so `gh pr merge --auto` can come
# back with one of these purely because it lost a race the workflow already
# plans for: `completed` is the documented retry. Reporting them as REFUSED
# turns every Dependabot PR into a red Actions run whose step summary claims a
# refusal that never happened -- observed on #468, which the `completed` run
# then merged 2m14s later with nobody involved (#432 clause 10). An alarm that
# fires on every healthy PR is one nobody reads.
RETRYABLE_GH_FAILURES = (
    "pull request is in unstable status",
    "pull request is in dirty status",
    "pull request is in blocked status",
    "pull request is in unknown status",
    "pull request is not mergeable",
    "base branch was modified",
)


def is_retryable_gh_failure(message: str) -> bool:
    """Whether a gh failure is a transient PR state the next event will resolve."""
    lowered = (message or "").lower()
    return any(marker in lowered for marker in RETRYABLE_GH_FAILURES)


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


def resolve_pr(repo: str, number: str, head_branch: str) -> dict | None:
    if number.strip().isdigit():
        return _api_json(f"repos/{repo}/pulls/{int(number)}")
    if not head_branch:
        return None
    owner = repo.split("/", 1)[0]
    found = _api_json(
        f"repos/{repo}/pulls",
        "-X", "GET",
        "-f", "state=open",
        "-f", f"head={owner}:{head_branch}",
        "-f", "per_page=1",
    )
    return found[0] if found else None


def pr_files(repo: str, number: int) -> list[dict]:
    out = _run_gh(["api", "--paginate", f"repos/{repo}/pulls/{number}/files", "--jq", ".[]"])
    return [json.loads(line) for line in out.splitlines() if line.strip()]


def head_check_runs(repo: str, sha: str) -> list[dict]:
    """Every check run GitHub has recorded against `sha` (#489)."""
    if not sha:
        return []
    out = _run_gh(
        [
            "api", "--paginate", f"repos/{repo}/commits/{sha}/check-runs?per_page=100",
            "--jq", ".check_runs[]",
        ]
    )
    return [json.loads(line) for line in out.splitlines() if line.strip()]


def arm(repo: str, number: int) -> str:
    """`gh pr merge --squash --auto`: arms when the gate is pending, merges when
    the PR is already mergeable (GitHub refuses to arm a clean PR). Returns the
    typed outcome read back from the PR, never inferred from gh's stdout."""
    _run_gh(["pr", "merge", str(number), "--repo", repo, "--squash", "--auto"])
    after = _api_json(f"repos/{repo}/pulls/{number}") or {}
    if after.get("merged"):
        return "MERGED"
    if after.get("auto_merge"):
        return "ARMED"
    raise GhError(
        f"gh pr merge --auto returned success but #{number} is neither merged nor armed "
        f"(state={after.get('state')!r})"
    )


def post_refusal(repo: str, number: int, reason: str) -> None:
    """One refusal comment per PR head; best-effort, never masks the exit code."""
    run_url = (
        f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/"
        f"{os.environ.get('GITHUB_REPOSITORY', repo)}/actions/runs/"
        f"{os.environ.get('GITHUB_RUN_ID', '')}"
    )
    try:
        existing = _run_gh(
            ["api", "--paginate", f"repos/{repo}/issues/{number}/comments", "--jq", ".[].body"]
        )
        if REFUSAL_MARKER in existing and reason in existing:
            return
        _run_gh(
            [
                "api", "-X", "POST", f"repos/{repo}/issues/{number}/comments",
                "-f", f"body={refusal_comment(reason, run_url)}",
            ]
        )
    except GhError as exc:  # pragma: no cover - network path
        print(f"[warn] could not post the refusal on #{number}: {exc}", file=sys.stderr)


# --------------------------------------------------------------------------
# Main orchestration.
# --------------------------------------------------------------------------


def _result(code: str, detail: str) -> None:
    print(f"{RESULT_PREFIX} {code}")
    print(detail)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(f"## Dependabot auto-merge\n\n{RESULT_PREFIX} {code}\n\n- {detail}\n")


def main() -> int:
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not repo or "/" not in repo:
        _result("REFUSED", "GITHUB_REPOSITORY is not set")
        return 1
    number = os.environ.get("DEPENDABOT_PR_NUMBER", "")
    head_branch = os.environ.get("DEPENDABOT_HEAD_BRANCH", "").strip()
    head_sha = os.environ.get("DEPENDABOT_HEAD_SHA", "").strip()

    try:
        pr = resolve_pr(repo, number, head_branch)
        open_pr = bool(pr) and pr.get("state") == "open"
        files = pr_files(repo, int(pr["number"])) if open_pr else []
        checks = head_check_runs(repo, head_sha) if open_pr else []
        verdict, reason = classify(pr, files, head_sha, checks)
        if verdict == "SKIP":
            _result("SKIP", reason)
            return 0
        if verdict == "REFUSED":
            post_refusal(repo, int(pr["number"]), reason)
            _result("REFUSED", reason)
            return 1
        outcome = arm(repo, int(pr["number"]))
    except GhError as exc:
        if is_retryable_gh_failure(str(exc)):
            # Not a refusal: the PR is not armable yet. The `completed`
            # activity type on the same workflow_run is the retry, and it is
            # idempotent -- by then the PR is armed, merged, or still pending.
            _result(
                "SKIP",
                f"pull request is not in an armable state yet, awaiting the "
                f"`completed` retry: {exc}",
            )
            return 0
        _result("REFUSED", f"gh failed: {exc}")
        return 1
    _result(outcome, f"#{pr['number']} {pr.get('html_url', '')}: {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
