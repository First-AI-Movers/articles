#!/usr/bin/env python3
"""Arm squash auto-merge on a Dependabot pull request (#432).

Why this exists
---------------
Under the AUTONOMOUS-MAIN lifecycle (AGENTS.md § PR lifecycle) an ordinary PR
reaches `main` because its author arms squash auto-merge while the one
required check, `aeos-merge-judge`, is still pending. Dependabot opens PRs
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
  6. The census in clause 5 is taken after `Run tests` has completed on that
     head (the `completed` event), never at `requested`. A new Dependabot
     head disarms an arm an earlier head earned.

Why clause 5 exists (#489)
--------------------------
`aeos-merge-judge` is this repository's only required context, so a check run
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

Why clause 6 exists (#489, measured 2026-10-26 and 2026-11-02)
-------------------------------------------------------------
Clause 5 alone lost every race it was built for. All 16 Dependabot PRs of those
two Monday runs were ARMED by the `requested` invocation, within about 20 s of
the PR opening, before any surface check had settled. Under the retired
`aeos-merge-ready` (about 30 s) a PR could already be `unstable` by then, and
GitHub declined the arm until `completed` (#468). Under `aeos-merge-judge`, which
reports only after the other checks settle, the PR is merely `blocked`, so GitHub
accepts the arm at once. The census therefore read nothing red:

  * #522 was armed 2 s after `mcp-server` failed, by a census taken before it did;
    #523 was armed before `og-worker` had even started.
  * Dependabot then rebased both. GitHub keeps auto-merge armed across that
    force-push, so every later invocation answered "already armed" and never
    looked. `aeos-merge-judge` passed and GitHub merged with the surface and
    `test` both red. #538 and #539 did the same on 2026-11-02.

So the census now waits for `completed`: by then `Run tests` itself has a
verdict and the surface checks (about 10 s) have long settled, while
`aeos-merge-judge` has not yet passed (it followed `test` by 15-70 s on all four
red heads). At `requested` the script arms nothing. An arm on an earlier head is
withdrawn, because the census that earned it was about a different commit, and
an arm on a head found red at `completed` is withdrawn before the refusal is
posted.

Result vocabulary (stdout, one line, `DEPENDABOT_AUTO_MERGE_RESULT: ...`):
  ARMED      auto-merge is now enabled on the PR
  MERGED     the PR was already mergeable and has been squash-merged
  DISARMED   a new Dependabot head arrived on an armed PR; the arm is withdrawn
             until the `completed` census of this head decides again
  SKIP       nothing to do (not a Dependabot PR, already armed/merged, a
             `requested` event deferring to `completed`, or the PR is not in an
             armable state -- see RETRYABLE_GH_FAILURES)
  REFUSED    a Dependabot PR that must not be armed; the reason is posted on
             the PR so it carries its own routing state, and the run fails
             so the refusal is visible in Actions.

Environment:
  GH_TOKEN                 App installation token (contents + pull requests).
  GITHUB_REPOSITORY        owner/repo.
  DEPENDABOT_PR_NUMBER     PR number from the event, when GitHub supplied it.
  DEPENDABOT_HEAD_BRANCH   the run's head branch (used to find the PR).
  DEPENDABOT_HEAD_SHA      the run's head SHA (the exact head to act on).
  DEPENDABOT_EVENT_ACTION  the workflow_run activity: `requested` or `completed`.

The `gh` CLI is the integration surface; this script never touches git.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import ci_check_runs

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
# `.github/dependabot.yml` configures them: the repository root only. The cookiecutter
# template's entry never scheduled a job and was removed (#362), so a Dependabot PR that
# touches the template's workflows is outside what this repository asked Dependabot for
# and is refused. A github-actions bump edits workflow files; the organization gate's
# workflow policy judges those bytes.
WORKFLOW_ROOTS = ("",)
WORKFLOW_DIR = ".github/workflows/"
WORKFLOW_SUFFIXES = (".yml", ".yaml")

REFUSAL_MARKER = "<!-- dependabot-auto-merge: REFUSED -->"

# What "red" means is shared with tools/main_red_watchdog.py (#489): one
# definition, so prevention and detection cannot disagree about a surface.
BLOCKING_CONCLUSIONS = ci_check_runs.BLOCKING_CONCLUSIONS

# Opening of the clause-5 refusal reason, so the posted comment can recognise
# its own case and route it (#489) without parsing a sentence.
FAILING_CHECKS_REASON = "check run(s) already failing"

# The two `workflow_run` activities the workflow listens to (clause 6). Only the
# `completed` census may arm: at `requested` no surface check has settled yet.
EVENT_REQUESTED = "requested"
EVENT_COMPLETED = "completed"


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

    Thin alias for the shared definition, kept so the decision table below reads
    as one module. The sorted result is what makes the refusal reason stable for
    the one-comment-per-reason dedupe in `post_refusal`.
    """
    return ci_check_runs.failed_check_names(check_runs)


