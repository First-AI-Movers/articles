#!/usr/bin/env python3
"""Tests for tools/main_red_watchdog.py and tools/ci_check_runs.py (#489).

Covers:
  - the shared "what counts as red" definition, including that prevention and
    detection read it from one place
  - classify(): RED / GREEN / SKIP for one head's check runs
  - issue_body(): identifiers and routing, never log output
  - main(): the gh shell-outs are stubbed, so open / refresh / close are
    exercised end to end without a network
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HEAD = "abcdef0123456789abcdef0123456789abcdef01"
REPO = "First-AI-Movers/articles"


@pytest.fixture
def mod():
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    m = importlib.import_module("main_red_watchdog")
    yield m
    importlib.reload(m)


@pytest.fixture
def shared():
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    m = importlib.import_module("ci_check_runs")
    yield m
    importlib.reload(m)


def _check(name, conclusion, *, run_id=1, status="completed", url=None):
    run = {"id": run_id, "name": name, "status": status, "conclusion": conclusion}
    if url:
        run["details_url"] = url
    return run


# --------------------------------------------------------------------------
# The shared definition of "red"
# --------------------------------------------------------------------------


class TestSharedDefinition:
    @pytest.mark.parametrize("conclusion", ["failure", "timed_out", "action_required"])
    def test_blocking_conclusions(self, shared, conclusion):
        assert shared.failed_check_names([_check("mcp-server", conclusion)]) == ["mcp-server"]

    @pytest.mark.parametrize("conclusion", ["success", "skipped", "neutral", "cancelled", "stale"])
    def test_non_verdicts_are_not_red(self, shared, conclusion):
        """`skipped` is what every `paths:`-filtered workflow concludes when it
        did not apply, and what the unarmed `main-smoke` revert legs conclude on
        a healthy head."""
        assert shared.failed_check_names([_check("og-worker", conclusion)]) == []

    def test_still_running_is_not_red(self, shared):
        assert shared.failed_check_names([_check("test", None, status="in_progress")]) == []

    def test_newest_attempt_per_name_wins(self, shared):
        runs = [_check("mcp-server", "failure", run_id=1), _check("mcp-server", "success", run_id=2)]
        assert shared.failed_check_names(runs) == []
        assert shared.failed_check_names(list(reversed(runs))) == []

    def test_a_newer_red_overrides_an_earlier_green(self, shared):
        runs = [_check("og-worker", "success", run_id=5), _check("og-worker", "failure", run_id=9)]
        assert shared.failed_check_names(runs) == ["og-worker"]

    def test_malformed_entries_are_ignored(self, shared):
        assert shared.failed_check_names([_check("", "failure"), "nonsense", None, {}]) == []

    def test_prevention_and_detection_share_one_definition(self, shared):
        """The arming script and the watchdog must never disagree about a
        surface, so neither may keep a private copy of the definition.

        Asserted against each module's *own* view of `ci_check_runs` rather than
        by identity with this test's import: the suite reloads these modules, so
        two live copies of the shared module can coexist and an `is` comparison
        across them would fail for a reason that says nothing about the code.
        """
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        arming = importlib.import_module("arm_dependabot_auto_merge")
        watchdog = importlib.import_module("main_red_watchdog")

        # Neither consumer spells the conclusions out: only the shared module
        # holds the literals. Checked in the source, because an identity
        # comparison on the frozenset is defeated by `importlib.reload`
        # rebinding it in place, which is a property of the suite, not the code.
        tools = REPO_ROOT / "tools"
        shared_source = (tools / "ci_check_runs.py").read_text(encoding="utf-8")
        assert 'frozenset({"failure", "timed_out", "action_required"})' in shared_source
        for consumer in ("arm_dependabot_auto_merge.py", "main_red_watchdog.py"):
            source = (tools / consumer).read_text(encoding="utf-8")
            assert "ci_check_runs" in source, f"{consumer} must read the shared definition"
            assert "timed_out" not in source, f"{consumer} must not restate the conclusions"

        assert arming.BLOCKING_CONCLUSIONS == shared.BLOCKING_CONCLUSIONS
        assert watchdog.ci_check_runs.BLOCKING_CONCLUSIONS == shared.BLOCKING_CONCLUSIONS

        # And the same input is judged the same way through both entry points.
        assert arming.failed_check_names([_check("x", "failure")]) == ["x"]
        assert watchdog.classify([_check("x", "failure")]) == ("RED", ["x"])


# --------------------------------------------------------------------------
# classify()
# --------------------------------------------------------------------------


class TestClassify:
    def test_no_check_runs_is_skip_not_green(self, mod):
        """A head whose checks have not reported yet must not close an incident:
        'nothing has run' is not 'nothing is broken'."""
        assert mod.classify([]) == ("SKIP", [])
        assert mod.classify(None) == ("SKIP", [])

    def test_all_good_is_green(self, mod):
        assert mod.classify([_check("test", "success"), _check("e2e", "skipped", run_id=2)]) == (
            "GREEN",
            [],
        )

    @pytest.mark.parametrize("status", ["queued", "in_progress", "waiting", "pending"])
    def test_an_unsettled_head_is_skip_not_green(self, mod, status):
        """GREEN closes an open incident, so it must mean "proven clean", never
        "nothing has failed yet". A commit landing on a broken `main` presents a
        head whose checks are all unfinished; calling that GREEN would close a
        live incident and reopen it an hour later."""
        assert mod.classify([_check("test", None, status=status)]) == ("SKIP", [])

    def test_one_green_check_does_not_settle_a_head_with_others_running(self, mod):
        assert mod.classify(
            [_check("test", "success", run_id=1), _check("e2e", None, run_id=2, status="queued")]
        ) == ("SKIP", [])

    def test_a_failure_outranks_an_unsettled_head(self, mod):
        """A settled failure is actionable whatever else is still running."""
        verdict, failed = mod.classify(
            [
                _check("mcp-server", "failure", run_id=1),
                _check("e2e", None, run_id=2, status="in_progress"),
            ]
        )
        assert verdict == "RED"
        assert failed == ["mcp-server"]

    def test_a_failure_is_red_with_every_name(self, mod):
        verdict, failed = mod.classify(
            [
                _check("mcp-server", "failure", run_id=1),
                _check("og-worker", "failure", run_id=2),
                _check("test", "success", run_id=3),
            ]
        )
        assert verdict == "RED"
        assert failed == ["mcp-server", "og-worker"]

    def test_running_checks_alongside_a_failure_are_still_red(self, mod):
        verdict, failed = mod.classify(
            [_check("mcp-server", "failure"), _check("test", None, run_id=2, status="in_progress")]
        )
        assert verdict == "RED"
        assert failed == ["mcp-server"]

    def test_failing_details_maps_names_to_runs(self, mod):
        runs = [_check("og-worker", "failure", url="https://example.invalid/job/1")]
        assert mod.failing_details(runs, ["og-worker"]) == {
            "og-worker": "https://example.invalid/job/1"
        }

    def test_failing_details_omits_a_missing_url(self, mod):
        assert mod.failing_details([_check("og-worker", "failure")], ["og-worker"]) == {}


# --------------------------------------------------------------------------
# issue_body()
# --------------------------------------------------------------------------


class TestIssueBody:
    def test_body_names_surfaces_commit_and_owner(self, mod):
        body = mod.issue_body(
            branch="main",
            sha=HEAD,
            failed=["mcp-server", "og-worker"],
            details={"mcp-server": "https://example.invalid/job/1"},
            commit_subject="chore(deps-dev): bump vitest",
            pull_request=498,
        )
        assert body.startswith(mod.ISSUE_MARKER)
        assert "mcp-server" in body and "og-worker" in body
        assert HEAD[:12] in body
        assert "#498" in body, "the PR is the route to an accountable owner"
        assert "https://example.invalid/job/1" in body

    def test_body_is_a_pure_function_of_head_state(self, mod):
        """Nothing per-run may enter the body: it is rewritten on every census
        while the red lasts, so a per-run value would edit the issue hourly for
        no new information. `issue_body` takes no run identity at all, which is
        what makes that structural rather than a convention."""
        import inspect

        params = set(inspect.signature(mod.issue_body).parameters)
        assert "run_url" not in params and "run_id" not in params
        kwargs = dict(branch="main", sha=HEAD, failed=["og-worker"])
        assert mod.issue_body(**kwargs) == mod.issue_body(**kwargs)

    def test_body_tolerates_a_missing_pr_and_subject(self, mod):
        body = mod.issue_body(branch="main", sha=HEAD, failed=["og-worker"])
        assert "Merged from" not in body
        assert "og-worker" in body

    def test_body_states_it_only_reports(self, mod):
        body = mod.issue_body(branch="main", sha=HEAD, failed=["og-worker"])
        assert "does not revert" in body


# --------------------------------------------------------------------------
# main() with gh stubbed
# --------------------------------------------------------------------------


class _Gh:
    """Answers the exact gh argument shapes the module issues."""

    def __init__(
        self, *, check_runs=(), open_issues=(), sha=HEAD, subject="a commit", pulls=(),
        issue_bodies=None,
    ):
        self.check_runs = list(check_runs)
        self.open_issues = list(open_issues)  # [(number, title)]
        self.sha = sha
        self.subject = subject
        self.pulls = list(pulls)
        self.issue_bodies = dict(issue_bodies or {})
        self.calls: list[list[str]] = []
        self.created = 777

    def __call__(self, args, *, check=True):
        self.calls.append(list(args))
        if args[:2] == ["api", "--paginate"] and "/check-runs" in args[2]:
            return "\n".join(json.dumps(c) for c in self.check_runs)
        if args == ["api", f"repos/{REPO}/commits/main"]:
            return json.dumps({"sha": self.sha, "commit": {"message": self.subject}})
        if args == ["api", f"repos/{REPO}/commits/{self.sha}/pulls"]:
            return json.dumps([{"number": n} for n in self.pulls])
        if args[:2] == ["api", "--paginate"] and "/issues?state=open" in args[2]:
            return "\n".join(json.dumps([n, t]) for n, t in self.open_issues)
        for number in self.issue_bodies:
            if args == ["api", f"repos/{REPO}/issues/{number}"]:
                return json.dumps({"number": number, "body": self.issue_bodies[number]})
        if len(args) == 2 and args[0] == "api" and args[1].startswith(f"repos/{REPO}/issues/"):
            return json.dumps({"body": ""})
        if args[:3] == ["api", "-X", "PATCH"]:
            return "{}"
        if args[:2] == ["api", f"repos/{REPO}/issues"] and "POST" in args:
            return json.dumps({"number": self.created})
        if args[:3] == ["api", "-X", "POST"]:
            return "{}"
        raise AssertionError(f"unexpected gh call: {args}")

    def patched(self, needle):
        return [c for c in self.calls if c[:3] == ["api", "-X", "PATCH"] and needle in c[3]]


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    monkeypatch.setenv("GITHUB_RUN_ID", "9")
    monkeypatch.setenv("GITHUB_SERVER_URL", "https://example.invalid")
    monkeypatch.delenv("MAIN_BRANCH", raising=False)
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    return summary


def test_red_head_opens_one_issue(mod, env, monkeypatch, capsys):
    gh = _Gh(check_runs=[_check("mcp-server", "failure"), _check("test", "success", run_id=2)],
             pulls=[498])
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 0, "a red main must not fail the watchdog's own run"
    out = capsys.readouterr().out
    assert f"{mod.RESULT_PREFIX} RED" in out
    assert "mcp-server" in out
    creates = [c for c in gh.calls if c[:2] == ["api", f"repos/{REPO}/issues"] and "POST" in c]
    assert len(creates) == 1
    assert any(f"title={mod.ISSUE_TITLE}" == a for a in creates[0])
    assert "RED" in env.read_text(encoding="utf-8")


def test_red_head_refreshes_the_existing_issue_instead_of_opening_a_second(
    mod, env, monkeypatch, capsys
):
    gh = _Gh(
        check_runs=[_check("og-worker", "failure")],
        open_issues=[(500, mod.ISSUE_TITLE)],
    )
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 0
    assert "refreshed #500" in capsys.readouterr().out
    assert not [c for c in gh.calls if c[:2] == ["api", f"repos/{REPO}/issues"] and "POST" in c]
    assert gh.patched(f"repos/{REPO}/issues/500")


def test_an_unchanged_red_writes_nothing(mod, env, monkeypatch, capsys):
    """Hourly censuses during a multi-day outage must not edit the issue once an
    hour. The body is a function of the head, so an unchanged body means an
    unchanged red and there is nothing to write."""
    checks = [_check("og-worker", "failure")]
    expected = mod.issue_body(
        branch="main",
        sha=HEAD,
        failed=["og-worker"],
        details=mod.failing_details(checks, ["og-worker"]),
        commit_subject="a commit",
        pull_request=None,
    )
    gh = _Gh(
        check_runs=checks,
        open_issues=[(500, mod.ISSUE_TITLE)],
        issue_bodies={500: expected},
    )
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 0
    out = capsys.readouterr().out
    assert f"{mod.RESULT_PREFIX} RED" in out, "it is still red, and must still say so"
    assert "unchanged #500" in out
    assert not [c for c in gh.calls if c[:3] == ["api", "-X", "PATCH"]], "no edit for no change"


def test_a_changed_red_does_refresh(mod, env, monkeypatch, capsys):
    """The other half: a red that moved to a different surface must update."""
    gh = _Gh(
        check_runs=[_check("mcp-server", "failure")],
        open_issues=[(500, mod.ISSUE_TITLE)],
        issue_bodies={500: "an older body naming og-worker"},
    )
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 0
    assert "refreshed #500" in capsys.readouterr().out
    assert gh.patched(f"repos/{REPO}/issues/500")


def test_an_unrelated_open_issue_is_not_mistaken_for_the_incident(mod, env, monkeypatch, capsys):
    gh = _Gh(
        check_runs=[_check("og-worker", "failure")],
        open_issues=[(423, "W5a — archive eligibility"), (489, "A failing surface check")],
    )
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 0
    creates = [c for c in gh.calls if c[:2] == ["api", f"repos/{REPO}/issues"] and "POST" in c]
    assert len(creates) == 1, "exact-title dedupe must not match a different issue"


def test_green_head_closes_the_open_incident(mod, env, monkeypatch, capsys):
    """#473: dedupe bounds the rate, only a closer bounds the population."""
    gh = _Gh(
        check_runs=[_check("mcp-server", "success"), _check("og-worker", "skipped", run_id=2)],
        open_issues=[(500, mod.ISSUE_TITLE)],
    )
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 0
    out = capsys.readouterr().out
    assert f"{mod.RESULT_PREFIX} GREEN" in out
    assert "closed #500" in out
    closed = [c for c in gh.patched(f"repos/{REPO}/issues/500") if "state=closed" in c]
    assert closed, "the incident must actually be closed, not just commented on"


