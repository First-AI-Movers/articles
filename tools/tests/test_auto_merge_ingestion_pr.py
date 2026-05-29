#!/usr/bin/env python3
"""Tests for tools/auto_merge_ingestion_pr.py (E41f).

Covers:
  - is_path_allowed / first_disallowed_path against the documented allowlist
  - title_matches / branch_matches
  - required_checks_status state machine
  - main() flow under the various skip / block / merge paths
"""

import importlib
import sys

import pytest


@pytest.fixture
def mod():
    # Import lazily so test discovery works even if the file is added later.
    sys.path.insert(0, "tools")
    m = importlib.import_module("auto_merge_ingestion_pr")
    yield m
    importlib.reload(m)


class TestPathAllowlist:
    @pytest.mark.parametrize(
        "path",
        [
            "articles/2026-05-04-x/article.md",
            "articles/2026-05-04-x/metadata.json",
            "articles/2026-05-04-some-long-slug-2026/article.md",
            "README.md",
            "ROADMAP.md",
            "index.json",
            "sitemap.xml",
            "feed.xml",
            "feed.json",
            "llms.txt",
            "llms-full.txt",
            "llms-recent.txt",
        ],
    )
    def test_allowed(self, mod, path):
        assert mod.is_path_allowed(path) is True

    @pytest.mark.parametrize(
        "path",
        [
            # Article folders may not have nested subdirs.
            "articles/2026-05-04-x/sub/article.md",
            "articles/2026-05-04-x/sub/metadata.json",
            # Article files must be exactly the two canonical files.
            "articles/2026-05-04-x/notes.md",
            "articles/2026-05-04-x/article.md.bak",
            "articles/2026-05-04-x/.metadata.json",
            "articles/2026-05-04-x/extra.json",
            "articles/2026-05-04-x/article.md/",
            # Top-level files with the wrong path or case.
            "Readme.md",
            "ROADMAP.md.bak",
            "tools/ingest_airtable.py",
            "docs/airtable-ingestion.md",
            ".github/workflows/ingest-airtable.yml",
            # Empty / weird inputs.
            "",
            "/",
            "articles//article.md",
            "articles/x\x00x/article.md",
            # Generated artifacts inside subdirs are not allowed.
            "tests/index.json",
            "subdir/sitemap.xml",
        ],
    )
    def test_disallowed(self, mod, path):
        assert mod.is_path_allowed(path) is False

    def test_first_disallowed_path_returns_first_violation(self, mod):
        paths = [
            "articles/2026-05-04-x/article.md",
            "tools/ingest_airtable.py",  # ← violator
            "README.md",
            "docs/something.md",
        ]
        assert mod.first_disallowed_path(paths) == "tools/ingest_airtable.py"

    def test_first_disallowed_path_returns_none_when_clean(self, mod):
        paths = [
            "articles/2026-05-04-x/article.md",
            "articles/2026-05-04-x/metadata.json",
            "README.md",
            "ROADMAP.md",
        ]
        assert mod.first_disallowed_path(paths) is None


class TestTitleAndBranch:
    def test_title_must_match_exactly(self, mod):
        assert mod.title_matches("ingest(articles): add articles from Airtable") is True
        assert mod.title_matches("ingest(articles): Add articles from Airtable") is False
        assert mod.title_matches("ingest(article): add articles from Airtable") is False
        assert mod.title_matches("") is False

    def test_branch_prefix_required(self, mod):
        # The cron workflow's exact branch must match.
        assert mod.branch_matches("ingest/airtable-articles") is True

        # E20b dispatch branches (ingest/airtable-record-recXXX) must NOT
        # match — they require human review per record, even though the
        # title-match would also reject them. Defense in depth.
        assert mod.branch_matches("ingest/airtable-record-rec123") is False

        # External (Flow B) and unrelated refs must not match.
        assert mod.branch_matches("ingest/article-fixture") is False
        assert mod.branch_matches("main") is False
        assert mod.branch_matches("") is False


