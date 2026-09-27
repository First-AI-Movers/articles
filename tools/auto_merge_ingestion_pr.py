#!/usr/bin/env python3
"""Auto-merge a freshly-created Airtable ingestion PR (E41f).

Strict, defense-in-depth gates. Default OFF behind two repo-level
switches: `INGEST_DRY_RUN` (cron kill switch — checked by the calling
workflow step's `if:`) and `AUTO_MERGE_INGESTION_PRS` (E41f-specific
gate — checked here).

Run after `peter-evans/create-pull-request` in
`.github/workflows/ingest-airtable.yml`. The same workflow run that
creates the PR also (optionally) merges it once CI is green.

Order of pre-flight checks (any failure aborts the merge):

  1. `AUTO_MERGE_INGESTION_PRS == "1"` — variable kill switch.
     Silent skip when off; no incident issue.
  2. An open PR exists with head ref starting with `ingest/airtable-`.
     Silent skip when none found (nothing was created this run).
  3. PR title is exactly `EXPECTED_TITLE`.
  4. Every changed path matches `ALLOWED_PATHS`.
  5. `mergeable == "MERGEABLE"`.
  6. All `REQUIRED_CHECKS` finished and `conclusion == "SUCCESS"`.
     Polled with timeout.

When checks (1)-(2) cause a skip, exit 0 with `[skip] reason`.
When checks (3)+ block, exit 1 and open an `E41 auto-merge blocked`
issue. Merge uses squash and deletes the head branch.

Environment:
  GH_TOKEN                       — passed by the workflow.
  AUTO_MERGE_INGESTION_PRS       — repo variable; default "0".
  AUTO_MERGE_HEAD_BRANCH         — override head branch (testing).
  AUTO_MERGE_TIMEOUT_SECONDS     — polling deadline (default 900).
  AUTO_MERGE_POLL_INTERVAL       — seconds between polls (default 30).
  AUTO_MERGE_REPO                — owner/repo (default inferred by gh).
  GITHUB_RUN_ID, GITHUB_SERVER_URL, GITHUB_REPOSITORY — for issue body.

The `gh` CLI is the integration surface; this script never touches the
git plumbing directly.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time

EXPECTED_TITLE = "ingest(articles): add articles from Airtable"
# Title prefix of the incident this script files. It is deliberately NOT the
# `E41 cron ingestion incident:` prefix the workflow's own alarm uses: the two
# report different things (this one, a blocked candidate PR; that one, a failed
# cron run). The cost of the separate prefix is that `ingest-airtable.yml`'s
# cleanup step cannot sweep these — it filters
# `startswith("E41 cron ingestion incident:")` exactly, by design, so it can
# never close an unrelated issue. Nothing owned this family's end of life, so it
# accumulated: #454-#458 were one block on PR #453 reported five times.
# `close_resolved_blocked_issues()` below is that missing owner.
BLOCKED_TITLE_PREFIX = "E41 auto-merge blocked:"
# Match the cron workflow's PR branch exactly. E20b dispatch opens PRs on
# `ingest/airtable-record-rec<id>` branches — those must NEVER be matched
# here, even if a future operator sets `AUTO_MERGE_HEAD_BRANCH` to one of
# them, because E20b PRs require human review per record. Title-match would
# also reject them (different EXPECTED_TITLE) but defense-in-depth: tightening
# this prefix means `branch_matches()` alone correctly rejects them.
HEAD_BRANCH_PREFIX = "ingest/airtable-articles"
ALLOWED_PATHS = [
    # Articles: only the two canonical files per folder.
    ("articles/", "/article.md"),
    ("articles/", "/metadata.json"),
    # Generated artifacts (rebuilt by rebuild_local.py).
    ("README.md", None),
    ("index.json", None),
    ("sitemap.xml", None),
    ("feed.xml", None),
    ("feed.json", None),
    ("llms.txt", None),
    ("llms-index.txt", None),
    ("llms-full.txt", None),
    ("llms-recent.txt", None),
    # Bundled MCP archive snapshot — added to the ingest pipeline in
    # PR #210 so the Generated artifacts drift check passes on fresh
    # ingest PRs. Must stay in lockstep with `add-paths:` in
    # `.github/workflows/ingest-airtable.yml` and with
    # `tools/check_generated_artifacts.py::ARTIFACTS`; the audit test
    # `test_auto_merge_allowlist_matches_ingest_add_paths` enforces
    # that alignment so a future contributor cannot regress this gap.
    ("mcp-server/src/generated/archive-data.json", None),
]
REQUIRED_CHECKS = (
    "check",        # Generated artifacts
    "e2e",          # E2E tests
    "geo-audit",    # GEO audit
    "gitleaks",     # Secret scanning
    "lychee",       # Article quality audit (link checking)
    "readability",  # Article quality audit (readability)
    "test",         # Run tests
    "vale",         # Article quality audit (Vale)
)
DEFAULT_TIMEOUT_SECONDS = 900   # 15 min — generous for e2e flake.
DEFAULT_POLL_INTERVAL = 30

# mergeStateStatus values `gh pr merge` can actually squash once the eight
# REQUIRED_CHECKS are all SUCCESS: CLEAN (everything green) and UNSTABLE (only
# a non-required / advisory check is red or pending — those never block a
# merge; e.g. the `mcp-server` context an ingest PR triggers via
# archive-data.json). HAS_HOOKS is likewise mergeable. BLOCKED / BEHIND /
# DIRTY / UNKNOWN are NOT mergeable and must keep polling until they settle.
MERGEABLE_MERGE_STATES = ("CLEAN", "UNSTABLE", "HAS_HOOKS")


# --------------------------------------------------------------------------
# Pure functions — unit-testable without the gh CLI.
# --------------------------------------------------------------------------


def is_path_allowed(path: str) -> bool:
    """Return True if `path` matches the ingestion-PR allowlist.

    Article paths must be exactly `articles/<folder>/article.md` or
    `articles/<folder>/metadata.json` — no nested subfolders, no other
    file types. Top-level allowlist entries match by exact path.
    """
    if not path or "\x00" in path:
        return False
    for prefix, suffix in ALLOWED_PATHS:
        if suffix is None:
            if path == prefix:
                return True
            continue
        # Two-segment match: prefix + folder + suffix, no nested slashes.
        if not path.startswith(prefix):
            continue
        if not path.endswith(suffix):
            continue
        middle = path[len(prefix):-len(suffix)]
        if middle and "/" not in middle:
            return True
    return False


def first_disallowed_path(paths) -> str | None:
    """Return the first path that violates the allowlist, or None."""
    for p in paths:
        if not is_path_allowed(p):
            return p
    return None


def title_matches(title: str) -> bool:
    return title == EXPECTED_TITLE


def branch_matches(head_ref: str) -> bool:
    return bool(head_ref) and head_ref.startswith(HEAD_BRANCH_PREFIX)


def required_checks_status(rollup):
    """Classify `statusCheckRollup` against REQUIRED_CHECKS.

    Returns (state, detail). state is one of:
      - "complete-success" — all required checks ended SUCCESS
      - "complete-failure" — at least one required check ended non-SUCCESS
      - "pending"          — at least one required check has no conclusion
      - "missing"          — at least one required check is absent
    """
    by_name = {c.get("name"): c for c in (rollup or [])}
    missing = [n for n in REQUIRED_CHECKS if n not in by_name]
    if missing:
        return ("missing", f"required checks not yet reported: {missing}")
    pending = []
    failed = []
    for name in REQUIRED_CHECKS:
        c = by_name[name]
        conclusion = (c.get("conclusion") or "").upper()
        if not conclusion:
            pending.append(name)
            continue
        if conclusion != "SUCCESS":
            failed.append(f"{name}={conclusion}")
    if failed:
        return ("complete-failure", f"failed: {failed}")
    if pending:
        return ("pending", f"in-progress: {pending}")
    return ("complete-success", "all required checks SUCCESS")


# --------------------------------------------------------------------------
# gh CLI shell-out.
# --------------------------------------------------------------------------


class GhError(RuntimeError):
    pass


def _run_gh(args, repo=None):
    cmd = ["gh"] + args
    if repo:
        cmd += ["-R", repo]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise GhError(
            f"gh {' '.join(args)} exited {proc.returncode}: "
            f"{proc.stderr.strip() or proc.stdout.strip()}"
        )
    return proc.stdout


def find_open_pr(head_branch, repo=None):
    """Return the PR object for the head branch, or None."""
    out = _run_gh(
        [
            "pr",
            "list",
            "--state",
            "open",
            "--head",
            head_branch,
            "--limit",
            "1",
            "--json",
            "number,title,headRefName,baseRefName,mergeable,mergeStateStatus,files,statusCheckRollup,url",
        ],
        repo=repo,
    )
    data = json.loads(out)
    return data[0] if data else None


def _open_blocked_issues(repo=None):
    """Open `E41 auto-merge blocked:` issues, newest first.

    A plain `gh issue list` with a local title filter and deliberately no
    `--search`. The search index is not a dependency worth having here: it is
    eventually consistent, and when the search path errors the dedupe below
    fails open and files a duplicate. That is how one block on PR #453 became
    five issues (#454-#458) while `_has_open_blocked_issue()` resolved `True`
    for the same PR when run against the same repository from a seat whose
    token could search. Listing open issues is exact and needs no index.
    """
    out = _run_gh(
        [
            "issue", "list", "--state", "open",
            "--limit", "100", "--json", "number,title,body",
        ],
        repo=repo,
    )
    return [
        i for i in json.loads(out)
        if (i.get("title") or "").startswith(BLOCKED_TITLE_PREFIX)
    ]


def _referenced_pr_number(body):
    """The PR number an incident body records, or None."""
    m = re.search(r"\*\*PR number:\*\*\s*(\d+)", body or "")
    return int(m.group(1)) if m else None


def _find_open_blocked_issue(pr_num, repo=None):
    """The newest open blocked incident that references PR #pr_num, or None.

    Best-effort: any listing failure returns None so a transient error can
    never suppress a genuinely-needed incident. Failing open costs a duplicate;
    failing closed costs the alarm.
    """
    if not pr_num:
        return None
    try:
        issues = _open_blocked_issues(repo=repo)
    except (GhError, ValueError, TypeError):
        return None
    for issue in issues:
        if _referenced_pr_number(issue.get("body")) == int(pr_num):
            return issue
    return None


def _has_open_blocked_issue(pr_num, repo=None):
    """Whether an open blocked incident already references PR #pr_num."""
    return _find_open_blocked_issue(pr_num, repo=repo) is not None


def _pr_state(pr_number, repo=None):
    """`OPEN` / `MERGED` / `CLOSED` for a PR, or None when it cannot be read."""
    try:
        out = _run_gh(
            ["pr", "view", str(pr_number), "--json", "state"], repo=repo
        )
        return (json.loads(out).get("state") or "").upper() or None
    except (GhError, ValueError, TypeError):
        return None


def _close_issue(number, comment, repo=None):
    """Close an issue, preferring a closing comment but never requiring one.

    Mirrors the workflow cleanup step's token-scope tolerance: the cron token
    can create and close issues but has been observed unauthorized for the
    `addComment` GraphQL mutation (run 26708845288). A comment we cannot write
    must not keep a resolved incident open.
    """
    try:
        _run_gh(
            ["issue", "close", str(number), "--reason", "completed",
             "--comment", comment],
            repo=repo,
        )
        return True
    except GhError:
        _run_gh(["issue", "close", str(number), "--reason", "completed"], repo=repo)
        return True


def close_resolved_blocked_issues(repo=None):
    """Close open blocked incidents whose PR is no longer open.

    Called only from paths where this script has just established that there is
    no blocked candidate: a completed squash-merge, a PR that vanished mid-poll,
    or no open PR at all. An incident whose PR merged or closed is a resolved
    alarm, and a resolved alarm left open is what trains an operator to skim
    past the family (#423, incident dedupe). Never raises and never changes the
    exit code: cleanup cannot be allowed to fail an otherwise successful cron.
    """
    try:
        issues = _open_blocked_issues(repo=repo)
    except (GhError, ValueError, TypeError) as e:
        print(f"[warn] could not list open blocked incidents: {e}", file=sys.stderr)
        return
    for issue in issues:
        pr_num = _referenced_pr_number(issue.get("body"))
        if not pr_num:
            continue
        state = _pr_state(pr_num, repo=repo)
        if state is None or state == "OPEN":
            # Unreadable or still open: leave the alarm standing.
            continue
        try:
            _close_issue(
                issue.get("number"),
                f"Resolved: PR #{pr_num} is {state.lower()}, so the auto-merge "
                f"block this incident reports no longer holds. Closed "
                f"automatically by `tools/auto_merge_ingestion_pr.py`.",
                repo=repo,
            )
            print(
                f"[cleanup] closed incident #{issue.get('number')} "
                f"(PR #{pr_num} {state.lower()})."
            )
        except GhError as e:
            print(
                f"[warn] could not close incident #{issue.get('number')}: {e}",
                file=sys.stderr,
            )


def open_incident_issue(reason, pr=None, repo=None):
    """Report an auto-merge block: one open incident per PR, one comment per run.

    The cron ingest PR uses a fixed head branch, so the same PR persists across
    runs until it merges. The order is the one PR #424 established for the
    workflow's own alarm family, now applied to this one: an open incident for
    this PR gets the run appended as a comment; a new issue is filed only when
    none is open, or when the comment could not be written -- so a failed dedupe
    can never become a lost alarm. What ends the incident is
    `close_resolved_blocked_issues()`.
    """
    pr_num = (pr or {}).get("number", "")
    existing = _find_open_blocked_issue(pr_num, repo=repo) if pr_num else None
    run_url = (
        f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/"
        f"{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/"
        f"{os.environ.get('GITHUB_RUN_ID', '')}"
    )
    pr_url = (pr or {}).get("url", "")
    pr_num = (pr or {}).get("number", "")
    files = [f.get("path") for f in (pr or {}).get("files") or []]
    rollup = (pr or {}).get("statusCheckRollup") or []
    failed_checks = [
        f"{c.get('name')}={c.get('conclusion') or c.get('status')}"
        for c in rollup
        if c.get("name") in REQUIRED_CHECKS
        and (c.get("conclusion") or "").upper() not in ("SUCCESS", "")
    ]

    title = f"E41 auto-merge blocked: {reason[:80]}"
    body_lines = [
        "## Auto-merge blocked",
        "",
        f"**Reason:** {reason}",
        "",
        f"- **PR:** {pr_url or '(none)'}",
        f"- **PR number:** {pr_num or '(none)'}",
        f"- **Workflow run:** {run_url}",
        f"- **Required checks:** {', '.join(REQUIRED_CHECKS)}",
        f"- **Changed files:** {len(files)}",
    ]
    if failed_checks:
        body_lines.append(f"- **Failed/non-success checks:** {failed_checks}")
    if files:
        body_lines.append("")
        body_lines.append("Changed files:")
        for p in files[:50]:
            body_lines.append(f"- `{p}`")
        if len(files) > 50:
            body_lines.append(f"- … ({len(files) - 50} more)")
    body_lines += [
        "",
        "No secret values are recorded in this issue. Triage:",
        "1. If the block is a check failure, fix the underlying issue and let the next cron retry.",
        "2. If the block is an allowlist violation, the PR contains unexpected paths — review and either fix the ingestion script or merge manually after CODEOWNERS approval.",
        "3. If the block is a timeout, increase `AUTO_MERGE_TIMEOUT_SECONDS` or temporarily set `AUTO_MERGE_INGESTION_PRS=0`.",
    ]
    if existing:
        existing_num = existing.get("number")
        try:
            _run_gh(
                ["issue", "comment", str(existing_num),
                 "--body", "\n".join(body_lines)],
                repo=repo,
            )
            print(
                f"[dedup] appended this run to open incident #{existing_num} "
                f"already tracking PR #{pr_num}; not duplicating."
            )
            return
        except GhError as e:
            # A dedupe that cannot write its comment must not swallow the
            # alarm: fall through and file the issue.
            print(
                f"[warn] could not comment on incident #{existing_num} ({e}); "
                f"filing a new incident so the block is still reported.",
                file=sys.stderr,
            )

    try:
        _run_gh(
            ["issue", "create", "--title", title, "--body", "\n".join(body_lines)],
            repo=repo,
        )
    except GhError as e:
        # Best-effort — never let issue creation prevent the script's
        # blocking exit code.
        print(f"[warn] failed to file incident issue: {e}", file=sys.stderr)


def squash_merge(pr_number, repo=None):
    """Squash-merge the PR and delete the head branch."""
    _run_gh(
        ["pr", "merge", str(pr_number), "--squash", "--delete-branch"],
        repo=repo,
    )


# --------------------------------------------------------------------------
# Main orchestration.
# --------------------------------------------------------------------------


def _env_int(name, default):
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def main():
    enabled = os.environ.get("AUTO_MERGE_INGESTION_PRS", "0").strip()
    if enabled != "1":
        print("[skip] AUTO_MERGE_INGESTION_PRS is not '1'; auto-merge disabled.")
        return 0

    head_branch = os.environ.get(
        "AUTO_MERGE_HEAD_BRANCH", "ingest/airtable-articles"
    ).strip()
    repo = os.environ.get("AUTO_MERGE_REPO") or None
    timeout_s = _env_int("AUTO_MERGE_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)
    poll_s = _env_int("AUTO_MERGE_POLL_INTERVAL", DEFAULT_POLL_INTERVAL)

    try:
        pr = find_open_pr(head_branch, repo=repo)
    except GhError as e:
        print(f"[error] gh pr list failed: {e}", file=sys.stderr)
        return 1

    if not pr:
        print(f"[skip] no open PR with head '{head_branch}'; nothing to merge.")
        close_resolved_blocked_issues(repo=repo)
        return 0

    pr_number = pr.get("number")
    pr_url = pr.get("url")
    print(f"[info] candidate PR #{pr_number}: {pr_url}")

    if not branch_matches(pr.get("headRefName") or ""):
        reason = (
            f"head branch '{pr.get('headRefName')}' does not start with "
            f"'{HEAD_BRANCH_PREFIX}'"
        )
        print(f"[block] {reason}")
        open_incident_issue(reason, pr=pr, repo=repo)
        return 1

    if not title_matches(pr.get("title") or ""):
        reason = (
            f"PR title '{pr.get('title')}' does not match expected "
            f"'{EXPECTED_TITLE}'"
        )
        print(f"[block] {reason}")
        open_incident_issue(reason, pr=pr, repo=repo)
        return 1

    paths = [f.get("path") for f in pr.get("files") or []]
    bad = first_disallowed_path(paths)
    if bad:
        reason = f"file '{bad}' not in ingestion allowlist"
        print(f"[block] {reason}")
        open_incident_issue(reason, pr=pr, repo=repo)
        return 1

    # Poll for CI completion + mergeability.
    deadline = time.monotonic() + max(0, timeout_s)
    last_state = None
    last_detail = None
    while True:
        rollup = pr.get("statusCheckRollup") or []
        state, detail = required_checks_status(rollup)
        last_state, last_detail = state, detail
        mergeable = (pr.get("mergeable") or "").upper()
        merge_state = (pr.get("mergeStateStatus") or "").upper()
        print(f"[poll] checks={state} ({detail}); mergeable={mergeable}/{merge_state}")

        if state == "complete-failure":
            # The PR is a real cron product (branch/title/paths already
            # validated). A failing required check is operator-review
            # signal, not a cron-failure signal: the `E41 auto-merge
            # blocked` issue is the single point of truth. Returning 0
            # here keeps the workflow itself in `success()` so the
            # success-path incident-cleanup step (PR #203) can sweep
            # stale `E41 cron ingestion incident:` issues from prior
            # failed cron runs without also filing a duplicate incident
            # for this same event.
            reason = f"required CI failed — {detail}"
            print(f"[block] {reason}")
            open_incident_issue(reason, pr=pr, repo=repo)
            return 0

        # Gate on a mergeable mergeStateStatus, not just mergeable == MERGEABLE.
        # `mergeable` (GraphQL) only reports the absence of merge conflicts;
        # branch-protection readiness lives in `mergeStateStatus`. GitHub
        # recomputes it asynchronously, so for a beat after the last required
        # check flips SUCCESS it can still read BLOCKED. Merging in that window
        # fails with "base branch policy prohibits the merge" (observed on run
        # 29186004190, PR #328).
        #
        # Accept every state gh can actually merge (MERGEABLE_MERGE_STATES:
        # CLEAN, UNSTABLE, HAS_HOOKS) — UNSTABLE means only a non-required /
        # advisory check is red or pending, which never blocks a merge (the
        # eight REQUIRED_CHECKS are already all SUCCESS here). Requiring exactly
        # CLEAN would hang an ingest PR whose advisory `mcp-server` context
        # (triggered via archive-data.json) is red or pending. Only keep polling
        # for the not-yet-mergeable states (BLOCKED / BEHIND / UNKNOWN / …).
        if (
            state == "complete-success"
            and mergeable == "MERGEABLE"
            and merge_state in MERGEABLE_MERGE_STATES
        ):
            break

        if state == "complete-success":
            # Required checks green but the merge state is not yet mergeable
            # (typically a transient BLOCKED/UNKNOWN while GitHub recomputes).
            # Fall through to the poll/timeout loop rather than attempt a merge
            # that branch protection would reject.
            print(
                f"[wait] required checks green but mergeStateStatus="
                f"{merge_state or 'UNKNOWN'}; awaiting a mergeable state "
                f"{MERGEABLE_MERGE_STATES}"
            )

        if time.monotonic() >= deadline:
            # Same rationale as the complete-failure branch above:
            # "checks have not finished yet" is operator-review signal,
            # not a cron-failure signal. The blocked-issue captures it;
            # the cron itself must not also fail and double-file an
            # incident.
            reason = (
                f"timed out after {timeout_s}s waiting for CI; "
                f"last state={state} mergeable={mergeable}/{merge_state} {detail}"
            )
            print(f"[block] {reason}")
            open_incident_issue(reason, pr=pr, repo=repo)
            return 0

        time.sleep(max(1, poll_s))
        try:
            pr = find_open_pr(head_branch, repo=repo)
        except GhError as e:
            print(f"[error] gh pr list during poll failed: {e}", file=sys.stderr)
            return 1
        if not pr:
            print("[skip] PR disappeared during polling (manually merged or closed).")
            close_resolved_blocked_issues(repo=repo)
            return 0

    print(f"[merge] squash-merging PR #{pr_number}")
    try:
        squash_merge(pr_number, repo=repo)
    except GhError as e:
        # Same rationale as the complete-failure / timeout branches: a merge
        # rejection (e.g. a late mergeStateStatus flip back to BLOCKED) is
        # operator-review signal, captured by the single (deduplicated)
        # `E41 auto-merge blocked` issue. Return 0 so the cron itself stays in
        # success() and its failure-path step does not double-file an
        # `E41 cron ingestion incident:` issue for the same event.
        reason = f"gh pr merge failed: {e}"
        print(f"[block] {reason}")
        open_incident_issue(reason, pr=pr, repo=repo)
        return 0
    print(f"[done] PR #{pr_number} squash-merged.")
    close_resolved_blocked_issues(repo=repo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
