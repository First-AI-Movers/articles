#!/usr/bin/env python3
"""Tests for ingest_airtable.py's oldest-backlog top-up (recurrence prevention).

Exercises main()'s two-pass flow with a monkeypatched _fetch_records (no
network), a tmp ARTICLES_DIR, and a tmp SUMMARY_PATH. Verifies:
  * recent-window records keep priority; unused capacity fills from the oldest
    backlog;
  * the --max-created cap bounds total creates;
  * the top-up is off unless --backfill-oldest is set and --max-created is given;
  * when the recent window already fills the cap, the backlog fetch never runs.
"""

import importlib
import json
import sys

import pytest

pytest.importorskip("requests")


@pytest.fixture
def ing(tmp_path, monkeypatch):
    sys.path.insert(0, "tools")
    m = importlib.import_module("ingest_airtable")
    monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
    monkeypatch.setattr(m, "SUMMARY_PATH", tmp_path / "ingest-summary.json")
    monkeypatch.setenv("AIRTABLE_PAT", "patDUMMY")
    monkeypatch.setenv("AIRTABLE_BASE_ID", "appDUMMY")
    monkeypatch.setenv("AIRTABLE_TABLE_NAME", "Table")
    monkeypatch.delenv("AIRTABLE_VIEW_NAME", raising=False)
    yield m
    importlib.reload(m)


def _rec(rid, *, n, status="Posted", date="2026-05-01"):
    return {
        "id": rid,
        "fields": {
            "Title": f"Title {n}",
            "GUID": f"https://x.com/{n}",
            "FAIM Status": status,
            "Pub Date": date,
            "Content HTML": "body",
        },
    }


def _install_fetch(ing, monkeypatch, recent, oldest):
    calls = {"recent": 0, "oldest": 0}

    def fake(pat, base_id, table_name, view_name=None, since_hours=None,
             record_id=None, limit=None, sort_direction=None):
        if sort_direction == "asc" and since_hours is None:
            calls["oldest"] += 1
            yield from oldest
        else:
            calls["recent"] += 1
            yield from recent

    monkeypatch.setattr(ing, "_fetch_records", fake)
    return calls


def _created(ing):
    return json.loads(ing.SUMMARY_PATH.read_text())["created"]


def test_topup_fills_unused_capacity(ing, monkeypatch):
    recent = [_rec("recR1", n=1), _rec("recR2", n=2)]
    oldest = [_rec(f"recO{i}", n=100 + i) for i in range(1, 8)]
    calls = _install_fetch(ing, monkeypatch, recent, oldest)
    rc = ing.main(["--write", "--max-created", "5", "--backfill-oldest", "--since-hours", "72"])
    assert rc == 0
    assert _created(ing) == 5          # 2 recent + 3 backfill top-up
    assert calls["recent"] == 1 and calls["oldest"] == 1


def test_no_topup_without_flag(ing, monkeypatch):
    recent = [_rec("recR1", n=1), _rec("recR2", n=2)]
    oldest = [_rec(f"recO{i}", n=100 + i) for i in range(1, 8)]
    calls = _install_fetch(ing, monkeypatch, recent, oldest)
    ing.main(["--write", "--max-created", "5", "--since-hours", "72"])
    assert _created(ing) == 2          # only the recent window
    assert calls["oldest"] == 0        # backlog fetch never happened


def test_no_topup_without_max_created(ing, monkeypatch):
    recent = [_rec("recR1", n=1)]
    oldest = [_rec(f"recO{i}", n=100 + i) for i in range(1, 5)]
    calls = _install_fetch(ing, monkeypatch, recent, oldest)
    ing.main(["--write", "--backfill-oldest", "--since-hours", "72"])
    assert _created(ing) == 1
    assert calls["oldest"] == 0        # unbounded -> top-up skipped


def test_recent_fills_cap_skips_backlog(ing, monkeypatch):
    recent = [_rec(f"recR{i}", n=i) for i in range(1, 7)]   # 6 recent
    oldest = [_rec(f"recO{i}", n=100 + i) for i in range(1, 5)]
    calls = _install_fetch(ing, monkeypatch, recent, oldest)
    ing.main(["--write", "--max-created", "5", "--backfill-oldest", "--since-hours", "72"])
    assert _created(ing) == 5          # cap hit in the recent pass
    assert calls["oldest"] == 0        # backlog fetch never happened


def test_topup_pages_past_present_to_reach_missing(ing, monkeypatch):
    # Codex P2: aged-out missing records are NOT the oldest by Date Added — many
    # already-present records precede them. The top-up must page PAST the present
    # ones (skips don't consume the cap) and still create the missing ones.
    present = [_rec(f"recP{i}", n=200 + i) for i in range(1, 4)]
    missing = [_rec("recM1", n=301), _rec("recM2", n=302)]
    schema = ing._load_schema()
    for rec in present:  # pre-populate the archive with the present records
        ing._write_article(ing._record_to_payload(rec), rec["id"], False)
    _install_fetch(ing, monkeypatch, [], present + missing)
    ing.main(["--write", "--max-created", "5", "--backfill-oldest", "--since-hours", "72"])
    assert _created(ing) == 2   # only the 2 missing, after paging past 3 present


def test_topup_respects_status_gate(ing, monkeypatch):
    recent = []
    # Only 2 of 4 oldest are Posted; the other 2 are Draft and must be skipped.
    oldest = [
        _rec("recO1", n=101, status="Posted"),
        _rec("recO2", n=102, status="Draft"),
        _rec("recO3", n=103, status="Posted"),
        _rec("recO4", n=104, status="Draft"),
    ]
    _install_fetch(ing, monkeypatch, recent, oldest)
    ing.main(["--write", "--max-created", "5", "--backfill-oldest", "--since-hours", "72"])
    assert _created(ing) == 2          # only the Posted ones
