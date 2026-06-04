#!/usr/bin/env python3
"""Freshness-parity tests for tools/build_summaries.py.

run_summary_batch.py grew a published_date freshness selector; build_summaries.py
is the older/direct entrypoint and must not be able to bypass that window. These
tests prove build_summaries applies the SAME fresh-only semantics (relative
window, absolute floor, stricter-floor-wins, fail-closed on non-positive
--fresh-days, fail-closed-fresh on missing/invalid dates, default OFF) and that
its mirrored helpers agree with run_summary_batch's canonical implementation.

All tests are network-free and deterministic (reference 'today' is pinned).
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

import pytest

# tools/ is on sys.path via tools/tests/conftest.py.
import build_summaries as bs
import run_summary_batch as rsb

TODAY = datetime.date(2026, 6, 4)


def _stage(tmp_path: Path, articles: list[dict]) -> Path:
    """Stage a fake repo with control over where published_date lives.

    Each article dict may set: folder, slug, title, summary_short (=> already
    summarised, not a candidate), index_date (published_date in the index entry
    — PRIMARY), meta_date (published_date in metadata.json — FALLBACK). Omitting
    both leaves the article undateable.
    """
    (tmp_path / "articles").mkdir(exist_ok=True)
    index_entries = []
    for a in articles:
        folder = a["folder"]
        slug = a.get("slug", folder)
        title = a.get("title", folder)
        adir = tmp_path / "articles" / folder
        adir.mkdir(parents=True, exist_ok=True)
        (adir / "article.md").write_text("# t\n\nBody for " + folder + ".\n", encoding="utf-8")
        meta = {"folder": folder, "slug": slug, "title": title}
        if a.get("summary_short"):
            meta["summary_short"] = a["summary_short"]
        if "meta_date" in a:
            meta["published_date"] = a["meta_date"]
        (adir / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        entry = {"folder": folder, "slug": slug, "title": title}
        if "index_date" in a:
            entry["published_date"] = a["index_date"]
        index_entries.append(entry)
    (tmp_path / "index.json").write_text(
        json.dumps({"articles": index_entries}), encoding="utf-8"
    )
    return tmp_path


def _run_select(tmp_path: Path, monkeypatch, argv: list[str]):
    """Run build_summaries.main() against the staged repo, capturing the selected
    candidate folders WITHOUT running generation (selection-only parity)."""
    monkeypatch.setattr(bs, "ARTICLES_DIR", tmp_path / "articles")
    monkeypatch.setattr(bs, "INDEX_PATH", tmp_path / "index.json")
    monkeypatch.setattr(bs, "_today_fresh", lambda: TODAY)

    captured: dict = {}

    def _capture(args, candidates):
        captured["candidates"] = list(candidates)

    monkeypatch.setattr(bs, "_cmd_generate", _capture)
    monkeypatch.setattr(bs, "_cmd_apply", _capture)
    # Network trip-wire: selection must never touch the provider.
    def _trip(*a, **k):  # pragma: no cover - must not run
        raise AssertionError("selection must not call the network")
    monkeypatch.setattr(bs, "_http_post_json", _trip, raising=False)

    rc = bs.main(argv)
    folders = [c.get("folder") for c in captured.get("candidates", [])]
    return rc, folders


# ---------------------------------------------------------------------------
# Inclusion / exclusion parity
# ---------------------------------------------------------------------------

def test_fresh_window_includes_recent_missing(tmp_path, monkeypatch):
    _stage(tmp_path, [
        {"folder": "fresh", "index_date": "2026-06-01"},
        {"folder": "old", "index_date": "2025-03-01"},
    ])
    rc, folders = _run_select(tmp_path, monkeypatch, ["--missing-only", "--fresh-days", "14"])
    assert rc == 0
    assert folders == ["fresh"]


def test_old_residue_excluded_by_fresh_days(tmp_path, monkeypatch):
    _stage(tmp_path, [
        {"folder": "old1", "index_date": "2025-03-01"},
        {"folder": "old2", "index_date": "2026-04-25"},  # residue's newest edge
    ])
    rc, folders = _run_select(tmp_path, monkeypatch, ["--missing-only", "--fresh-days", "14"])
    assert rc == 0
    assert folders == []


def test_old_residue_excluded_by_published_after(tmp_path, monkeypatch):
    _stage(tmp_path, [
        {"folder": "old", "index_date": "2026-04-25"},
        {"folder": "fresh", "index_date": "2026-05-20"},
    ])
    rc, folders = _run_select(
        tmp_path, monkeypatch, ["--missing-only", "--published-after", "2026-05-01"]
    )
    assert rc == 0
    assert folders == ["fresh"]


def test_both_flags_stricter_floor_wins(tmp_path, monkeypatch):
    # fresh_days=30 => relative floor 2026-05-05; absolute floor 2026-05-20 wins.
    _stage(tmp_path, [
        {"folder": "between", "index_date": "2026-05-10"},
        {"folder": "newer", "index_date": "2026-05-25"},
    ])
    rc, folders = _run_select(
        tmp_path, monkeypatch,
        ["--missing-only", "--fresh-days", "30", "--published-after", "2026-05-20"],
    )
    assert rc == 0
    assert folders == ["newer"]


def test_missing_date_excluded_in_freshness_mode(tmp_path, monkeypatch):
    _stage(tmp_path, [
        {"folder": "nodate"},  # no index_date, no meta_date
        {"folder": "fresh", "index_date": "2026-06-01"},
    ])
    rc, folders = _run_select(tmp_path, monkeypatch, ["--missing-only", "--fresh-days", "14"])
    assert rc == 0
    assert folders == ["fresh"]


def test_invalid_date_excluded_in_freshness_mode(tmp_path, monkeypatch):
    _stage(tmp_path, [
        {"folder": "bad", "index_date": "not-a-date"},
        {"folder": "empty", "index_date": "   "},
        {"folder": "fresh", "index_date": "2026-06-01"},
    ])
    rc, folders = _run_select(tmp_path, monkeypatch, ["--missing-only", "--fresh-days", "14"])
    assert rc == 0
    assert folders == ["fresh"]


def test_date_source_index_primary_metadata_fallback(tmp_path, monkeypatch):
    _stage(tmp_path, [
        {"folder": "idx", "index_date": "2026-06-01"},
        {"folder": "meta", "meta_date": "2026-06-01"},  # index lacks date -> metadata fallback
        {"folder": "both_old_idx", "index_date": "2025-03-01", "meta_date": "2026-06-01"},  # index primary -> old -> drop
        {"folder": "none"},  # undateable -> drop
    ])
    rc, folders = _run_select(tmp_path, monkeypatch, ["--missing-only", "--fresh-days", "14"])
    assert rc == 0
    assert set(folders) == {"idx", "meta"}


@pytest.mark.parametrize("limit", [1, 10, 1000])
def test_missing_only_plus_freshness_never_selects_residue(tmp_path, monkeypatch, limit):
    arts = [{"folder": f"residue{i}", "index_date": f"2025-03-{(i % 27) + 1:02d}"} for i in range(20)]
    arts.append({"folder": "fresh", "index_date": "2026-06-01"})
    _stage(tmp_path, arts)
    rc, folders = _run_select(
        tmp_path, monkeypatch,
        ["--missing-only", "--fresh-days", "14", "--published-after", "2026-05-01",
         "--limit", str(limit)],
    )
    assert rc == 0
    assert "fresh" in folders
    assert all(not f.startswith("residue") for f in folders)


# ---------------------------------------------------------------------------
# Ordering: freshness BEFORE --batch-offset / --limit
# ---------------------------------------------------------------------------

def test_limit_applies_after_freshness(tmp_path, monkeypatch):
    arts = [{"folder": f"fresh{i}", "index_date": "2026-06-01"} for i in range(5)]
    arts += [{"folder": f"old{i}", "index_date": "2025-03-01"} for i in range(5)]
    _stage(tmp_path, arts)
    rc, folders = _run_select(
        tmp_path, monkeypatch, ["--missing-only", "--fresh-days", "14", "--limit", "3"]
    )
    assert rc == 0
    assert len(folders) == 3
    assert all(f.startswith("fresh") for f in folders)


def test_batch_offset_applies_after_freshness(tmp_path, monkeypatch):
    # 4 fresh + residue; freshness keeps the 4 fresh, then offset 2 skips the
    # first 2 fresh (NOT residue), leaving the last 2 fresh.
    arts = [{"folder": f"fresh{i}", "index_date": "2026-06-01"} for i in range(4)]
    arts += [{"folder": f"old{i}", "index_date": "2025-03-01"} for i in range(3)]
    _stage(tmp_path, arts)
    rc, folders = _run_select(
        tmp_path, monkeypatch,
        ["--missing-only", "--fresh-days", "14", "--batch-offset", "2"],
    )
    assert rc == 0
    assert folders == ["fresh2", "fresh3"]


# ---------------------------------------------------------------------------
# Default OFF parity + fail-closed misconfiguration
# ---------------------------------------------------------------------------

def test_no_freshness_flag_unchanged(tmp_path, monkeypatch):
    _stage(tmp_path, [
        {"folder": "old", "index_date": "2025-03-01"},
        {"folder": "fresh", "index_date": "2026-06-01"},
        {"folder": "done", "index_date": "2026-06-02", "summary_short": "x"},
    ])
    # No freshness flags -> identical to plain --missing-only (old NOT excluded,
    # undateable NOT excluded), order preserved.
    rc, folders = _run_select(tmp_path, monkeypatch, ["--missing-only"])
    assert rc == 0
    assert folders == ["old", "fresh"]


def test_no_flag_undateable_not_excluded(tmp_path, monkeypatch):
    # Without freshness flags, a missing published_date must NOT drop the article
    # (fail-closed-fresh applies ONLY when a freshness flag is active).
    _stage(tmp_path, [
        {"folder": "nodate"},
        {"folder": "dated", "index_date": "2025-01-01"},
    ])
    rc, folders = _run_select(tmp_path, monkeypatch, ["--missing-only"])
    assert rc == 0
    assert set(folders) == {"nodate", "dated"}


@pytest.mark.parametrize("bad", ["0", "-1", "-30"])
def test_non_positive_fresh_days_rejected(tmp_path, monkeypatch, capsys, bad):
    _stage(tmp_path, [
        {"folder": "old", "index_date": "2025-03-01"},
        {"folder": "fresh", "index_date": "2026-06-01"},
    ])
    rc, folders = _run_select(tmp_path, monkeypatch, ["--missing-only", "--fresh-days", bad])
    assert rc == 2
    assert "fresh-days" in capsys.readouterr().err
    assert folders == []  # never reached generation


def test_non_positive_fresh_days_rejected_even_with_floor(tmp_path, monkeypatch, capsys):
    _stage(tmp_path, [{"folder": "old", "index_date": "2025-03-01"}])
    rc, folders = _run_select(
        tmp_path, monkeypatch,
        ["--missing-only", "--fresh-days", "0", "--published-after", "2026-05-01"],
    )
    assert rc == 2
    assert "fresh-days" in capsys.readouterr().err


def test_bad_published_after_errors(tmp_path, monkeypatch, capsys):
    _stage(tmp_path, [{"folder": "f", "index_date": "2026-06-01"}])
    rc, folders = _run_select(
        tmp_path, monkeypatch, ["--missing-only", "--published-after", "June 1st"]
    )
    assert rc == 2
    assert "published-after" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# Direct cross-parity: mirrored helpers agree with the canonical ones
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fresh_days,published_after", [
    (None, None),
    (14, None),
    (None, "2026-05-01"),
    (30, "2026-05-20"),
    (7, "2026-04-01"),
    (1, "2026-06-04"),
])
def test_freshness_cutoff_matches_run_summary_batch(fresh_days, published_after):
    assert bs.freshness_cutoff(fresh_days, published_after, TODAY) == \
        rsb.freshness_cutoff(fresh_days, published_after, TODAY)


@pytest.mark.parametrize("bad", [0, -1, -99])
def test_both_reject_non_positive_fresh_days(bad):
    with pytest.raises(ValueError, match="fresh-days"):
        bs.freshness_cutoff(bad, None, TODAY)
    with pytest.raises(ValueError, match="fresh-days"):
        rsb.freshness_cutoff(bad, None, TODAY)


@pytest.mark.parametrize("value,expected", [
    ("2026-06-01", datetime.date(2026, 6, 1)),
    ("2026-06-01T12:00:00Z", datetime.date(2026, 6, 1)),
    ("   ", None),
    ("not-a-date", None),
    (None, None),
    (12345, None),
])
def test_parse_iso_date_matches_run_summary_batch(value, expected):
    assert bs._parse_iso_date(value) == expected
    assert rsb._parse_iso_date(value) == expected
