#!/usr/bin/env python3
"""Tests for tools/arm_dependabot_auto_merge.py (#432).

Covers:
  - is_path_allowed / first_disallowed_path, and their alignment with the
    directories `.github/dependabot.yml` actually configures
  - classify(): the SKIP / REFUSED / ARM decision table
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
        for entry in cfg["updates"]:
            eco = entry["package-ecosystem"]
            dirs = entry.get("directories") or [entry["directory"]]
            assert eco in manifests, f"unknown ecosystem {eco!r} in dependabot.yml"
            for d in dirs:
                prefix = d.strip("/")
                prefix = f"{prefix}/" if prefix else ""
                for m in manifests[eco]:
                    expected.add(f"{prefix}{m}")
                if eco == "github-actions":
                    assert d == "/", "github-actions entries are rooted at '/'"
                    assert mod.is_path_allowed(".github/workflows/x.yml")
        assert set(mod.ALLOWED_PATHS) == expected, (
            f"ALLOWED_PATHS must equal the manifests of every pip/npm directory in "
            f".github/dependabot.yml; expected {sorted(expected)}, got {sorted(mod.ALLOWED_PATHS)}"
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
# main() with gh stubbed
# --------------------------------------------------------------------------


class _Gh:
    """Records every gh invocation and answers from a scripted PR state.

    Matches the exact argument shapes the module issues, so a change in how the
    module calls gh fails here instead of being silently answered.
    """

    def __init__(self, pr, files, *, merged_after=False, armed_after=True, comments=""):
        self.pr = pr
        self.files = files
        self.merged_after = merged_after
        self.armed_after = armed_after
        self.comments = comments
        self.calls: list[list[str]] = []

    def __call__(self, args, *, check=True):
        self.calls.append(list(args))
        repo = "First-AI-Movers/articles"
        n = self.pr["number"]
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


def test_main_without_repository_is_a_typed_refusal(mod, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    assert mod.main() == 1
    assert f"{mod.RESULT_PREFIX} REFUSED" in capsys.readouterr().out