class TestRequiredChecksStatus:
    def _rollup(self, **named):
        """Build a rollup like gh's JSON output. {name: conclusion or None}."""
        return [{"name": k, "conclusion": v} for k, v in named.items()]

    def test_all_success(self, mod):
        rollup = self._rollup(
            check="SUCCESS", e2e="SUCCESS", **{"geo-audit": "SUCCESS"},
            gitleaks="SUCCESS", lychee="SUCCESS", readability="SUCCESS",
            test="SUCCESS", vale="SUCCESS",
        )
        state, _ = mod.required_checks_status(rollup)
        assert state == "complete-success"

    def test_one_failure(self, mod):
        rollup = self._rollup(
            check="SUCCESS", e2e="FAILURE", **{"geo-audit": "SUCCESS"},
            gitleaks="SUCCESS", lychee="SUCCESS", readability="SUCCESS",
            test="SUCCESS", vale="SUCCESS",
        )
        state, detail = mod.required_checks_status(rollup)
        assert state == "complete-failure"
        assert "e2e=FAILURE" in detail

    def test_pending_check(self, mod):
        rollup = self._rollup(
            check="SUCCESS", e2e=None, **{"geo-audit": "SUCCESS"},
            gitleaks="SUCCESS", lychee="SUCCESS", readability="SUCCESS",
            test="SUCCESS", vale="SUCCESS",
        )
        state, detail = mod.required_checks_status(rollup)
        assert state == "pending"
        assert "e2e" in detail

    def test_missing_required_check(self, mod):
        # No `vale` reported at all.
        rollup = [
            {"name": n, "conclusion": "SUCCESS"}
            for n in ("check", "e2e", "geo-audit", "gitleaks", "lychee", "readability", "test")
        ]
        state, detail = mod.required_checks_status(rollup)
        assert state == "missing"
        assert "vale" in detail

    def test_extra_unknown_checks_ignored(self, mod):
        """Optional/extra checks must not block when all required are green."""
        rollup = self._rollup(
            check="SUCCESS", e2e="SUCCESS", **{"geo-audit": "SUCCESS"},
            gitleaks="SUCCESS", lychee="SUCCESS", readability="SUCCESS",
            test="SUCCESS", vale="SUCCESS",
            wayback="FAILURE",  # ignored — not in REQUIRED_CHECKS
        )
        state, _ = mod.required_checks_status(rollup)
        assert state == "complete-success"


class TestMainSkipPaths:
    def test_kill_switch_off_silent_skip(self, mod, monkeypatch, capsys):
        monkeypatch.delenv("AUTO_MERGE_INGESTION_PRS", raising=False)
        rc = mod.main()
        assert rc == 0
        assert "[skip]" in capsys.readouterr().out

    def test_kill_switch_value_zero_silent_skip(self, mod, monkeypatch, capsys):
        monkeypatch.setenv("AUTO_MERGE_INGESTION_PRS", "0")
        rc = mod.main()
        assert rc == 0
        assert "[skip]" in capsys.readouterr().out

    def test_no_open_pr_silent_skip(self, mod, monkeypatch, capsys):
        monkeypatch.setenv("AUTO_MERGE_INGESTION_PRS", "1")
        monkeypatch.setattr(mod, "find_open_pr", lambda *a, **kw: None)
        rc = mod.main()
        assert rc == 0
        out = capsys.readouterr().out
        assert "[skip]" in out
        assert "no open PR" in out


