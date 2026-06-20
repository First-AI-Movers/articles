#!/usr/bin/env python3
"""Tests for the fresh-article candidate selector in tools/run_summary_batch.py.

These prove the freshness/lookback filter constrains missing-summary selection to
recently published articles and can NEVER select the older hard-residue backlog.
All tests are network-free and deterministic (the reference 'today' is pinned).
"""

from __future__ import annotations

import datetime
import json
import shutil
from pathlib import Path

import pytest

# tools/ is on sys.path via tools/tests/conftest.py.
import build_summaries as bs
import run_summary_batch as rsb
import verify_summaries as vs

# Pinned reference date so --fresh-days windows are deterministic.
TODAY = datetime.date(2026, 6, 4)


def _stage(tmp_path: Path, articles: list[dict]) -> Path:
    """Stage a fake repo with full control over where published_date lives.

    Each article dict may set:
      folder, slug, title, summary_short (=> already summarised, not a candidate),
      index_date  (published_date in the index entry — the PRIMARY source),
      meta_date   (published_date in metadata.json — the FALLBACK source).
    Omitting both leaves the article undateable.
    """
    (tmp_path / "articles").mkdir(exist_ok=True)
    (tmp_path / "summaries").mkdir(exist_ok=True)
    index_entries = []
    for a in articles:
        folder = a["folder"]
        slug = a.get("slug", folder)
        title = a.get("title", folder)
        adir = tmp_path / "articles" / folder
        adir.mkdir(parents=True, exist_ok=True)
        (adir / "article.md").write_text("# t\n\nBody text for " + folder + ".\n", encoding="utf-8")
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


def _select(tmp_path: Path, **kwargs):
    kwargs.setdefault("missing_only", True)
    kwargs.setdefault("slug", None)
    kwargs.setdefault("limit", 50)
    kwargs.setdefault("today", TODAY)
    return rsb.select_articles(tmp_path / "index.json", tmp_path / "articles", **kwargs)


def _folders(sel) -> list:
    return [a["folder"] for a in sel]


# ---------------------------------------------------------------------------
# Freshness inclusion / exclusion
# ---------------------------------------------------------------------------

def test_fresh_window_includes_recent_missing(tmp_path):
    _stage(tmp_path, [
        {"folder": "fresh", "index_date": "2026-06-01"},  # 3 days before TODAY
        {"folder": "old", "index_date": "2025-03-01"},    # hard residue
    ])
    assert _folders(_select(tmp_path, fresh_days=14)) == ["fresh"]


def test_old_residue_excluded_by_fresh_days(tmp_path):
    _stage(tmp_path, [
        {"folder": "old1", "index_date": "2025-03-01"},
        {"folder": "old2", "index_date": "2026-04-25"},  # residue's newest edge
    ])
    assert _folders(_select(tmp_path, fresh_days=14)) == []


def test_old_residue_excluded_by_published_after(tmp_path):
    _stage(tmp_path, [
        {"folder": "old", "index_date": "2026-04-25"},
        {"folder": "fresh", "index_date": "2026-05-20"},
    ])
    assert _folders(_select(tmp_path, published_after="2026-05-01")) == ["fresh"]


def test_both_flags_stricter_floor_wins(tmp_path):
    # fresh_days=30 => relative floor 2026-05-05; absolute floor 2026-05-20 wins.
    _stage(tmp_path, [
        {"folder": "between", "index_date": "2026-05-10"},  # in window, before abs floor
        {"folder": "newer", "index_date": "2026-05-25"},
    ])
    sel = _select(tmp_path, fresh_days=30, published_after="2026-05-20")
    assert _folders(sel) == ["newer"]


def test_missing_date_excluded_in_freshness_mode(tmp_path):
    _stage(tmp_path, [
        {"folder": "nodate"},  # no index_date, no meta_date
        {"folder": "fresh", "index_date": "2026-06-01"},
    ])
    assert _folders(_select(tmp_path, fresh_days=14)) == ["fresh"]


def test_invalid_date_excluded_in_freshness_mode(tmp_path):
    _stage(tmp_path, [
        {"folder": "bad", "index_date": "not-a-date"},
        {"folder": "empty", "index_date": "   "},
        {"folder": "fresh", "index_date": "2026-06-01"},
    ])
    assert _folders(_select(tmp_path, fresh_days=14)) == ["fresh"]


@pytest.mark.parametrize("limit", [1, 10, 1000])
def test_missing_only_plus_freshness_never_selects_residue(tmp_path, limit):
    arts = [{"folder": f"residue{i}", "index_date": f"2025-03-{(i % 27) + 1:02d}"} for i in range(20)]
    arts.append({"folder": "fresh", "index_date": "2026-06-01"})
    _stage(tmp_path, arts)
    sel = _select(tmp_path, fresh_days=14, published_after="2026-05-01", limit=limit)
    assert "fresh" in _folders(sel)
    assert all(not f.startswith("residue") for f in _folders(sel))