def classify(
    pr: dict | None,
    files,
    expected_head_sha: str,
    check_runs=(),
    event_action: str = EVENT_COMPLETED,
) -> tuple[str, str]:
    """Decide what to do with the PR: ("ARM" | "DISARM" | "SKIP" | "REFUSED", reason).

    SKIP is "not a job for this script" (no PR, already handled, not a
    Dependabot PR at all) or "not yet" (a `requested` event, which defers to
    the `completed` census). REFUSED is "a Dependabot PR this script must not
    arm" -- an author or content property, or a red head, that makes it
    ineligible. DISARM is "an arm earned by an earlier head must not carry over
    to this one" (clause 6).

    An existing arm is never a reason to skip the census: that is how #522/#523
    and #538/#539 merged red after a rebase (#489).
    """
    if not pr:
        return ("SKIP", "no open pull request for this head")
    if pr.get("state") != "open":
        return ("SKIP", f"pull request is {pr.get('state')!r}, not open")
    if pr.get("merged"):
        return ("SKIP", "pull request is already merged")

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

    armed = bool(pr.get("auto_merge"))
    if event_action == EVENT_REQUESTED:
        if armed:
            return (
                "DISARM",
                f"new Dependabot head {head_sha[:12]} on a PR armed for an earlier head; "
                f"the `{EVENT_COMPLETED}` census of this head decides again",
            )
        return (
            "SKIP",
            f"deferred to the `{EVENT_COMPLETED}` census: at `{EVENT_REQUESTED}` no check "
            f"on {head_sha[:12]} has settled yet",
        )
    if event_action != EVENT_COMPLETED:
        return (
            "REFUSED",
            f"event action {event_action!r} is neither {EVENT_REQUESTED!r} nor {EVENT_COMPLETED!r}",
        )

    failed = failed_check_names(check_runs)
    if failed:
        return (
            "REFUSED",
            f"{FAILING_CHECKS_REASON} at {head_sha[:12]}: {', '.join(failed)}",
        )
    if armed:
        return ("SKIP", f"auto-merge is already armed and the census at {head_sha[:12]} is clean")
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
        "or lockfile; nothing here bypasses `aeos-merge-judge`. See #432.",
    ]
    if reason.startswith(FAILING_CHECKS_REASON):
        lines += [
            "",
            "That check is not a required context, so it would not have stopped this merge "
            "by itself -- which is exactly how #451/#452, #485/#486 and #498/#499 left `main` "
            "broken. Withholding arming is the half of the remedy this repository owns; the "
            "required-context list and branch protection are unchanged (#489). If this PR "
            "was armed for an earlier head, that arm has been withdrawn.",
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
    return ci_check_runs.fetch_check_runs(_run_gh, repo, sha)


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


def disarm(repo: str, number: int) -> str:
    """`gh pr merge --disable-auto`: withdraw an arm this head did not earn
    (clause 6). Read back like `arm`, so a PR that merged first is a failure the
    run reports, never a silent success."""
    _run_gh(["pr", "merge", str(number), "--repo", repo, "--disable-auto"])
    after = _api_json(f"repos/{repo}/pulls/{number}") or {}
    if after.get("merged"):
        raise GhError(f"#{number} merged before its arm could be withdrawn")
    if after.get("auto_merge"):
        raise GhError(f"gh pr merge --disable-auto returned success but #{number} is still armed")
    return "DISARMED"


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
    event_action = os.environ.get("DEPENDABOT_EVENT_ACTION", "").strip()

    arming = False
    try:
        pr = resolve_pr(repo, number, head_branch)
        open_pr = bool(pr) and pr.get("state") == "open"
        files = pr_files(repo, int(pr["number"])) if open_pr else []
        checks = head_check_runs(repo, head_sha) if open_pr else []
        verdict, reason = classify(pr, files, head_sha, checks, event_action)
        if verdict == "SKIP":
            _result("SKIP", reason)
            return 0
        if verdict == "DISARM":
            _result(disarm(repo, int(pr["number"])), f"#{pr['number']}: {reason}")
            return 0
        if verdict == "REFUSED":
            if open_pr and pr.get("auto_merge"):
                # A refused head must not stay armed: the arm is withdrawn before
                # the refusal is posted, so the comment never claims a state the
                # PR does not have (clause 6).
                disarm(repo, int(pr["number"]))
            post_refusal(repo, int(pr["number"]), reason)
            _result("REFUSED", reason)
            return 1
        arming = True
        outcome = arm(repo, int(pr["number"]))
    except GhError as exc:
        # Only an arm can meet a transient PR state. A failed disarm always
        # fails the run: an arm that should have been withdrawn is still live.
        if arming and is_retryable_gh_failure(str(exc)):
            # Not a refusal: GitHub would not accept the arm in the PR's current
            # state. Only `completed` arms, so no later event retries this head;
            # a new head, or a re-run of `Run tests`, decides it again.
            _result(
                "SKIP",
                f"pull request is not in an armable state; a new head or a re-run "
                f"of `Run tests` retries it: {exc}",
            )
            return 0
        _result("REFUSED", f"gh failed: {exc}")
        return 1
    _result(outcome, f"#{pr['number']} {pr.get('html_url', '')}: {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