class TestMainBlockPaths:
    def _pr(self, **overrides):
        base = {
            "number": 999,
            "url": "https://github.com/o/r/pull/999",
            "title": "ingest(articles): add articles from Airtable",
            "headRefName": "ingest/airtable-articles",
            "baseRefName": "main",
            "mergeable": "MERGEABLE",
            "mergeStateStatus": "CLEAN",
            "files": [
                {"path": "articles/2026-05-04-x/article.md"},
                {"path": "articles/2026-05-04-x/metadata.json"},
                {"path": "README.md"},
            ],
            "statusCheckRollup": [
                {"name": n, "conclusion": "SUCCESS"}
                for n in (
                    "check", "e2e", "geo-audit", "gitleaks",
                    "lychee", "readability", "test", "vale",
                )
            ],
        }
        base.update(overrides)
        return base

    def test_branch_mismatch_blocks(self, mod, monkeypatch, capsys):
        monkeypatch.setenv("AUTO_MERGE_INGESTION_PRS", "1")
        pr = self._pr(headRefName="feature/something-else")
        monkeypatch.setattr(mod, "find_open_pr", lambda *a, **kw: pr)
        issued = {}
        monkeypatch.setattr(
            mod, "open_incident_issue",
            lambda reason, pr=None, repo=None: issued.setdefault("r", reason),
        )
        rc = mod.main()
        assert rc == 1
        assert "head branch" in issued["r"]
        assert "[block]" in capsys.readouterr().out

    def test_title_mismatch_blocks(self, mod, monkeypatch, capsys):
        monkeypatch.setenv("AUTO_MERGE_INGESTION_PRS", "1")
        pr = self._pr(title="something else entirely")
        monkeypatch.setattr(mod, "find_open_pr", lambda *a, **kw: pr)
        issued = {}
        monkeypatch.setattr(
            mod, "open_incident_issue",
            lambda reason, pr=None, repo=None: issued.setdefault("r", reason),
        )
        rc = mod.main()
        assert rc == 1
        assert "title" in issued["r"]

    def test_disallowed_file_blocks(self, mod, monkeypatch):
        monkeypatch.setenv("AUTO_MERGE_INGESTION_PRS", "1")
        pr = self._pr(files=[
            {"path": "articles/2026-05-04-x/article.md"},
            {"path": "tools/ingest_airtable.py"},  # violator
        ])
        monkeypatch.setattr(mod, "find_open_pr", lambda *a, **kw: pr)
        issued = {}
        monkeypatch.setattr(
            mod, "open_incident_issue",
            lambda reason, pr=None, repo=None: issued.setdefault("r", reason),
        )
        rc = mod.main()
        assert rc == 1
        assert "tools/ingest_airtable.py" in issued["r"]
        assert "allowlist" in issued["r"]

    def test_failed_check_blocks_files_issue_but_does_not_fail_cron(self, mod, monkeypatch):
        """A real CI failure on the freshly-created ingest PR must surface
        as an `E41 auto-merge blocked` issue (so an operator can act on
        it), but must NOT also fail the cron run — otherwise the
        failure-path step in the workflow files a duplicate
        `E41 cron ingestion incident:` issue for the same event. The
        single point of truth is the auto-merge-blocked issue.
        """
        monkeypatch.setenv("AUTO_MERGE_INGESTION_PRS", "1")
        rollup = [
            {"name": n, "conclusion": "SUCCESS"}
            for n in ("check", "geo-audit", "gitleaks", "lychee", "readability", "test", "vale")
        ]
        rollup.append({"name": "e2e", "conclusion": "FAILURE"})
        pr = self._pr(statusCheckRollup=rollup)
        monkeypatch.setattr(mod, "find_open_pr", lambda *a, **kw: pr)
        issued = {}
        monkeypatch.setattr(
            mod, "open_incident_issue",
            lambda reason, pr=None, repo=None: issued.setdefault("r", reason),
        )
        rc = mod.main()
        assert rc == 0, (
            "complete-failure must exit 0 so the cron's success-path "
            "incident-cleanup step can sweep stale incidents from prior "
            "failed runs without double-filing for this event."
        )
        assert "CI failed" in issued["r"]
        assert "e2e=FAILURE" in issued["r"]


