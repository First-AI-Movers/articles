#!/usr/bin/env python3
"""Tests for tools/arm_dependabot_auto_merge.py (#432).

Covers:
  - is_path_allowed / first_disallowed_path, and their alignment with the
    directories `.github/dependabot.yml` actually configures
  - classify(): the SKIP / REFUSED / ARM decision table
  - failed_check_names() and clause 5: a head whose own surface check has
    already failed is not armed (#489)
  - clause 6: only the `completed` census arms, and a new Dependabot head
    withdraws an arm an earlier head earned (#489, the 2026-10-26 and
    2026-11-02 red merges)
  - main(): the gh shell-outs are stubbed, so the flow is exercised end to end
    without a network, including the typed result line and exit codes
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HEAD = "0123456789abcdef0123456789abcdef01234567"


@pytest.fixture
def mod():
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    m = importlib.import_module("arm_dependabot_auto_merge")
    yield m
    importlib.reload(m)


def _pr(**overrides):
    base = {
        "number": 999,
        "state": "open",
        "merged": False,
        "draft": False,
        "auto_merge": None,
        "html_url": "https://github.com/First-AI-Movers/articles/pull/999",
        "user": {"login": "dependabot[bot]", "type": "Bot"},
        "head": {"ref": "dependabot/npm_and_yarn/mcp-server/qs-6.16.0", "sha": HEAD},
        "base": {"ref": "main"},
    }
    base.update(overrides)
    return base


def _files(*paths):
    return [{"filename": p} for p in paths]


def _check(name, conclusion, *, run_id=1, status="completed"):
    return {"id": run_id, "name": name, "status": status, "conclusion": conclusion}


# --------------------------------------------------------------------------
# Path allowlist
# --------------------------------------------------------------------------


class TestPathAllowlist:
    @pytest.mark.parametrize(
        "path",
        [
            "package.json",
            "package-lock.json",
            "mcp-server/package.json",
            "mcp-server/package-lock.json",
            "og-worker/package.json",
            "og-worker/package-lock.json",
            "tools/requirements.txt",
            ".github/workflows/tests.yml",
            ".github/workflows/e2e.yaml",
        ],
    )
    def test_allowed(self, mod, path):
        assert mod.is_path_allowed(path) is True

    @pytest.mark.parametrize(
        "path",
        [
            "",
            "tools/ingest_airtable.py",
            "mcp-server/src/index.ts",
            "og-worker/wrangler.toml",
            "articles/2026-01-01-x/article.md",
            ".github/dependabot.yml",
            ".github/workflows/nested/x.yml",
            ".github/workflows/",
            ".github/workflows/script.sh",
            ".github/actions/thing/action.yml",
            "somewhere-else/.github/workflows/tests.yml",
            "cookiecutter-archive-template/.github/workflows/tests.yml",
            # Not watched since #362 removed the inert template entry.
            "cookiecutter-archive-template/{{cookiecutter.repo_slug}}/.github/workflows/tests.yml",
            "/package.json",
            "../package.json",
            "tools/../package.json",
            "package.json\x00",
            "requirements.txt",
        ],
    )
    def test_disallowed(self, mod, path):
        assert mod.is_path_allowed(path) is False

    def test_first_disallowed_path(self, mod):
        assert mod.first_disallowed_path(["package.json", "tools/requirements.txt"]) is None
        assert mod.first_disallowed_path(["package.json", "README.md", "x"]) == "README.md"

    def test_allowlist_covers_every_dependabot_directory(self, mod):
        """Every ecosystem/directory in .github/dependabot.yml has its manifest in
        ALLOWED_PATHS, and ALLOWED_PATHS names no directory Dependabot is not
        configured for -- the two files cannot drift apart silently."""
        yaml = pytest.importorskip("yaml")
        cfg = yaml.safe_load((REPO_ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8"))
        manifests = {
            "pip": ("requirements.txt",),
            "npm": ("package.json", "package-lock.json"),
            "github-actions": (),
        }
        expected: set[str] = set()
        expected_roots: set[str] = set()
        for entry in cfg["updates"]:
            eco = entry["package-ecosystem"]
            dirs = entry.get("directories") or [entry["directory"]]
            assert eco in manifests, f"unknown ecosystem {eco!r} in dependabot.yml"
            for d in dirs:
                prefix = d.strip("/")
                prefix = f"{prefix}/" if prefix else ""
                if eco == "github-actions":
                    # A github-actions entry watches `<directory>/.github/workflows/`,
                    # so its bumps change files there and the arming must accept them.
                    expected_roots.add(prefix)
                    assert mod.is_path_allowed(f"{prefix}.github/workflows/x.yml"), (
                        f"dependabot.yml watches github-actions in {d!r}, but the arming "
                        f"allowlist rejects {prefix}.github/workflows/x.yml"
                    )
                    continue
                for m in manifests[eco]:
                    expected.add(f"{prefix}{m}")
        assert set(mod.ALLOWED_PATHS) == expected, (
            f"ALLOWED_PATHS must equal the manifests of every pip/npm directory in "
            f".github/dependabot.yml; expected {sorted(expected)}, got {sorted(mod.ALLOWED_PATHS)}"
        )
        assert set(mod.WORKFLOW_ROOTS) == expected_roots, (
            f"WORKFLOW_ROOTS must equal the github-actions directories in "
            f".github/dependabot.yml; expected {sorted(expected_roots)}, "
            f"got {sorted(mod.WORKFLOW_ROOTS)}"
        )

    def test_every_github_actions_directory_exists_on_disk(self):
        """Every `github-actions` directory in dependabot.yml really holds
        workflows.

        An entry whose `directory:` resolves to nothing is silently inert: it
        parses, it appears to grant coverage, and it bumps nothing. That is not
        hypothetical here: the cookiecutter template's entry, whose directory
        name is literally `{{cookiecutter.repo_slug}}`, never scheduled a single
        Dependabot job in eight weeks and was removed (#362).

        This test cannot see Dependabot's own path resolution. What it owns is
        the failure mode that IS checkable: the directory must exist and contain
        at least one workflow, so a rename or a typo fails here instead of
        quietly widening the gap.
        """
        yaml = pytest.importorskip("yaml")
        cfg = yaml.safe_load(
            (REPO_ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
        )
        checked = 0
        for entry in cfg["updates"]:
            if entry["package-ecosystem"] != "github-actions":
                continue
            for d in entry.get("directories") or [entry["directory"]]:
                wf_dir = REPO_ROOT / d.strip("/") / ".github" / "workflows"
                assert wf_dir.is_dir(), (
                    f"dependabot.yml watches github-actions in {d!r}, but "
                    f"{wf_dir.relative_to(REPO_ROOT)} is not a directory -- that "
                    f"entry is inert (#362)"
                )
                assert list(wf_dir.glob("*.yml")) or list(wf_dir.glob("*.yaml")), (
                    f"{wf_dir.relative_to(REPO_ROOT)} holds no workflow file, so "
                    f"the github-actions entry for {d!r} has nothing to govern"
                )
                checked += 1
        assert checked >= 1, (
            f"expected at least the root to be watched for github-actions; checked {checked}"
        )


# --------------------------------------------------------------------------
# classify()
# --------------------------------------------------------------------------


class TestClassify:
    def test_arms_a_clean_dependabot_pr(self, mod):
        verdict, reason = mod.classify(_pr(), _files("mcp-server/package-lock.json"), HEAD)
        assert verdict == "ARM"
        assert HEAD[:12] in reason

    def test_no_pr_skips(self, mod):
        assert mod.classify(None, [], HEAD)[0] == "SKIP"

    @pytest.mark.parametrize(
        "overrides",
        [
            {"state": "closed"},
            {"merged": True},
            {"auto_merge": {"enabled_by": {"login": "x"}}},
            {"user": {"login": "hpcosta", "type": "User"}},
            {"user": {"login": "dependabot[bot]", "type": "User"}},
            {"user": {"login": "aeos-autonomous-main[bot]", "type": "Bot"}},
        ],
    )
    def test_not_this_scripts_job_skips(self, mod, overrides):
        verdict, _ = mod.classify(_pr(**overrides), _files("package.json"), HEAD)
        assert verdict == "SKIP"

    def test_head_moved_skips_for_the_next_event(self, mod):
        verdict, reason = mod.classify(_pr(), _files("package.json"), "f" * 40)
        assert verdict == "SKIP"
        assert "head moved" in reason

    def test_missing_expected_head_skips(self, mod):
        assert mod.classify(_pr(), _files("package.json"), "")[0] == "SKIP"

    @pytest.mark.parametrize(
        "overrides, needle",
        [
            ({"head": {"ref": "feature/x", "sha": HEAD}}, "dependabot/"),
            ({"draft": True}, "draft"),
            ({"base": {"ref": "release"}}, "base branch"),
        ],
    )
    def test_ineligible_dependabot_pr_is_refused(self, mod, overrides, needle):
        verdict, reason = mod.classify(_pr(**overrides), _files("package.json"), HEAD)
        assert verdict == "REFUSED"
        assert needle in reason

    def test_non_dependency_path_is_refused(self, mod):
        verdict, reason = mod.classify(
            _pr(), _files("mcp-server/package-lock.json", "mcp-server/src/index.ts"), HEAD
        )
        assert verdict == "REFUSED"
        assert "mcp-server/src/index.ts" in reason

    def test_empty_change_set_is_refused(self, mod):
        assert mod.classify(_pr(), [], HEAD)[0] == "REFUSED"

    def test_workflow_bump_is_eligible(self, mod):
        """A github-actions bump edits workflow files; the organization gate's
        workflow policy judges those bytes, this script only arms."""
        pr = _pr(head={"ref": "dependabot/github_actions/actions/checkout-8", "sha": HEAD})
        assert mod.classify(pr, _files(".github/workflows/tests.yml"), HEAD)[0] == "ARM"


# --------------------------------------------------------------------------
# failed_check_names() and clause 5: a red surface withholds arming (#489)
# --------------------------------------------------------------------------


class TestFailedCheckNames:
    def test_no_check_runs_is_not_a_failure(self, mod):
        """The ordinary arming window: nothing has reported yet."""
        assert mod.failed_check_names([]) == []
        assert mod.failed_check_names(None) == []

    @pytest.mark.parametrize("conclusion", ["failure", "timed_out", "action_required"])
    def test_blocking_conclusions_are_reported(self, mod, conclusion):
        assert mod.failed_check_names([_check("mcp-server", conclusion)]) == ["mcp-server"]

    @pytest.mark.parametrize("conclusion", ["success", "skipped", "neutral", "cancelled", "stale"])
    def test_non_verdicts_are_not_failures(self, mod, conclusion):
        """`skipped` is what every `paths:`-filtered workflow concludes when it
        did not apply, and what the unarmed `main-smoke` revert legs conclude on
        a healthy head -- treating it as red would refuse every PR."""
        assert mod.failed_check_names([_check("og-worker", conclusion)]) == []

    def test_a_still_running_check_is_not_a_failure(self, mod):
        assert mod.failed_check_names(
            [_check("test", None, status="in_progress"), _check("e2e", None, status="queued")]
        ) == []

    def test_newest_attempt_per_name_wins(self, mod):
        """A check re-run green must retire its own earlier red: same name, from
        a later workflow run, so the higher check-run id is the live verdict."""
        runs = [_check("mcp-server", "failure", run_id=1), _check("mcp-server", "success", run_id=2)]
        assert mod.failed_check_names(runs) == []
        assert mod.failed_check_names(list(reversed(runs))) == [], "order must not matter"

    def test_a_newer_red_overrides_an_earlier_green(self, mod):
        runs = [_check("og-worker", "success", run_id=5), _check("og-worker", "failure", run_id=9)]
        assert mod.failed_check_names(runs) == ["og-worker"]

    def test_every_failing_name_is_listed_sorted(self, mod):
        runs = [
            _check("og-worker", "failure", run_id=2),
            _check("mcp-server", "failure", run_id=1),
            _check("test", "success", run_id=3),
        ]
        assert mod.failed_check_names(runs) == ["mcp-server", "og-worker"]

    def test_unnamed_and_malformed_entries_are_ignored(self, mod):
        runs = [_check("", "failure"), {"id": 2, "status": "completed"}, "nonsense", None]
        assert mod.failed_check_names(runs) == []


class TestClauseFiveRefusal:
    """#485/#486 and #498/#499 merged with `mcp-server`/`og-worker` red because
    neither is a required context. Clause 5 withholds this script's arming for
    exactly that head state.
    """

    def test_a_red_surface_refuses_the_arming(self, mod):
        verdict, reason = mod.classify(
            _pr(),
            _files("mcp-server/package-lock.json"),
            HEAD,
            [_check("mcp-server", "failure")],
        )
        assert verdict == "REFUSED"
        assert "mcp-server" in reason
        assert HEAD[:12] in reason

    def test_a_green_head_still_arms(self, mod):
        verdict, _ = mod.classify(
            _pr(),
            _files("mcp-server/package-lock.json"),
            HEAD,
            [_check("mcp-server", "success"), _check("test", "success", run_id=2)],
        )
        assert verdict == "ARM"

    def test_checks_still_running_still_arm(self, mod):
        """Arming while the gate is pending is the lifecycle, not a hazard."""
        verdict, _ = mod.classify(
            _pr(),
            _files("package.json"),
            HEAD,
            [_check("test", None, status="in_progress")],
        )
        assert verdict == "ARM"

    def test_an_earlier_refusal_still_takes_precedence(self, mod):
        """A disallowed path is the more fundamental refusal and keeps its reason,
        so the existing routing does not change shape when a surface is also red."""
        verdict, reason = mod.classify(
            _pr(),
            _files("package.json", "tools/build_embeddings.py"),
            HEAD,
            [_check("mcp-server", "failure")],
        )
        assert verdict == "REFUSED"
        assert "tools/build_embeddings.py" in reason

    def test_the_refusal_comment_routes_to_489(self, mod):
        _, reason = mod.classify(
            _pr(), _files("package.json"), HEAD, [_check("og-worker", "failure")]
        )
        body = mod.refusal_comment(reason, "https://example.invalid/run/1")
        assert body.startswith(mod.REFUSAL_MARKER)
        assert "og-worker" in body
        assert "#489" in body
        assert "required-context list and branch protection are unchanged" in body

    def test_an_unrelated_refusal_comment_stays_unchanged(self, mod):
        body = mod.refusal_comment("pull request is a draft", "https://example.invalid/run/1")
        assert "#489" not in body
        assert "#432" in body


# --------------------------------------------------------------------------
# main() with gh stubbed
# --------------------------------------------------------------------------


class _Gh:
    """Records every gh invocation and answers from a scripted PR state.

    Matches the exact argument shapes the module issues, so a change in how the
    module calls gh fails here instead of being silently answered.
    """

    def __init__(
        self,
        pr,
        files,
        *,
        merged_after=False,
        armed_after=True,
        comments="",
        check_runs=(),
        disarm_sticks=True,
        merged_before_disarm=False,
    ):
        self.pr = pr
        self.files = files
        self.merged_after = merged_after
        self.armed_after = armed_after
        self.disarm_sticks = disarm_sticks
        self.merged_before_disarm = merged_before_disarm
        self.comments = comments
        self.check_runs = list(check_runs)
        self.calls: list[list[str]] = []

    def __call__(self, args, *, check=True):
        self.calls.append(list(args))
        repo = "First-AI-Movers/articles"
        n = self.pr["number"]
        if args[:2] == ["api", "--paginate"] and "/check-runs" in args[2]:
            return "\n".join(json.dumps(c) for c in self.check_runs)
        if args[:2] == ["pr", "merge"] and "--disable-auto" in args:
            assert args == ["pr", "merge", str(n), "--repo", repo, "--disable-auto"], args
            if self.merged_before_disarm:
                self.pr = dict(self.pr, merged=True, state="closed")
            elif self.disarm_sticks:
                self.pr = dict(self.pr, auto_merge=None)
            return ""
        if args[:2] == ["pr", "merge"]:
            if self.merged_after:
                self.pr = dict(self.pr, merged=True, state="closed")
            elif self.armed_after:
                self.pr = dict(self.pr, auto_merge={"enabled_by": {"login": "app"}})
            return ""
        if args == ["api", f"repos/{repo}/pulls/{n}"]:
            return json.dumps(self.pr)
        if args[:4] == ["api", f"repos/{repo}/pulls", "-X", "GET"]:
            return json.dumps([self.pr]) if self.pr.get("state") == "open" else "[]"
        if args == ["api", "--paginate", f"repos/{repo}/pulls/{n}/files", "--jq", ".[]"]:
            return "\n".join(json.dumps(f) for f in self.files)
        if args == ["api", "--paginate", f"repos/{repo}/issues/{n}/comments", "--jq", ".[].body"]:
            return self.comments
        if args[:4] == ["api", "-X", "POST", f"repos/{repo}/issues/{n}/comments"]:
            return "{}"
        raise AssertionError(f"unexpected gh call: {args}")


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_REPOSITORY", "First-AI-Movers/articles")
    monkeypatch.setenv("DEPENDABOT_PR_NUMBER", "999")
    monkeypatch.setenv("DEPENDABOT_HEAD_BRANCH", "dependabot/npm_and_yarn/mcp-server/qs-6.16.0")
    monkeypatch.setenv("DEPENDABOT_HEAD_SHA", HEAD)
    monkeypatch.setenv("DEPENDABOT_EVENT_ACTION", "completed")
    monkeypatch.setenv("GITHUB_RUN_ID", "1")
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    return summary


def test_main_arms_and_reports(mod, env, monkeypatch, capsys):
    gh = _Gh(_pr(), _files("mcp-server/package-lock.json"))
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 0
    out = capsys.readouterr().out
    assert f"{mod.RESULT_PREFIX} ARMED" in out
    merges = [c for c in gh.calls if c[:2] == ["pr", "merge"]]
    assert merges == [["pr", "merge", "999", "--repo", "First-AI-Movers/articles", "--squash", "--auto"]]
    assert "ARMED" in env.read_text(encoding="utf-8")


def test_main_reports_merged_when_gh_merged_immediately(mod, env, monkeypatch, capsys):
    """GitHub refuses to arm a PR already in clean status, so gh merges it at that
    head instead; the script reads the outcome back from the PR."""
    gh = _Gh(_pr(), _files("tools/requirements.txt"), merged_after=True)
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 0
    assert f"{mod.RESULT_PREFIX} MERGED" in capsys.readouterr().out


def test_main_fails_when_gh_claims_success_but_nothing_changed(mod, env, monkeypatch, capsys):
    gh = _Gh(_pr(), _files("package.json"), armed_after=False)
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 1
    assert f"{mod.RESULT_PREFIX} REFUSED" in capsys.readouterr().out


def test_main_skips_without_writing(mod, env, monkeypatch, capsys):
    gh = _Gh(_pr(auto_merge={"enabled_by": {"login": "app"}}), _files("package.json"))
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 0
    assert f"{mod.RESULT_PREFIX} SKIP" in capsys.readouterr().out
    assert not [c for c in gh.calls if c[:2] == ["pr", "merge"] or "-X" in c]


def test_main_refuses_posts_once_and_fails(mod, env, monkeypatch, capsys):
    gh = _Gh(_pr(), _files("package.json", "tools/build_embeddings.py"))
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 1
    out = capsys.readouterr().out
    assert f"{mod.RESULT_PREFIX} REFUSED" in out
    posts = [c for c in gh.calls if "-X" in c and "POST" in c]
    assert len(posts) == 1
    body = posts[0][-1]
    assert body.startswith("body=" + mod.REFUSAL_MARKER)
    assert "tools/build_embeddings.py" in body
    assert not [c for c in gh.calls if c[:2] == ["pr", "merge"]]

    # Second run for the same head and reason: the existing comment is found, no duplicate.
    gh2 = _Gh(_pr(), _files("package.json", "tools/build_embeddings.py"), comments=body[len("body="):])
    monkeypatch.setattr(mod, "_run_gh", gh2)
    assert mod.main() == 1
    assert not [c for c in gh2.calls if "-X" in c and "POST" in c]


def test_main_resolves_pr_by_head_branch_when_number_missing(mod, env, monkeypatch, capsys):
    monkeypatch.setenv("DEPENDABOT_PR_NUMBER", "")
    gh = _Gh(_pr(), _files("og-worker/package.json"))
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 0
    assert f"{mod.RESULT_PREFIX} ARMED" in capsys.readouterr().out
    lookups = [c for c in gh.calls if any("head=First-AI-Movers:dependabot/" in a for a in c)]
    assert lookups, "the PR must be looked up by owner:head-branch when no number is given"


def test_main_refuses_a_red_surface_without_merging(mod, env, monkeypatch, capsys):
    """The #485/#486 head state, end to end: the bump is not armed, not merged,
    and the PR carries the reason (#489)."""
    gh = _Gh(
        _pr(),
        _files("mcp-server/package-lock.json"),
        check_runs=[_check("mcp-server", "failure"), _check("test", "success", run_id=2)],
    )
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 1, "the refusal must be visible as a failed run"
    out = capsys.readouterr().out
    assert f"{mod.RESULT_PREFIX} REFUSED" in out
    assert "mcp-server" in out
    assert not [c for c in gh.calls if c[:2] == ["pr", "merge"]], "nothing may be merged or armed"
    posts = [c for c in gh.calls if "-X" in c and "POST" in c]
    assert len(posts) == 1
    assert "#489" in posts[0][-1]


def test_main_arms_when_the_head_is_green(mod, env, monkeypatch, capsys):
    gh = _Gh(
        _pr(),
        _files("mcp-server/package-lock.json"),
        check_runs=[_check("mcp-server", "success"), _check("og-worker", "skipped", run_id=2)],
    )
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 0
    assert f"{mod.RESULT_PREFIX} ARMED" in capsys.readouterr().out


def test_main_reads_check_runs_for_the_event_head(mod, env, monkeypatch, capsys):
    """The census must be taken on the SHA the event reported, not on `main`."""
    gh = _Gh(_pr(), _files("package.json"))
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 0
    census = [c for c in gh.calls if any("/check-runs" in a for a in c)]
    assert census, "clause 5 needs the head's check runs"
    assert any(HEAD in a for c in census for a in c)


def test_main_without_repository_is_a_typed_refusal(mod, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    assert mod.main() == 1
    assert f"{mod.RESULT_PREFIX} REFUSED" in capsys.readouterr().out


# --------------------------------------------------------------------------
# A transient PR state is not a refusal (#432, PR #468)
# --------------------------------------------------------------------------

UNSTABLE_ERR = (
    "gh pr merge 468 --repo First-AI-Movers/articles --squash --auto exited 1: "
    "GraphQL: Pull request Pull request is in unstable status"
)


class TestRetryableGhFailure:
    """GitHub can decline an arm for a PR state that is not a refusal (#468 was
    `unstable` while its checks ran). Reporting that as REFUSED made every
    healthy Dependabot PR a red run claiming a refusal that never happened.
    Since clause 6 only `completed` arms, so the reason names what retries it:
    a new head, or a re-run of `Run tests`.
    """

    @pytest.mark.parametrize("message", [
        UNSTABLE_ERR,
        "GraphQL: Pull request is in dirty status",
        "GraphQL: Pull request is in blocked status",
        "GraphQL: Pull request is in unknown status",
        "GraphQL: Pull request is not mergeable",
        "GraphQL: Base branch was modified. Review and try the merge again.",
        "graphql: pull request IS IN UNSTABLE STATUS",  # case-insensitive
    ])
    def test_transient_states_are_retryable(self, mod, message):
        assert mod.is_retryable_gh_failure(message) is True

    @pytest.mark.parametrize("message", [
        "HTTP 401: Bad credentials",
        "HTTP 404: Not Found",
        "GraphQL: Resource not accessible by integration",
        "gh: command not found",
        "",
    ])
    def test_real_failures_are_not_retryable(self, mod, message):
        assert mod.is_retryable_gh_failure(message) is False

    def test_main_skips_and_exits_zero_on_a_transient_state(
        self, mod, env, monkeypatch, capsys
    ):
        """The whole point: exit 0 so Actions stays green for a PR that is
        simply not ready, and say truthfully what will retry it."""
        gh = _Gh(_pr(), _files("package.json"))
        real = gh.__call__

        def failing(args, *, check=True):
            if args[:2] == ["pr", "merge"]:
                gh.calls.append(list(args))
                raise mod.GhError(UNSTABLE_ERR)
            return real(args, check=check)

        monkeypatch.setattr(mod, "_run_gh", failing)
        assert mod.main() == 0, "a transient state must not fail the run"
        out = capsys.readouterr().out
        assert f"{mod.RESULT_PREFIX} SKIP" in out
        assert f"{mod.RESULT_PREFIX} REFUSED" not in out
        assert "re-run of `Run tests`" in out, "the reason must name what retries it"
        assert "awaiting" not in out, "no later event retries this head; do not promise one"
        assert "unstable status" in out, "and carry the provider's own wording"

    def test_main_still_fails_on_a_real_gh_failure(
        self, mod, env, monkeypatch, capsys
    ):
        """Bad credentials must stay a red REFUSED -- this must not become a
        blanket swallow of every gh error."""
        gh = _Gh(_pr(), _files("package.json"))
        real = gh.__call__

        def failing(args, *, check=True):
            if args[:2] == ["pr", "merge"]:
                raise mod.GhError("HTTP 401: Bad credentials")
            return real(args, check=check)

        monkeypatch.setattr(mod, "_run_gh", failing)
        assert mod.main() == 1
        out = capsys.readouterr().out
        assert f"{mod.RESULT_PREFIX} REFUSED" in out
        assert "Bad credentials" in out

    def test_a_transient_state_posts_no_refusal_comment(
        self, mod, env, monkeypatch
    ):
        """#468 carried no refusal comment and must never carry one: a PR that
        merged two minutes later must not be told it was refused."""
        gh = _Gh(_pr(), _files("package.json"))
        real = gh.__call__

        def failing(args, *, check=True):
            if args[:2] == ["pr", "merge"]:
                gh.calls.append(list(args))
                raise mod.GhError(UNSTABLE_ERR)
            return real(args, check=check)

        monkeypatch.setattr(mod, "_run_gh", failing)
        assert mod.main() == 0
        assert not [c for c in gh.calls if "-X" in c and "POST" in c], (
            "no comment may be posted for a state the next event resolves"
        )


# --------------------------------------------------------------------------
# Clause 6: only the `completed` census arms; a new head withdraws an old arm
# (#489, the red merges of 2026-10-26 and 2026-11-02)
# --------------------------------------------------------------------------

ARMED = {"enabled_by": {"login": "articles-automation[bot]"}, "merge_method": "squash"}
OTHER = "fedcba9876543210fedcba9876543210fedcba98"


class TestClauseSix:
    """Every Dependabot PR of those two Mondays was armed by the `requested`
    invocation before any surface reported, so clause 5's census read nothing
    red; a rebase kept the arm, and every later invocation answered "already
    armed" without looking. These pin the decision table that closes both holes.
    """

    def test_requested_never_arms_even_a_clean_head(self, mod):
        verdict, reason = mod.classify(
            _pr(), _files("package.json"), HEAD, [], mod.EVENT_REQUESTED
        )
        assert verdict == "SKIP"
        assert "completed" in reason and HEAD[:12] in reason

    def test_requested_with_checks_in_flight_is_the_522_state_and_does_not_arm(self, mod):
        """#522 at 09:22:4xZ: `mcp-server` and `test` still running. The old
        census armed here; the surface failed seconds later."""
        verdict, _ = mod.classify(
            _pr(),
            _files("mcp-server/package.json", "mcp-server/package-lock.json"),
            HEAD,
            [
                _check("mcp-server", None, status="in_progress"),
                _check("test", None, run_id=2, status="in_progress"),
            ],
            mod.EVENT_REQUESTED,
        )
        assert verdict == "SKIP"

    def test_requested_on_an_armed_pr_disarms(self, mod):
        """A Dependabot rebase: GitHub kept the arm across the force-push."""
        verdict, reason = mod.classify(
            _pr(auto_merge=ARMED), _files("package.json"), HEAD, [], mod.EVENT_REQUESTED
        )
        assert verdict == "DISARM"
        assert HEAD[:12] in reason

    def test_completed_on_an_armed_red_head_is_refused_not_skipped(self, mod):
        """The old table returned SKIP "already armed" before the census, which
        is how #538 merged red at its third head."""
        verdict, reason = mod.classify(
            _pr(auto_merge=ARMED),
            _files("mcp-server/package-lock.json"),
            HEAD,
            [_check("mcp-server", "failure"), _check("test", "failure", run_id=2)],
            mod.EVENT_COMPLETED,
        )
        assert verdict == "REFUSED"
        assert "mcp-server" in reason and "test" in reason

    def test_completed_on_an_armed_clean_head_skips(self, mod):
        verdict, reason = mod.classify(
            _pr(auto_merge=ARMED),
            _files("package.json"),
            HEAD,
            [_check("test", "success")],
            mod.EVENT_COMPLETED,
        )
        assert verdict == "SKIP"
        assert "already armed" in reason

    def test_completed_on_a_clean_unarmed_head_arms(self, mod):
        verdict, _ = mod.classify(
            _pr(), _files("package.json"), HEAD, [_check("test", "success")], mod.EVENT_COMPLETED
        )
        assert verdict == "ARM"

    @pytest.mark.parametrize("action", ["", "rerequested", "COMPLETED"])
    def test_an_unknown_event_action_never_arms(self, mod, action):
        verdict, reason = mod.classify(_pr(), _files("package.json"), HEAD, [], action)
        assert verdict == "REFUSED"
        assert "event action" in reason

    def test_a_disallowed_path_is_refused_at_requested_too(self, mod):
        """Content refusals keep their timing: visible on the first event."""
        verdict, reason = mod.classify(
            _pr(), _files("tools/build_embeddings.py"), HEAD, [], mod.EVENT_REQUESTED
        )
        assert verdict == "REFUSED"
        assert "tools/build_embeddings.py" in reason

    def test_head_moved_still_skips_before_any_disarm(self, mod):
        """An event for a superseded head must not touch the PR: the new head's
        own `requested` event owns the disarm."""
        verdict, _ = mod.classify(
            _pr(auto_merge=ARMED), _files("package.json"), OTHER, [], mod.EVENT_REQUESTED
        )
        assert verdict == "SKIP"


def _merges(gh):
    return [c for c in gh.calls if c[:2] == ["pr", "merge"]]


def _posts(gh):
    return [c for c in gh.calls if "-X" in c and "POST" in c]


def test_main_requested_defers_without_writing(mod, env, monkeypatch, capsys):
    monkeypatch.setenv("DEPENDABOT_EVENT_ACTION", "requested")
    gh = _Gh(_pr(), _files("mcp-server/package-lock.json"))
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 0
    assert f"{mod.RESULT_PREFIX} SKIP" in capsys.readouterr().out
    assert not _merges(gh) and not _posts(gh)


def test_main_requested_on_an_armed_pr_withdraws_the_arm(mod, env, monkeypatch, capsys):
    monkeypatch.setenv("DEPENDABOT_EVENT_ACTION", "requested")
    gh = _Gh(_pr(auto_merge=ARMED), _files("package.json"))
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 0
    assert f"{mod.RESULT_PREFIX} DISARMED" in capsys.readouterr().out
    assert _merges(gh) == [["pr", "merge", "999", "--repo", "First-AI-Movers/articles", "--disable-auto"]]
    assert gh.pr["auto_merge"] is None
    assert not _posts(gh), "a withdrawn arm is not a refusal"


def test_main_completed_red_and_armed_disarms_before_it_refuses(mod, env, monkeypatch, capsys):
    gh = _Gh(
        _pr(auto_merge=ARMED),
        _files("og-worker/package-lock.json"),
        check_runs=[_check("og-worker", "failure"), _check("test", "failure", run_id=2)],
    )
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 1
    assert f"{mod.RESULT_PREFIX} REFUSED" in capsys.readouterr().out
    assert gh.pr["auto_merge"] is None, "a red head must not stay armed"
    disarm_at = next(i for i, c in enumerate(gh.calls) if "--disable-auto" in c)
    post_at = next(i for i, c in enumerate(gh.calls) if "-X" in c and "POST" in c)
    assert disarm_at < post_at, "the arm is withdrawn before the refusal says so"
    assert "has been withdrawn" in _posts(gh)[0][-1]
    assert not [c for c in _merges(gh) if "--auto" in c], "nothing may be armed"


def test_main_completed_red_and_unarmed_refuses_without_a_disarm_call(mod, env, monkeypatch):
    gh = _Gh(_pr(), _files("package.json"), check_runs=[_check("mcp-server", "failure")])
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 1
    assert not _merges(gh)


@pytest.mark.parametrize(
    "stub, needle",
    [
        ({"disarm_sticks": False}, "still armed"),
        ({"merged_before_disarm": True}, "merged before"),
    ],
)
def test_main_a_failed_disarm_fails_the_run(mod, env, monkeypatch, capsys, stub, needle):
    """A live arm that should have been withdrawn must be loud."""
    monkeypatch.setenv("DEPENDABOT_EVENT_ACTION", "requested")
    gh = _Gh(_pr(auto_merge=ARMED), _files("package.json"), **stub)
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 1
    out = capsys.readouterr().out
    assert f"{mod.RESULT_PREFIX} REFUSED" in out
    assert needle in out


def test_main_a_disarm_failure_is_never_treated_as_transient(mod, env, monkeypatch, capsys):
    """The retryable allowance belongs to arming. The same provider wording on
    a disarm leaves a red head armed, so it must fail the run."""
    monkeypatch.setenv("DEPENDABOT_EVENT_ACTION", "requested")
    gh = _Gh(_pr(auto_merge=ARMED), _files("package.json"))
    real = gh.__call__

    def failing(args, *, check=True):
        if "--disable-auto" in args:
            raise mod.GhError(UNSTABLE_ERR)
        return real(args, check=check)

    monkeypatch.setattr(mod, "_run_gh", failing)
    assert mod.main() == 1
    assert f"{mod.RESULT_PREFIX} REFUSED" in capsys.readouterr().out


def test_replay_of_522_never_arms_a_head_that_goes_red(mod, env, monkeypatch, capsys):
    """#522 on 2026-10-26, as event sequence: requested on the first head while
    `mcp-server` runs, completed with it red; Dependabot rebases; requested and
    completed on the new head, red again. Under clause 6 no step arms it."""
    first = _pr()
    runs_red = [_check("mcp-server", "failure"), _check("test", "failure", run_id=2)]

    monkeypatch.setenv("DEPENDABOT_EVENT_ACTION", "requested")
    gh = _Gh(first, _files("mcp-server/package-lock.json"),
             check_runs=[_check("mcp-server", None, status="in_progress")])
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 0
    assert not _merges(gh)

    monkeypatch.setenv("DEPENDABOT_EVENT_ACTION", "completed")
    gh = _Gh(gh.pr, _files("mcp-server/package-lock.json"), check_runs=runs_red)
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 1
    assert not _merges(gh)

    rebased = dict(gh.pr, head=dict(gh.pr["head"], sha=OTHER))
    monkeypatch.setenv("DEPENDABOT_HEAD_SHA", OTHER)
    for action, expected_rc in (("requested", 0), ("completed", 1)):
        monkeypatch.setenv("DEPENDABOT_EVENT_ACTION", action)
        gh = _Gh(rebased, _files("mcp-server/package-lock.json"), check_runs=runs_red)
        monkeypatch.setattr(mod, "_run_gh", gh)
        assert mod.main() == expected_rc
        assert not [c for c in _merges(gh) if "--auto" in c], f"{action}: nothing may be armed"
        rebased = gh.pr
    assert not rebased.get("auto_merge")
    capsys.readouterr()
