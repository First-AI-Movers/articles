#!/usr/bin/env python3
"""Tests for tools/recover_airtable_backlog.py.

Pure selection/apply logic exercised with synthetic REST-shaped records and a
tmp archive; no network is touched. The tool reuses ingest_airtable's field map /
validation / status gate / writer and audit_airtable_reconciliation's archive
index, so these tests exercise that shared contract via find_recoverable/apply.
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
    m = importlib.import_module("recover_airtable_backlog")
    yield m
    importlib.reload(m)


@pytest.fixture
def schema(mod):
    return mod.ing._load_schema()


def _rec(rid, *, url, title="A Title", status="Posted", date="2026-05-01"):
    """A REST-shaped Airtable record whose payload passes schema validation
    (slug derives from the GUID's last path segment)."""
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


EMPTY_ARCHIVE = {"ids": set(), "urls": set(), "titles": set()}


class TestFindRecoverable:
    def test_posted_valid_missing_is_recoverable(self, mod, schema):
        recs = [_rec("rec1", url="https://x.com/a")]
        got = mod.find_recoverable(recs, EMPTY_ARCHIVE, schema)
        assert [c["record_id"] for c in got] == ["rec1"]

    def test_present_by_id_excluded(self, mod, schema):
        recs = [_rec("rec1", url="https://x.com/a")]
        archive = {"ids": {"rec1"}, "urls": set()}
        assert mod.find_recoverable(recs, archive, schema) == []

    def test_present_by_canonical_url_excluded(self, mod, schema):
        # Re-created record (new id, same URL) must NOT be recovered again.
        recs = [_rec("recNEW", url="https://x.com/a")]
        archive = {"ids": {"recOLD"}, "urls": {"https://x.com/a"}}
        assert mod.find_recoverable(recs, archive, schema) == []

    def test_present_by_title_excluded(self, mod, schema):
        # Identity drift: new record id + new canonical URL, but the title is
        # already published -> NOT recoverable (would duplicate an article).
        recs = [_rec("recNEW", url="https://x.com/new-slug", title="Already Published")]
        archive = {"ids": set(), "urls": set(),
                   "titles": {mod.ing._normalize_title("Already Published")}}
        assert mod.find_recoverable(recs, archive, schema) == []

    def test_non_posted_excluded(self, mod, schema):
        recs = [_rec("rec1", url="https://x.com/a", status="Draft")]
        assert mod.find_recoverable(recs, EMPTY_ARCHIVE, schema) == []

    def test_invalid_blank_canonical_excluded(self, mod, schema):
        # Missing GUID/canonical -> no slug derivable -> schema-invalid -> excluded.
        rec = {"id": "recX", "fields": {"Title": "T", "FAIM Status": "Posted", "Pub Date": "2026-05-01", "Content HTML": "b"}}
        assert mod.find_recoverable([rec], EMPTY_ARCHIVE, schema) == []

    def test_deterministic_oldest_first(self, mod, schema):
        recs = [
            _rec("recB", url="https://x.com/b", date="2026-05-10"),
            _rec("recA", url="https://x.com/a", date="2026-05-01"),
            _rec("recC", url="https://x.com/c", date="2026-05-05"),
        ]
        got = [c["record_id"] for c in mod.find_recoverable(recs, EMPTY_ARCHIVE, schema)]
        assert got == ["recA", "recC", "recB"]  # ascending published_date

    def test_tiebreak_by_record_id(self, mod, schema):
        recs = [
            _rec("rec9", url="https://x.com/9", date="2026-05-01"),
            _rec("rec1", url="https://x.com/1", date="2026-05-01"),
        ]
        got = [c["record_id"] for c in mod.find_recoverable(recs, EMPTY_ARCHIVE, schema)]
        assert got == ["rec1", "rec9"]


class TestSelectBatch:
    def test_slices_oldest_n(self, mod):
        cands = [{"record_id": f"rec{i}"} for i in range(10)]
        assert [c["record_id"] for c in mod.select_batch(cands, 5)] == [f"rec{i}" for i in range(5)]

    def test_hard_max_rejected(self, mod):
        with pytest.raises(ValueError):
            mod.select_batch([], 6)

    def test_hard_max_is_five(self, mod):
        assert mod.HARD_MAX_BATCH == 5
        mod.select_batch([], 5)  # exactly 5 is allowed

    def test_zero_rejected(self, mod):
        with pytest.raises(ValueError):
            mod.select_batch([], 0)


class TestApplyBatch:
    def _payload(self, mod, schema, rid, url, date="2026-05-01"):
        cands = mod.find_recoverable([_rec(rid, url=url, date=date)], EMPTY_ARCHIVE, schema)
        return cands

    def test_dry_run_writes_nothing(self, mod, schema, tmp_path, monkeypatch):
        monkeypatch.setattr(mod.ing, "ARTICLES_DIR", tmp_path)
        sel = self._payload(mod, schema, "rec1", "https://x.com/a")
        results = mod.apply_batch(sel, dry_run=True)
        assert results[0]["created"] is True  # would-create
        assert list(tmp_path.iterdir()) == []  # nothing written

    def test_apply_writes_article(self, mod, schema, tmp_path, monkeypatch):
        monkeypatch.setattr(mod.ing, "ARTICLES_DIR", tmp_path)
        sel = self._payload(mod, schema, "rec1", "https://x.com/a")
        results = mod.apply_batch(sel, dry_run=False)
        assert results[0]["created"] is True
        folder = tmp_path / results[0]["folder"]
        assert (folder / "article.md").exists()
        meta = json.loads((folder / "metadata.json").read_text())
        assert meta["id"] == "rec1"
        assert meta["canonical_url"] == "https://x.com/a"

    def test_apply_is_idempotent(self, mod, schema, tmp_path, monkeypatch):
        monkeypatch.setattr(mod.ing, "ARTICLES_DIR", tmp_path)
        sel = self._payload(mod, schema, "rec1", "https://x.com/a")
        mod.apply_batch(sel, dry_run=False)
        # Second run over the same selection must skip (folder already exists).
        results2 = mod.apply_batch(sel, dry_run=False)
        assert results2[0]["created"] is False


class TestCounts:
    def test_counts_and_remaining(self, mod, schema, tmp_path, monkeypatch):
        monkeypatch.setattr(mod.ing, "ARTICLES_DIR", tmp_path)
        recs = [_rec(f"rec{i}", url=f"https://x.com/{i}", date=f"2026-05-0{i}", title=f"Title {i}") for i in range(1, 8)]
        candidates = mod.find_recoverable(recs, EMPTY_ARCHIVE, schema)
        selected = mod.select_batch(candidates, 5)
        results = mod.apply_batch(selected, dry_run=False)
        counts = mod._counts(recs, candidates, selected, results, dry_run=False)
        assert counts["fetched"] == 7
        assert counts["recoverable_backlog"] == 7
        assert counts["batch_selected"] == 5
        assert counts["created"] == 5
        assert counts["remaining_after_batch"] == 2


class TestRenderSummary:
    def test_backlog_label_is_gate_neutral(self, mod):
        """The summary names what the eligibility gate admitted, whichever gate is
        configured. Under `receipt` the backlog is not "valid Posted" rows (#423)."""
        counts = {
            "fetched": 7, "recoverable_backlog": 2, "batch_selected": 2, "created": 2,
            "skipped_existing": 0, "remaining_after_batch": 0, "dry_run": True,
        }
        out = mod._render_summary(counts)
        assert "- Recoverable backlog (admitted by the eligibility gate, missing): 2" in out
        assert "Posted" not in out


class _StubVerifier:
    def __init__(self, admit):
        self.admit = set(admit)
        self.calls = []

    def listed(self, fields, *, canonical_url, slug, license_value=""):
        raise AssertionError("recovery never needs the cheap check: present rows are skipped first")

    def decide(self, fields, *, canonical_url, slug, license_value=""):
        self.calls.append(canonical_url)
        class D:
            pass
        d = D()
        d.eligible = canonical_url in self.admit
        d.klass = "eligible" if d.eligible else "no_receipt"
        d.reason = "stub"
        d.receipt = ({"kind": "OWNED_SOURCE_URL", "url": canonical_url, "canonical_match": True,
                      "verified_at": "2026-09-18T11:02:00Z"} if d.eligible else None)
        return d


class TestReceiptGateRecovery:
    def test_bounded_backlog_is_receipt_admitted_absent_and_capped(self, mod, schema):
        """#423 predicate: recover rows the eligibility gate admitted that are
        absent (id / canonical URL / title). Pub Date recency never admits;
        already-present rows are the dedupe; the batch is hard-capped at 5."""
        recs = [
            _rec("recFreshPosted", url="https://www.firstaimovers.com/p/fresh-label",
                 status="Posted", date="2026-09-20", title="Fresh Label Only"),
            _rec("recStaleDraft", url="https://www.firstaimovers.com/p/stale-live",
                 status="Draft", date="2024-01-01", title="Stale But Live"),
            _rec("recPresentTitle", url="https://www.firstaimovers.com/p/other-slug",
                 status="Draft", date="2023-01-01", title="Already Published"),
        ]
        archive = {"ids": set(), "urls": set(),
                   "titles": {mod.ing._normalize_title("Already Published")}}
        v = _StubVerifier(admit={"https://www.firstaimovers.com/p/stale-live",
                                 "https://www.firstaimovers.com/p/other-slug"})
        cands = mod.find_recoverable(recs, archive, schema, gate="receipt", verifier=v)
        assert [c["record_id"] for c in cands] == ["recStaleDraft"]
        assert v.calls == [
            "https://www.firstaimovers.com/p/fresh-label",
            "https://www.firstaimovers.com/p/stale-live",
        ], "the title-deduped row must not reach the verifier"
        with pytest.raises(ValueError):
            mod.select_batch(cands, mod.HARD_MAX_BATCH + 1)
        assert [c["record_id"] for c in mod.select_batch(cands, mod.HARD_MAX_BATCH)] == [
            "recStaleDraft"
        ]

    def test_receipt_gate_selects_by_receipt_and_carries_it_to_the_writer(self, mod, monkeypatch, tmp_path):
        monkeypatch.setattr(mod.ing, "ARTICLES_DIR", tmp_path / "articles")
        schema = mod.ing._load_schema()
        archive = {"ids": set(), "urls": set(), "titles": set()}
        recs = [
            _rec("rec1", url="https://www.firstaimovers.com/p/live", status="Draft", date="2026-04-01"),
            _rec("rec2", url="https://www.firstaimovers.com/p/label-only", status="Posted", date="2026-04-02"),
        ]
        v = _StubVerifier(admit={"https://www.firstaimovers.com/p/live"})
        cands = mod.find_recoverable(recs, archive, schema, gate="receipt", verifier=v)
        assert [c["record_id"] for c in cands] == ["rec1"], "Posted without a receipt is not recoverable"
        assert cands[0]["receipt"]["kind"] == "OWNED_SOURCE_URL"
        results = mod.apply_batch(mod.select_batch(cands, 5), dry_run=False)
        assert results[0]["created"] is True
        meta = json.loads((tmp_path / "articles" / "2026-04-01-live" / "metadata.json").read_text())
        assert meta["publication_receipt"]["kind"] == "OWNED_SOURCE_URL"

    def test_status_gate_candidates_carry_no_receipt(self, mod, monkeypatch):
        monkeypatch.delenv(mod.ing.ELIGIBILITY_GATE_ENV, raising=False)
        schema = mod.ing._load_schema()
        archive = {"ids": set(), "urls": set(), "titles": set()}
        cands = mod.find_recoverable([_rec("rec1", url="https://x/p/a", status="Posted")], archive, schema)
        assert len(cands) == 1 and cands[0]["receipt"] is None


    def test_present_rows_never_reach_the_verifier(self, mod, monkeypatch):
        monkeypatch.delenv(mod.ing.ELIGIBILITY_GATE_ENV, raising=False)
        schema = mod.ing._load_schema()
        archive = {"ids": {"rec1"}, "urls": set(), "titles": set()}
        v = _StubVerifier(admit={"https://www.firstaimovers.com/p/missing"})
        cands = mod.find_recoverable(
            [_rec("rec1", url="https://www.firstaimovers.com/p/present", status="Posted"),
             _rec("rec2", url="https://www.firstaimovers.com/p/missing", title="Other", status="Posted")],
            archive, schema, gate="receipt", verifier=v)
        assert [c["record_id"] for c in cands] == ["rec2"]
        assert v.calls == ["https://www.firstaimovers.com/p/missing"]
