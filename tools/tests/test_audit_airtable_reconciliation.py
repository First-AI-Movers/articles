#!/usr/bin/env python3
"""Tests for tools/audit_airtable_reconciliation.py (read-only reconciliation).

Covers the pure logic — build_archive_index and reconcile — with fixtures; no
network is touched. The tool reuses ingest_airtable's field map / validation /
status gate, so these tests exercise that shared contract via reconcile().
"""

import importlib
import json
import sys

import pytest

# The module imports ingest_airtable, which imports requests.
pytest.importorskip("requests")


@pytest.fixture
def mod():
    sys.path.insert(0, "tools")
    m = importlib.import_module("audit_airtable_reconciliation")
    yield m
    importlib.reload(m)


@pytest.fixture
def schema(mod):
    return mod.ing._load_schema()


def _rec(rid, *, title="A Title", url, status="Posted", date="2026-05-01"):
    """A REST-shaped Airtable record whose payload passes schema validation
    (slug is derived from the GUID's last path segment)."""
    return {
        "id": rid,
        "fields": {
            "Title": title,
            "GUID": url,
            "FAIM Status": status,
            "Pub Date": date,
            "Content HTML": "body text",
        },
    }


class TestBuildArchiveIndex:
    def _write_meta(self, root, folder, *, rid, url):
        d = root / folder
        d.mkdir(parents=True)
        (d / "metadata.json").write_text(
            json.dumps({"id": rid, "canonical_url": url}), encoding="utf-8"
        )

    def test_collects_ids_and_normalized_urls(self, mod, tmp_path):
        self._write_meta(tmp_path, "2026-01-01-a", rid="rec1", url="https://X.com/A/")
        self._write_meta(tmp_path, "2026-01-02-b", rid="rec2", url="https://y.com/b")
        idx = mod.build_archive_index(tmp_path)
        assert idx["ids"] == {"rec1", "rec2"}
        # URL normalization lowercases scheme/host and strips trailing slash.
        assert "https://x.com/A" in idx["urls"]
        assert "https://y.com/b" in idx["urls"]

    def test_missing_dir_is_empty(self, mod, tmp_path):
        idx = mod.build_archive_index(tmp_path / "does-not-exist")
        assert idx == {"ids": set(), "urls": set(), "titles": set()}

    def test_malformed_metadata_skipped(self, mod, tmp_path):
        good = tmp_path / "2026-01-01-a"
        good.mkdir()
        (good / "metadata.json").write_text('{"id":"rec1","canonical_url":"https://x.com/a"}')
        bad = tmp_path / "2026-01-02-b"
        bad.mkdir()
        (bad / "metadata.json").write_text("{not json")
        idx = mod.build_archive_index(tmp_path)
        assert idx["ids"] == {"rec1"}