def test_limit_applies_after_freshness(tmp_path):
    arts = [{"folder": f"fresh{i}", "index_date": "2026-06-01"} for i in range(5)]
    arts += [{"folder": f"old{i}", "index_date": "2025-03-01"} for i in range(5)]
    _stage(tmp_path, arts)
    sel = _select(tmp_path, fresh_days=14, limit=3)
    assert len(sel) == 3
    assert all(f.startswith("fresh") for f in _folders(sel))


def test_date_source_index_primary_and_metadata_fallback(tmp_path):
    _stage(tmp_path, [
        {"folder": "idx", "index_date": "2026-06-01"},                                    # index only
        {"folder": "meta", "meta_date": "2026-06-01"},                                    # metadata-only fallback
        {"folder": "both_old_idx", "index_date": "2025-03-01", "meta_date": "2026-06-01"},  # index primary wins -> old -> drop
        {"folder": "none"},                                                               # undateable -> drop
    ])
    assert set(_folders(_select(tmp_path, fresh_days=14))) == {"idx", "meta"}


# ---------------------------------------------------------------------------
# No-flag parity + candidate report
# ---------------------------------------------------------------------------

def test_no_freshness_flag_unchanged(tmp_path):
    _stage(tmp_path, [
        {"folder": "old", "index_date": "2025-03-01"},
        {"folder": "fresh", "index_date": "2026-06-01"},
        {"folder": "done", "index_date": "2026-06-02", "summary_short": "x"},
    ])
    # No freshness flags -> identical to plain --missing-only (old NOT excluded).
    assert _folders(_select(tmp_path)) == ["old", "fresh"]


def test_candidate_report_counts_and_safe_identifiers(tmp_path):
    _stage(tmp_path, [
        {"folder": "fresh", "slug": "s-fresh", "index_date": "2026-06-01"},
        {"folder": "old", "index_date": "2025-03-01"},
        {"folder": "nodate"},
        {"folder": "done", "index_date": "2026-06-02", "summary_short": "x"},
    ])
    stats: dict = {}
    sel = _select(tmp_path, fresh_days=14, stats=stats)
    assert _folders(sel) == ["fresh"]
    assert stats["missing_candidates"] == 3        # fresh, old, nodate (done is summarised)
    assert stats["excluded_stale"] == 1            # old
    assert stats["excluded_undateable"] == 1       # nodate
    assert stats["selected_fresh"] == 1
    assert stats["cutoff"] == (TODAY - datetime.timedelta(days=14)).isoformat()

    report = rsb.build_candidate_report(sel, stats)
    assert "- fresh (slug: s-fresh)" in report
    assert "- old (slug" not in report           # excluded folder not in the selected list
    # The report is value-safe: no article body text.
    assert "Body text" not in report


# ---------------------------------------------------------------------------
# main()-level dry-run: no network, no writes, fresh-only, value-safe report
# ---------------------------------------------------------------------------

def test_main_dry_run_with_freshness_no_network_no_writes(tmp_path, monkeypatch):
    _stage(tmp_path, [
        {"folder": "fresh", "slug": "s-fresh", "index_date": "2026-06-01"},
        {"folder": "old", "index_date": "2025-03-01"},
    ])
    monkeypatch.setattr(rsb, "_today", lambda: TODAY)  # deterministic window

    def trip(*a, **kw):  # pragma: no cover - must not run
        raise AssertionError("freshness dry-run must not call network")

    monkeypatch.setattr(bs, "_http_post_json", trip)
    monkeypatch.setattr(vs, "_http_post_json", trip)

    report = Path("/tmp") / f"fresh-dryrun-report-{tmp_path.name}.md"
    cand = Path("/tmp") / f"fresh-dryrun-cand-{tmp_path.name}.md"
    try:
        rc = rsb.main([
            "--missing-only", "--fresh-days", "14",
            "--published-after", "2026-05-01", "--limit", "50", "--dry-run",
            "--articles-dir", str(tmp_path / "articles"),
            "--index-path", str(tmp_path / "index.json"),
            "--summaries-dir", str(tmp_path / "summaries"),
            "--report-path", str(report),
            "--candidate-report", str(cand),
        ])
        assert rc == 0
        # No review files and no metadata mutation.
        assert list((tmp_path / "summaries").glob("*.review.md")) == []
        old_meta = json.loads((tmp_path / "articles" / "old" / "metadata.json").read_text(encoding="utf-8"))
        assert "summary_short" not in old_meta
        # Candidate report written, fresh-only.
        assert cand.exists()
        text = cand.read_text(encoding="utf-8")
        assert "- fresh (slug: s-fresh)" in text
        assert "- old (slug" not in text
    finally:
        report.unlink(missing_ok=True)
        cand.unlink(missing_ok=True)


