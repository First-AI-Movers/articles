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
        assert idx == {"ids": set(), "urls": set()}

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