class TestReconcile:
    def test_present_by_record_id(self, mod, schema):
        recs = [_rec("rec1", url="https://x.com/a")]
        archive = {"ids": {"rec1"}, "urls": set()}
        counts, missing = mod.reconcile(recs, archive, schema)
        assert counts["eligible"] == 1
        assert counts["eligible_present"] == 1
        assert counts["eligible_missing"] == 0
        assert missing == []

    def test_present_by_canonical_url_when_id_differs(self, mod, schema):
        """A re-created record (new id, same URL) must NOT count as missing."""
        recs = [_rec("recNEW", url="https://x.com/a")]
        archive = {"ids": {"recOLD"}, "urls": {"https://x.com/a"}}
        counts, missing = mod.reconcile(recs, archive, schema)
        assert counts["eligible_present"] == 1
        assert counts["eligible_missing"] == 0

    def test_missing_when_neither_id_nor_url_matches(self, mod, schema):
        recs = [_rec("rec2", url="https://x.com/b")]
        archive = {"ids": {"rec1"}, "urls": {"https://x.com/a"}}
        counts, missing = mod.reconcile(recs, archive, schema)
        assert counts["eligible_missing"] == 1
        assert missing == ["rec2"]

    def test_present_by_title_when_id_and_url_drifted(self, mod, schema):
        """Re-created record: new id AND drifted canonical URL, but the title is
        already published -> present, NOT missing (identity-drift false-missing)."""
        recs = [_rec("recNEW", title="Drifted Title", url="https://x.com/new-slug")]
        archive = {"ids": {"recOLD"}, "urls": {"https://x.com/old-slug"},
                   "titles": {mod.ing._normalize_title("Drifted Title")}}
        counts, missing = mod.reconcile(recs, archive, schema)
        assert counts["eligible_present"] == 1
        assert counts["eligible_missing"] == 0
        assert counts["present_by_title_drift"] == 1  # reclassified by title, surfaced
        assert missing == []

    def test_non_posted_status_skipped(self, mod, schema):
        recs = [_rec("rec3", url="https://x.com/c", status="Draft")]
        counts, _ = mod.reconcile(recs, {"ids": set(), "urls": set()}, schema)
        assert counts["status_skipped"] == 1
        assert counts["eligible"] == 0

    def test_invalid_record_counted_invalid(self, mod, schema):
        recs = [{"id": "rec4", "fields": {"FAIM Status": "Posted"}}]  # missing required fields
        counts, _ = mod.reconcile(recs, {"ids": set(), "urls": set()}, schema)
        assert counts["invalid"] == 1
        assert counts["eligible"] == 0

    def test_allow_no_status_gate_counts_blank_status_eligible(self, mod, schema):
        recs = [_rec("rec5", url="https://x.com/e", status="")]
        no_gate, _ = mod.reconcile(recs, {"ids": set(), "urls": set()}, schema,
                                   allow_no_status_gate=True)
        assert no_gate["eligible"] == 1
        with_gate, _ = mod.reconcile(recs, {"ids": set(), "urls": set()}, schema,
                                     allow_no_status_gate=False)
        assert with_gate["status_skipped"] == 1

    def test_full_tally_is_consistent(self, mod, schema):
        recs = [
            _rec("rec1", url="https://x.com/a"),                 # present
            _rec("rec2", url="https://x.com/b"),                 # missing
            _rec("rec3", url="https://x.com/c", status="Draft"),  # status-skipped
            {"id": "rec4", "fields": {"FAIM Status": "Posted"}},  # invalid
        ]
        archive = {"ids": {"rec1"}, "urls": set()}
        counts, missing = mod.reconcile(recs, archive, schema)
        assert counts == {
            "fetched": 4, "invalid": 1, "status_skipped": 1,
            "eligible": 2, "eligible_present": 1, "eligible_missing": 1,
            "present_by_title_drift": 0,
        }
        assert missing == ["rec2"]
        # No Airtable writes / backfill: reconcile returns data only.


class TestWorkflowIsReadOnly:
    """Pin the read-only invariant of the reconciliation workflow so a future
    edit cannot silently grant it write access or a PR/backfill path."""

    def _wf(self):
        yaml = pytest.importorskip("yaml")
        from pathlib import Path
        p = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "audit-airtable-reconciliation.yml"
        return yaml.safe_load(p.read_text(encoding="utf-8")), (p.read_text(encoding="utf-8"))

    def test_permissions_are_read_only_plus_issues(self):
        wf, _ = self._wf()
        perms = wf.get("permissions") or {}
        assert perms.get("contents") == "read", (
            f"reconciliation workflow must keep contents: read (never write); got {perms!r}"
        )
        assert "write" != perms.get("pull-requests"), (
            "reconciliation workflow must not grant pull-requests: write"
        )

    def test_no_pr_creation_or_backfill(self):
        _, text = self._wf()
        assert "create-pull-request" not in text, (
            "reconciliation workflow must never open a PR"
        )
        assert "--write" not in text and "--backfill" not in text, (
            "reconciliation workflow must never invoke a write/backfill path"
        )


class _StubVerifier:
    """Receipt-gate stub: admits by canonical URL; `drift` marks canonical_match False."""

    def __init__(self, admit, *, drift=(), klass="no_receipt"):
        self.admit, self.drift, self.klass = set(admit), set(drift), klass
        self.calls = []

    def decide(self, fields, *, canonical_url, slug, license_value=""):
        self.calls.append(("decide", canonical_url))
        class D:  # noqa: D401 - minimal decision shape
            pass
        d = D()
        if canonical_url in self.admit:
            d.eligible, d.klass, d.reason = True, "eligible", "stub"
            d.receipt = {"kind": "HASHNODE_POST", "canonical_match": canonical_url not in self.drift}
        else:
            d.eligible, d.klass, d.reason, d.receipt = False, self.klass, "stub", None
        return d