def test_bad_published_after_errors(tmp_path, capsys):
    _stage(tmp_path, [{"folder": "f", "index_date": "2026-06-01"}])
    report = Path("/tmp") / f"bad-pa-{tmp_path.name}.md"
    try:
        rc = rsb.main([
            "--missing-only", "--published-after", "June 1st", "--limit", "5",
            "--articles-dir", str(tmp_path / "articles"),
            "--index-path", str(tmp_path / "index.json"),
            "--summaries-dir", str(tmp_path / "summaries"),
            "--report-path", str(report),
        ])
        assert rc == 2
        assert "published-after" in capsys.readouterr().err
    finally:
        report.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Fail-closed on misconfiguration (Codex P1) + report dir creation (Codex P2)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad", [0, -1, -30])
def test_non_positive_fresh_days_rejected(tmp_path, bad):
    # A non-positive --fresh-days must NOT silently disable freshness (which
    # would sweep the old backlog). It is rejected fail-closed.
    _stage(tmp_path, [
        {"folder": "old", "index_date": "2025-03-01"},
        {"folder": "fresh", "index_date": "2026-06-01"},
    ])
    with pytest.raises(ValueError, match="fresh-days"):
        _select(tmp_path, fresh_days=bad)


def test_non_positive_fresh_days_does_not_disable_floor(tmp_path):
    # Guard against the regression directly: even combined with a valid
    # absolute floor, a non-positive relative window is rejected rather than
    # ignored, so the operator must fix the misconfiguration explicitly.
    _stage(tmp_path, [{"folder": "old", "index_date": "2025-03-01"}])
    with pytest.raises(ValueError, match="fresh-days"):
        _select(tmp_path, fresh_days=0, published_after="2026-05-01")


def test_main_non_positive_fresh_days_errors(tmp_path, capsys):
    _stage(tmp_path, [{"folder": "old", "index_date": "2025-03-01"}])
    report = Path("/tmp") / f"nonpos-fd-{tmp_path.name}.md"
    try:
        rc = rsb.main([
            "--missing-only", "--fresh-days", "0", "--limit", "5",
            "--articles-dir", str(tmp_path / "articles"),
            "--index-path", str(tmp_path / "index.json"),
            "--summaries-dir", str(tmp_path / "summaries"),
            "--report-path", str(report),
        ])
        assert rc == 2
        err = capsys.readouterr().err
        assert "fresh-days" in err
        # The backlog article was never selected (process exited before plan).
        assert "old" not in err or "ERROR" in err
    finally:
        report.unlink(missing_ok=True)


def test_candidate_report_creates_missing_parent_dirs(tmp_path):
    # --candidate-report under a not-yet-existing scratch dir must succeed
    # (parent created), matching the batch report writer — not crash with
    # FileNotFoundError after selection.
    # This test drives the CLI (rsb.main), whose --fresh-days floor is computed
    # from the real UTC `date.today()` (the pinned TODAY hook only applies to the
    # select_articles() helper the other tests use). A fixed fresh date rots out
    # of the 14-day window over time, so derive it relative to today.
    fresh_date = (datetime.date.today() - datetime.timedelta(days=3)).isoformat()
    _stage(tmp_path, [
        {"folder": "fresh", "slug": "s-fresh", "index_date": fresh_date},
        {"folder": "old", "index_date": "2025-03-01"},
    ])
    report = Path("/tmp") / f"cr-parent-report-{tmp_path.name}.md"
    cand = Path("/tmp") / f"cr-parent-{tmp_path.name}" / "nested" / "deeper" / "cand.md"
    assert not cand.parent.exists()
    try:
        rc = rsb.main([
            "--missing-only", "--fresh-days", "14", "--limit", "50", "--dry-run",
            "--articles-dir", str(tmp_path / "articles"),
            "--index-path", str(tmp_path / "index.json"),
            "--summaries-dir", str(tmp_path / "summaries"),
            "--report-path", str(report),
            "--candidate-report", str(cand),
        ])
        assert rc == 0
        assert cand.exists()
        text = cand.read_text(encoding="utf-8")
        assert "- fresh (slug: s-fresh)" in text
        assert "- old (slug" not in text
    finally:
        report.unlink(missing_ok=True)
        # Clean the scratch tree created under /tmp.
        shutil.rmtree(Path("/tmp") / f"cr-parent-{tmp_path.name}", ignore_errors=True)