class TestMainHappyPath:
    def test_clean_pr_is_squash_merged(self, mod, monkeypatch, capsys):
        monkeypatch.setenv("AUTO_MERGE_INGESTION_PRS", "1")
        pr = {
            "number": 165,
            "url": "https://github.com/o/r/pull/165",
            "title": "ingest(articles): add articles from Airtable",
            "headRefName": "ingest/airtable-articles",
            "baseRefName": "main",
            "mergeable": "MERGEABLE",
            "mergeStateStatus": "CLEAN",
            "files": [
                {"path": "articles/2026-05-04-x/article.md"},
                {"path": "articles/2026-05-04-x/metadata.json"},
                {"path": "README.md"},
                {"path": "ROADMAP.md"},
                {"path": "index.json"},
                {"path": "sitemap.xml"},
                {"path": "feed.xml"},
                {"path": "feed.json"},
                {"path": "llms.txt"},
                {"path": "llms-full.txt"},
                {"path": "llms-recent.txt"},
            ],
            "statusCheckRollup": [
                {"name": n, "conclusion": "SUCCESS"}
                for n in ("check", "e2e", "geo-audit", "gitleaks",
                         "lychee", "readability", "test", "vale")
            ],
        }
        monkeypatch.setattr(mod, "find_open_pr", lambda *a, **kw: pr)
        merged = {}
        monkeypatch.setattr(mod, "squash_merge",
                            lambda n, repo=None: merged.setdefault("n", n))
        rc = mod.main()
        assert rc == 0
        assert merged["n"] == 165
        out = capsys.readouterr().out
        assert "[merge]" in out
        assert "[done]" in out

    def test_pending_then_success_polls_until_green(self, mod, monkeypatch):
        monkeypatch.setenv("AUTO_MERGE_INGESTION_PRS", "1")
        monkeypatch.setenv("AUTO_MERGE_TIMEOUT_SECONDS", "5")
        monkeypatch.setenv("AUTO_MERGE_POLL_INTERVAL", "0")  # don't actually wait

        pr_pending = {
            "number": 200,
            "url": "https://github.com/o/r/pull/200",
            "title": "ingest(articles): add articles from Airtable",
            "headRefName": "ingest/airtable-articles",
            "baseRefName": "main",
            "mergeable": "MERGEABLE",
            "mergeStateStatus": "BLOCKED",
            "files": [{"path": "README.md"}],
            "statusCheckRollup": [
                {"name": "check", "conclusion": "SUCCESS"},
                {"name": "e2e", "conclusion": None},  # pending
                {"name": "geo-audit", "conclusion": "SUCCESS"},
                {"name": "gitleaks", "conclusion": "SUCCESS"},
                {"name": "lychee", "conclusion": "SUCCESS"},
                {"name": "readability", "conclusion": "SUCCESS"},
                {"name": "test", "conclusion": "SUCCESS"},
                {"name": "vale", "conclusion": "SUCCESS"},
            ],
        }
        pr_done = dict(pr_pending)
        pr_done["mergeStateStatus"] = "CLEAN"
        pr_done["statusCheckRollup"] = [
            {"name": n, "conclusion": "SUCCESS"}
            for n in ("check", "e2e", "geo-audit", "gitleaks",
                     "lychee", "readability", "test", "vale")
        ]

        responses = iter([pr_pending, pr_done])
        monkeypatch.setattr(mod, "find_open_pr",
                            lambda *a, **kw: next(responses))
        merged = {}
        monkeypatch.setattr(mod, "squash_merge",
                            lambda n, repo=None: merged.setdefault("n", n))
        # Avoid real sleep.
        monkeypatch.setattr(mod.time, "sleep", lambda _s: None)
        rc = mod.main()
        assert rc == 0
        assert merged["n"] == 200

    def test_timeout_blocks_with_incident(self, mod, monkeypatch):
        monkeypatch.setenv("AUTO_MERGE_INGESTION_PRS", "1")
        monkeypatch.setenv("AUTO_MERGE_TIMEOUT_SECONDS", "0")  # immediate timeout
        monkeypatch.setenv("AUTO_MERGE_POLL_INTERVAL", "0")

        pr_pending = {
            "number": 300,
            "url": "https://github.com/o/r/pull/300",
            "title": "ingest(articles): add articles from Airtable",
            "headRefName": "ingest/airtable-articles",
            "mergeable": "MERGEABLE",
            "mergeStateStatus": "BLOCKED",
            "files": [{"path": "README.md"}],
            "statusCheckRollup": [
                {"name": "check", "conclusion": None},
                {"name": "e2e", "conclusion": None},
                {"name": "geo-audit", "conclusion": None},
                {"name": "gitleaks", "conclusion": None},
                {"name": "lychee", "conclusion": None},
                {"name": "readability", "conclusion": None},
                {"name": "test", "conclusion": None},
                {"name": "vale", "conclusion": None},
            ],
        }
        monkeypatch.setattr(mod, "find_open_pr", lambda *a, **kw: pr_pending)
        issued = {}
        monkeypatch.setattr(
            mod, "open_incident_issue",
            lambda reason, pr=None, repo=None: issued.setdefault("r", reason),
        )
        rc = mod.main()
        assert rc == 0, (
            "Polling timeout (required checks not finished yet) must exit 0 "
            "so the cron does not fail merely because a freshly opened PR's "
            "checks have not completed within the auto-merge poll window. "
            "The `E41 auto-merge blocked` issue captures the operator-review "
            "signal; the cron itself stays in success()."
        )
        assert "timed out" in issued["r"]