class TestReceiptGateReconcile:
    def test_receipt_gate_reclassifies_and_counts_drift(self, mod, schema):
        """Under the receipt gate a Draft row with a receipt is eligible, a Posted row
        without one is `no_receipt`, and canonical drift is counted but still eligible."""
        archive = {"ids": set(), "urls": set(), "titles": set()}
        recs = [
            _rec("rec1", url="https://www.firstaimovers.com/p/live", status="Draft"),
            _rec("rec2", url="https://www.firstaimovers.com/p/drifted", status="Ready"),
            _rec("rec3", url="https://www.firstaimovers.com/p/label-only", status="Posted"),
        ]
        v = _StubVerifier(admit={"https://www.firstaimovers.com/p/live",
                                 "https://www.firstaimovers.com/p/drifted"},
                          drift={"https://www.firstaimovers.com/p/drifted"})
        counts, missing = mod.reconcile(recs, archive, schema, gate="receipt", verifier=v)
        assert counts["gate"] == "receipt"
        assert counts["eligible"] == 2 and counts["eligible_missing"] == 2
        assert counts["no_receipt"] == 1 and counts["status_skipped"] == 0
        assert counts["canonical_drift"] == 1
        assert set(missing) == {"rec1", "rec2"}

    def test_status_gate_counts_shape_is_unchanged(self, mod, schema, monkeypatch):
        monkeypatch.delenv(mod.ing.ELIGIBILITY_GATE_ENV, raising=False)
        archive = {"ids": set(), "urls": set(), "titles": set()}
        counts, _ = mod.reconcile([_rec("rec1", url="https://x/p/a", status="Draft")], archive, schema)
        assert "gate" not in counts and "no_receipt" not in counts
        assert counts["status_skipped"] == 1

    def test_summary_names_the_gate(self, mod):
        base = {"fetched": 0, "eligible": 0, "eligible_present": 0, "eligible_missing": 0,
                "status_skipped": 0, "invalid": 0}
        assert "- Gate: status" in mod._render_summary(dict(base), since_hours=None)
        rec = dict(base, gate="receipt", no_receipt=3, canonical_drift=1)
        out = mod._render_summary(rec, since_hours=None)
        assert "Gate: receipt" in out and "no receipt 3" in out and "canonical drift 1" in out

    def test_summary_eligible_label_is_gate_neutral(self, mod):
        """The weekly summary names what the eligibility gate admitted, whichever
        gate is configured. Under `receipt` the eligible set is not "Posted" rows
        (#423): admission is a verified publication receipt."""
        counts = {
            "fetched": 947, "eligible": 929, "eligible_present": 929,
            "eligible_missing": 0, "status_skipped": 0, "invalid": 18,
            "gate": "receipt", "excluded": 0, "rights_denied": 0, "no_receipt": 0,
            "receipt_unverifiable": 0, "canonical_drift": 0,
            "present_by_title_drift": 0, "archive_articles": 932,
        }
        out = mod._render_summary(counts, since_hours=None)
        assert "- Eligible (admitted by the eligibility gate, valid): 929" in out
        assert "Posted" not in out


    def test_present_rows_are_present_without_any_lookup_and_absent_rows_are_explained(self, mod, schema):
        """The gate governs admission, never retention: an archived row is
        `eligible_present` under the receipt gate even if no receipt could be found
        for it today, and the verifier is consulted only for absent rows. Absent rows
        the gate does not admit are reported with class and reason."""
        archive = {"ids": {"rec1"}, "urls": set(), "titles": {mod.ing._normalize_title("A Title")}}
        recs = [
            _rec("rec1", url="https://www.firstaimovers.com/p/present-by-id", status="Draft"),
            _rec("rec2", url="https://www.firstaimovers.com/p/missing", title="Missing One", status="Draft"),
            _rec("rec3", url="https://www.firstaimovers.com/p/absent-no-receipt", title="Absent", status="Posted"),
        ]
        v = _StubVerifier(admit={"https://www.firstaimovers.com/p/missing"})  # NOT the present row
        detail = []
        counts, missing = mod.reconcile(recs, archive, schema, gate="receipt", verifier=v, detail=detail)
        assert counts["eligible_present"] == 1 and counts["eligible_missing"] == 1 and missing == ["rec2"]
        assert counts["no_receipt"] == 1
        assert v.calls == [("decide", "https://www.firstaimovers.com/p/missing"),
                           ("decide", "https://www.firstaimovers.com/p/absent-no-receipt")]
        assert detail == [("rec3", "no_receipt", "stub (editorial_status='posted')")]