def test_green_head_with_no_incident_is_a_quiet_no_op(mod, env, monkeypatch, capsys):
    gh = _Gh(check_runs=[_check("test", "success")])
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 0
    assert f"{mod.RESULT_PREFIX} GREEN" in capsys.readouterr().out
    assert not [c for c in gh.calls if c[:3] == ["api", "-X", "PATCH"]]
    assert not [c for c in gh.calls if c[:3] == ["api", "-X", "POST"]]


def test_a_head_with_no_checks_yet_changes_nothing(mod, env, monkeypatch, capsys):
    """Mid-CI must neither alarm nor close an open incident."""
    gh = _Gh(check_runs=[], open_issues=[(500, mod.ISSUE_TITLE)])
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 0
    assert f"{mod.RESULT_PREFIX} SKIP" in capsys.readouterr().out
    assert not [c for c in gh.calls if c[:3] == ["api", "-X", "PATCH"]]


def test_an_unsettled_head_does_not_close_a_live_incident(mod, env, monkeypatch, capsys):
    """The regression this exists for: a commit landing on a broken `main`
    presents an unsettled head, and the incident must survive it."""
    gh = _Gh(
        check_runs=[_check("test", None, status="queued"), _check("e2e", None, run_id=2, status="in_progress")],
        open_issues=[(500, mod.ISSUE_TITLE)],
    )
    monkeypatch.setattr(mod, "_run_gh", gh)
    assert mod.main() == 0
    out = capsys.readouterr().out
    assert f"{mod.RESULT_PREFIX} SKIP" in out
    assert "still running" in out and "e2e" in out, "the reason must name what is pending"
    assert not [c for c in gh.patched(f"repos/{REPO}/issues/500")], "the incident must stay open"


def test_a_gh_failure_is_a_typed_error(mod, env, monkeypatch, capsys):
    def failing(args, *, check=True):
        raise mod.GhError("HTTP 401: Bad credentials")

    monkeypatch.setattr(mod, "_run_gh", failing)
    assert mod.main() == 1
    out = capsys.readouterr().out
    assert f"{mod.RESULT_PREFIX} ERROR" in out
    assert "Bad credentials" in out


def test_without_repository_is_a_typed_error(mod, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    assert mod.main() == 1
    assert f"{mod.RESULT_PREFIX} ERROR" in capsys.readouterr().out
