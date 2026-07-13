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
import subprocess
import sys
import time

EXPECTED_TITLE = "ingest(articles): add articles from Airtable"
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
    # Generated artifacts (touched by rebuild_local + update_docs).
    ("README.md", None),
    ("ROADMAP.md", None),
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


def _has_open_blocked_issue(pr_num, repo=None):
    """Whether an open `E41 auto-merge blocked` issue already references PR #pr_num.

    Best-effort: a `gh issue list` failure returns False so a transient list
    error can never suppress a genuinely-needed incident.
    """
    if not pr_num:
        return False
    try:
        out = _run_gh(
            [
                "issue", "list", "--state", "open",
                "--search", 'in:title "E41 auto-merge blocked"',
                "--limit", "50", "--json", "number,body",
            ],
            repo=repo,
        )
    except GhError:
        return False
    try:
        needle = f"**PR number:** {pr_num}"
        return any(needle in (i.get("body") or "") for i in json.loads(out))
    except (ValueError, TypeError):
        return False


def open_incident_issue(reason, pr=None, repo=None):
    """File an `E41 auto-merge blocked` issue, deduplicated by PR number.

    The cron ingest PR uses a fixed head branch, so the same PR persists
    across cron runs until it merges. Without dedup, every run that finds the
    same stuck PR files a new issue. Skip creation when an open
    `E41 auto-merge blocked` issue already references this PR number; the
    operator triages the existing one.
    """
    pr_num = (pr or {}).get("number", "")
    if pr_num and _has_open_blocked_issue(pr_num, repo=repo):
        print(
            f"[skip] an open 'E41 auto-merge blocked' issue already tracks "
            f"PR #{pr_num}; not duplicating."
        )
        return
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

        # Require mergeStateStatus == CLEAN, not just mergeable == MERGEABLE.
        # `mergeable` (GraphQL) only reports the absence of merge conflicts;
        # branch-protection readiness lives in `mergeStateStatus`. GitHub
        # recomputes it asynchronously, so for a beat after the last required
        # check flips SUCCESS it can still read BLOCKED. Merging in that window
        # fails with "base branch policy prohibits the merge" (observed on run
        # 29186004190, PR #328). Keep polling until GitHub agrees the PR is
        # CLEAN, so the merge only fires when it can actually succeed.
        if state == "complete-success" and mergeable == "MERGEABLE" and merge_state == "CLEAN":
            break

        if state == "complete-success":
            # Checks are green but the merge state is not yet CLEAN (typically
            # a transient BLOCKED/UNKNOWN while GitHub recomputes). Fall through
            # to the poll/timeout loop rather than attempt a merge that would
            # be rejected by branch protection.
            print(
                f"[wait] required checks green but mergeStateStatus="
                f"{merge_state or 'UNKNOWN'}; awaiting CLEAN"
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