class TestIncidentFamilyIsBounded:
    """The discrepancy family must be bounded at both ends (#473).

    Dedupe bounds how fast the family grows. Only a closer bounds how large it
    gets, and this workflow had no closer at all: its alarm step is gated on
    `missing != '0'`, so on a clean run nothing executed and a resolved
    discrepancy stayed open until a human noticed. #342, #369 and #470 were
    three filings of this one family and all three were closed by hand; #369
    outlived its own discrepancy by at least nine days. This is the signal
    #423 verifies its backlog drain against, so a stale positive is expensive.
    """

    def _text(self):
        from pathlib import Path
        p = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "audit-airtable-reconciliation.yml"
        return p.read_text(encoding="utf-8")

    def _steps(self):
        yaml = pytest.importorskip("yaml")
        wf = yaml.safe_load(self._text())
        return wf["jobs"]["reconcile"]["steps"]

    def _named(self, fragment):
        matches = [s for s in self._steps() if fragment in (s.get("name") or "")]
        assert len(matches) == 1, (
            f"expected exactly one step whose name contains {fragment!r}, found {len(matches)}"
        )
        return matches[0]

    def test_a_closer_step_exists_and_actually_closes(self):
        run = self._named("Close the discrepancy issue")["run"]
        assert "gh issue close" in run, "the closer step must actually close the issue"
        # A closer that comments instead of closing looks right and bounds
        # nothing. The closing note rides on `gh issue close --comment`, so a
        # bare `gh issue comment` in this step means some path reports success
        # having left the issue open.
        assert "gh issue comment" not in run, (
            "the closer must close, not comment: the explanatory note belongs on "
            "`gh issue close --comment`. A `gh issue comment` call here means a path "
            "reports success while the issue stays open."
        )
        assert "--comment" in run, (
            "closing without a reason leaves no trace of which run resolved it"
        )

    def test_closer_runs_exactly_when_the_backlog_is_clear(self):
        cond = self._named("Close the discrepancy issue")["if"]
        assert "steps.recon.outputs.missing == '0'" in cond, (
            f"the closer must be gated on a clean reconciliation; got {cond!r}"
        )

    def test_closer_never_runs_on_a_gate_override_report(self):
        """An override run is a report; its counts do not describe the tracked backlog."""
        cond = self._named("Close the discrepancy issue")["if"]
        assert "inputs.eligibility_gate == ''" in cond, (
            "a gate-override run must never close the discrepancy issue -- its counts "
            f"describe a hypothetical gate, not the live backlog; got {cond!r}"
        )

    def test_alarm_and_closer_are_complementary(self):
        """No live-gate outcome may leave both steps idle, or fire both."""
        alarm = self._named("Open deduplicated discrepancy issue")["if"]
        closer = self._named("Close the discrepancy issue")["if"]
        assert "missing != '0'" in alarm and "missing == '0'" in closer, (
            "the two steps must partition the outcome space on the live-gate path, "
            f"otherwise a state exists with no owner.\n  alarm:  {alarm}\n  closer: {closer}"
        )

    def test_neither_step_dedupes_through_the_search_index(self):
        """`--search` fails open when the index lags, and files a duplicate (#462)."""
        for fragment in ("Open deduplicated discrepancy issue", "Close the discrepancy issue"):
            # Strip shell comments first: both steps *explain* why they avoid
            # `--search`, and prose naming the flag is not a use of it.
            run = "\n".join(
                line for line in self._named(fragment)["run"].splitlines()
                if not line.lstrip().startswith("#")
            )
            assert "--search" not in run, (
                f"{fragment!r} must not use `gh issue list --search`: the search index is "
                "eventually consistent, and when it lags the dedupe fails open and files a "
                "duplicate (that is how one block became #454-#458). Use a plain listing "
                "with a local exact-title filter."
            )
            assert "--json number,title" in run, (
                f"{fragment!r} must list titles so it can filter them locally"
            )

    def test_closer_is_best_effort_and_cannot_fail_the_run(self):
        run = self._named("Close the discrepancy issue")["run"]
        assert run.rstrip().endswith("exit 0"), (
            "incident bookkeeping must never fail the reconciliation run; a failed close "
            "costs a stale issue, a failed run costs the signal"
        )
        assert "set +e" in run, "the closer must not abort on the first non-zero gh exit"
