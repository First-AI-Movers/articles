#!/usr/bin/env python3
"""Tests for <MODULE>."""

import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from xml.etree.ElementTree import fromstring

import pytest

class TestBuildLlmsFull:
    """Full-corpus concatenation for LLM ingestion."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def _run(self, monkeypatch, tmp_path, articles_on_disk=None):
        """Build llms-full.txt against a synthetic corpus."""
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        index = {"articles": []}
        for spec in (articles_on_disk or []):
            folder = spec["folder"]
            (tmp_path / "articles" / folder).mkdir(exist_ok=True)
            (tmp_path / "articles" / folder / "article.md").write_text(
                spec.get("body", f"---\ntitle: {spec['title']}\n---\n# {spec['title']}\n\nBody of {folder}.\n"))
            index["articles"].append({
                "folder": folder,
                "title": spec["title"],
                "published_date": spec["published_date"],
                "tags": spec.get("tags", []),
                "topics": spec.get("topics", []),
                "funnel_stage": "middle",
                "canonical_url": spec.get("canonical_url", f"https://radar.firstaimovers.com/{folder}"),
            })
        index["articles"].sort(key=lambda a: a["published_date"], reverse=True)
        m.build_llms_full(index)
        return (tmp_path / "llms-full.txt").read_text(encoding="utf-8")

    def test_header_contains_corpus_metadata(self, monkeypatch, tmp_path):
        out = self._run(monkeypatch, tmp_path, [
            {"folder": "2026-01-01-first", "title": "First", "published_date": "2026-01-01"},
        ])
        assert "First AI Movers — Full Article Archive" in out
        assert "CC BY 4.0" in out
        assert "ORCID 0000-0002-6813-4641" in out

    def test_articles_emitted_newest_first(self, monkeypatch, tmp_path):
        out = self._run(monkeypatch, tmp_path, [
            {"folder": "2025-06-01-older", "title": "Older Article", "published_date": "2025-06-01"},
            {"folder": "2026-04-01-newer", "title": "Newer Article", "published_date": "2026-04-01"},
        ])
        assert out.index("Newer Article") < out.index("Older Article")

    def test_per_entry_header_has_title_date_url_topics(self, monkeypatch, tmp_path):
        out = self._run(monkeypatch, tmp_path, [
            {"folder": "2026-04-01-x", "title": "The Title", "published_date": "2026-04-01",
             "topics": ["AI Strategy", "European SME AI"],
             "canonical_url": "https://radar.firstaimovers.com/the-title"},
        ])
        assert "# The Title" in out
        assert "**Published:** 2026-04-01" in out
        assert "**URL:** https://radar.firstaimovers.com/the-title" in out
        assert "**Topics:** AI Strategy, European SME AI" in out

    def test_leading_h1_in_body_is_stripped(self, monkeypatch, tmp_path):
        out = self._run(monkeypatch, tmp_path, [
            {"folder": "2026-04-01-x", "title": "The Title", "published_date": "2026-04-01",
             "body": "---\ntitle: x\n---\n# Duplicate Heading\n\nBody text here."},
        ])
        # Only the emitted header H1 should be present; body's H1 stripped
        assert out.count("# Duplicate Heading") == 0
        assert "Body text here." in out

    def test_missing_article_md_is_skipped_not_fatal(self, monkeypatch, tmp_path):
        m = self._mod()
        (tmp_path / "articles").mkdir()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        # Folder referenced in index but no file on disk
        index = {"articles": [
            {"folder": "ghost", "title": "Ghost", "published_date": "2026-01-01",
             "tags": [], "canonical_url": "https://radar.firstaimovers.com/ghost"},
        ]}
        m.build_llms_full(index)  # must not raise
        out = (tmp_path / "llms-full.txt").read_text(encoding="utf-8")
        assert "Ghost" not in out  # skipped entirely
        assert "Articles: 1" in out  # header still computed from index total

    def test_newline_canonical_is_cleaned(self, monkeypatch, tmp_path):
        """LinkedIn-batch articles have newlines inside the canonical_url value."""
        out = self._run(monkeypatch, tmp_path, [
            {"folder": "2026-01-21-x", "title": "LinkedIn One",
             "published_date": "2026-01-21",
             "canonical_url": "\nhttps://www.linkedin.com/pulse/linkedin-one\n"},
        ])
        assert "**URL:** https://www.linkedin.com/pulse/linkedin-one" in out


# =========================================================================
# Tests: normalize_tags.py — tag -> topic normalization
# =========================================================================


class TestBuildLlmsIndex:
    """Middle-context corpus catalog for LLM discovery."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def _run(self, monkeypatch, tmp_path, articles_on_disk):
        """Build llms-index.txt against a synthetic corpus and return the
        rendered text. Mirrors the harness used by TestBuildLlmsFull /
        TestBuildLlmsRecent.
        """
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        index = {"articles": []}
        for spec in articles_on_disk:
            folder = spec["folder"]
            (tmp_path / "articles" / folder).mkdir(exist_ok=True)
            body = spec.get(
                "body",
                f"---\ntitle: {spec['title']}\n---\n\n"
                f"Body of {folder} with enough prose to look like a paragraph "
                f"for the summary extractor. " * 4,
            )
            (tmp_path / "articles" / folder / "article.md").write_text(
                body, encoding="utf-8"
            )
            entry = {
                "folder": folder,
                "title": spec["title"],
                "published_date": spec["published_date"],
                "tags": spec.get("tags", []),
                "topics": spec.get("topics", []),
                "funnel_stage": "middle",
                "canonical_url": spec.get(
                    "canonical_url",
                    f"https://radar.firstaimovers.com/{folder}",
                ),
            }
            if "summary_short" in spec:
                entry["summary_short"] = spec["summary_short"]
            if "doi" in spec:
                entry["doi"] = spec["doi"]
            if "series" in spec:
                entry["series"] = spec["series"]
            index["articles"].append(entry)
        index["articles"].sort(
            key=lambda a: a["published_date"], reverse=True
        )
        m.build_llms_index(index)
        return (tmp_path / "llms-index.txt").read_text(encoding="utf-8")

    def test_header_contains_corpus_metadata(self, monkeypatch, tmp_path):
        out = self._run(monkeypatch, tmp_path, [
            {"folder": "2026-01-01-first", "title": "First", "published_date": "2026-01-01"},
        ])
        assert "First AI Movers — Corpus Index" in out
        assert "Articles: 1" in out
        assert "CC BY 4.0" in out
        # Header points back to the corpus discovery file and to the full
        # corpus so an LLM reading the catalog knows where to look next.
        assert "/llms.txt" in out
        assert "/llms-full.txt" in out
        assert "/llms-recent.txt" in out
        assert "/index.json" in out

    def test_one_entry_per_article_newest_first(self, monkeypatch, tmp_path):
        out = self._run(monkeypatch, tmp_path, [
            {"folder": "2025-06-01-older", "title": "Older Article", "published_date": "2025-06-01"},
            {"folder": "2026-04-01-newer", "title": "Newer Article", "published_date": "2026-04-01"},
            {"folder": "2025-12-15-mid",   "title": "Mid Article",   "published_date": "2025-12-15"},
        ])
        # Newest-first order matches llms-full.txt / index.json.
        assert out.index("Newer Article") < out.index("Mid Article") < out.index("Older Article")
        # One H2 header per article.
        assert out.count("## Newer Article") == 1
        assert out.count("## Mid Article") == 1
        assert out.count("## Older Article") == 1

    def test_entry_contains_title_date_canonical_archive_topics_summary(
        self, monkeypatch, tmp_path
    ):
        out = self._run(monkeypatch, tmp_path, [{
            "folder": "2026-04-01-x",
            "title": "Example Article",
            "published_date": "2026-04-01",
            "topics": ["AI Strategy", "European SME AI", "Governance"],
            "canonical_url": "https://radar.firstaimovers.com/example-article",
            "summary_short": "A short curated summary of the article.",
        }])
        assert "## Example Article" in out
        assert "- Date: 2026-04-01" in out
        assert "- Canonical: https://radar.firstaimovers.com/example-article" in out
        assert "- Archive: https://articles.firstaimovers.com/articles/2026-04-01-x/article.md" in out
        assert "- Topics: AI Strategy, European SME AI, Governance" in out
        assert "- Summary: A short curated summary of the article." in out

    def test_falls_back_to_extracted_summary_when_summary_short_missing(
        self, monkeypatch, tmp_path
    ):
        """When `summary_short` is absent the index uses the same TL;DR/
        first-paragraph fallback that `_extract_summary` provides for
        feeds. Verifies the prose body shows up in the catalog.
        """
        out = self._run(monkeypatch, tmp_path, [{
            "folder": "2026-04-01-no-summary",
            "title": "NoSummary",
            "published_date": "2026-04-01",
            "body": (
                "---\ntitle: NoSummary\n---\n\n"
                "This is the leading prose paragraph that has enough words "
                "to satisfy the prose heuristic and serve as the fallback "
                "summary in the catalog.\n"
            ),
        }])
        assert "leading prose paragraph" in out

    def test_summary_is_truncated_at_bounded_length(self, monkeypatch, tmp_path):
        """Summaries are truncated to INDEX_SUMMARY_MAX_CHARS so the file
        size stays bounded; truncation produces an ellipsis.
        """
        m = self._mod()
        long_summary = (
            "A " * (m.INDEX_SUMMARY_MAX_CHARS // 2 + 100)
        ).strip()
        out = self._run(monkeypatch, tmp_path, [{
            "folder": "2026-04-01-long",
            "title": "Long",
            "published_date": "2026-04-01",
            "summary_short": long_summary,
        }])
        # Locate the rendered summary line.
        summary_lines = [
            ln for ln in out.splitlines() if ln.startswith("- Summary: ")
        ]
        assert summary_lines, f"No summary line in output:\n{out[:400]}"
        rendered = summary_lines[0][len("- Summary: "):]
        assert len(rendered) <= m.INDEX_SUMMARY_MAX_CHARS, (
            f"Summary length {len(rendered)} exceeds "
            f"INDEX_SUMMARY_MAX_CHARS={m.INDEX_SUMMARY_MAX_CHARS}"
        )
        assert rendered.endswith("…"), (
            f"Truncation should append an ellipsis; got: {rendered[-20:]!r}"
        )

    def test_topics_capped_per_entry(self, monkeypatch, tmp_path):
        """Topics are capped at INDEX_TOPICS_PER_ENTRY so a heavily-tagged
        article doesn't bloat the catalog.
        """
        m = self._mod()
        many = [f"topic-{i}" for i in range(m.INDEX_TOPICS_PER_ENTRY + 5)]
        out = self._run(monkeypatch, tmp_path, [{
            "folder": "2026-04-01-many-topics",
            "title": "ManyTopics",
            "published_date": "2026-04-01",
            "topics": many,
        }])
        topics_lines = [
            ln for ln in out.splitlines() if ln.startswith("- Topics: ")
        ]
        assert topics_lines
        rendered_topics = topics_lines[0][len("- Topics: "):].split(", ")
        assert len(rendered_topics) == m.INDEX_TOPICS_PER_ENTRY

    def test_no_full_article_body_in_catalog(self, monkeypatch, tmp_path):
        """The catalog is a discovery file; the full article body lives in
        `llms-full.txt`. Verify by writing a recognisable sentinel into
        the article body and asserting it does NOT appear in the index.
        """
        sentinel = "ZSENTINEL_BODY_TEXT_THAT_MUST_NEVER_LEAK_ZZQ"
        body = (
            "---\ntitle: WithBody\n---\n\n"
            "Short curated paragraph for the summary.\n\n"
            f"## Section\n\n{sentinel} appears only deep in the body.\n"
        )
        out = self._run(monkeypatch, tmp_path, [{
            "folder": "2026-04-01-body-leak",
            "title": "WithBody",
            "published_date": "2026-04-01",
            "summary_short": "Short curated paragraph for the summary.",
            "body": body,
        }])
        assert sentinel not in out, (
            "llms-index.txt must not include any article body content; "
            f"sentinel '{sentinel}' leaked into the catalog."
        )

    def test_optional_doi_and_series_rendered_when_present(
        self, monkeypatch, tmp_path
    ):
        out = self._run(monkeypatch, tmp_path, [{
            "folder": "2026-04-01-doi-series",
            "title": "WithDoiSeries",
            "published_date": "2026-04-01",
            "doi": "10.5281/zenodo.example",
            "series": {"slug": "prompt-engineering-10-day", "title": "Prompt Eng"},
        }])
        assert "- DOI: 10.5281/zenodo.example" in out
        assert "- Series: prompt-engineering-10-day" in out

    def test_size_bounded_for_large_corpus(self, monkeypatch, tmp_path):
        """A synthetic 200-article corpus must stay well under the 750 KB
        hard halt the implementation brief sets.
        """
        articles = [
            {
                "folder": f"2026-04-{(i % 28) + 1:02d}-article-{i}",
                "title": f"Article Number {i}",
                "published_date": f"2026-04-{(i % 28) + 1:02d}",
                "summary_short": "A typical short summary string for the catalog entry, kept under the truncation cap.",
                "topics": ["AI Strategy", "Governance", "European SME AI"],
            }
            for i in range(200)
        ]
        out = self._run(monkeypatch, tmp_path, articles)
        size_kb = len(out.encode("utf-8")) / 1024
        # 200 articles should comfortably stay under ~250 KB; assert a
        # generous bound that still catches accidental bloat.
        assert size_kb < 500, (
            f"Catalog of 200 synthetic articles must stay under 500 KB; "
            f"got {size_kb:.1f} KB."
        )


class TestBuildLlmsRecent:
    """Rolling window sibling of llms-full.txt."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def _run(self, monkeypatch, tmp_path, articles_on_disk):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        index = {"articles": []}
        for spec in articles_on_disk:
            folder = spec["folder"]
            (tmp_path / "articles" / folder).mkdir(exist_ok=True)
            (tmp_path / "articles" / folder / "article.md").write_text(
                f"---\ntitle: {spec['title']}\n---\n# {spec['title']}\n\nBody of {folder}.\n")
            index["articles"].append({
                "folder": folder,
                "title": spec["title"],
                "published_date": spec["published_date"],
                "tags": [], "topics": [],
                "funnel_stage": "middle",
                "canonical_url": f"https://radar.firstaimovers.com/{folder}",
            })
        index["articles"].sort(key=lambda a: a["published_date"], reverse=True)
        m.build_llms_recent(index)
        return (tmp_path / "llms-recent.txt").read_text(encoding="utf-8")

    def test_filters_to_window_relative_to_newest_not_today(self, monkeypatch, tmp_path):
        # Articles spanning 60 days; window should be 30 days back from newest.
        articles = [
            {"folder": "2026-04-20-new", "title": "NewArticle", "published_date": "2026-04-20"},
            {"folder": "2026-04-05-mid", "title": "MidArticle", "published_date": "2026-04-05"},
            {"folder": "2026-02-20-old", "title": "OldArticle", "published_date": "2026-02-20"},
        ]
        out = self._run(monkeypatch, tmp_path, articles)
        assert "NewArticle" in out
        assert "MidArticle" in out  # within 30 days of 2026-04-20
        assert "OldArticle" not in out  # 2026-02-20 is 59 days before newest

    def test_header_reports_window_count(self, monkeypatch, tmp_path):
        out = self._run(monkeypatch, tmp_path, [
            {"folder": "2026-04-20-a", "title": "A", "published_date": "2026-04-20"},
            {"folder": "2026-04-15-b", "title": "B", "published_date": "2026-04-15"},
        ])
        assert "Articles in window: 2" in out
        assert "Window: 2026-03-21 to 2026-04-20" in out

    def test_empty_index_writes_empty_file(self, monkeypatch, tmp_path):
        out = self._run(monkeypatch, tmp_path, [])
        assert out == ""

    def test_window_size_is_30_days(self):
        m = self._mod()
        assert m.LLMS_RECENT_DAYS == 30


# =========================================================================
# Tests: rebuild_local.py TL;DR extraction for Quick reads (E4)
# =========================================================================


class TestLlmsFullStability:
    """Prove llms-full.txt is deterministic for fixed input and fixed date."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def test_llms_full_identical_across_builds_for_fixed_date(self, monkeypatch, tmp_path):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        index = {"articles": [
            {"folder": "2026-04-01-a", "title": "A", "published_date": "2026-04-01",
             "tags": [], "topics": ["AI Strategy"],
             "canonical_url": "https://radar.firstaimovers.com/a"},
            {"folder": "2026-03-01-b", "title": "B", "published_date": "2026-03-01",
             "tags": [], "topics": ["AI Strategy"],
             "canonical_url": "https://radar.firstaimovers.com/b"},
        ]}
        for a in index["articles"]:
            d = tmp_path / "articles" / a["folder"]
            d.mkdir(exist_ok=True)
            (d / "article.md").write_text(f"---\ntitle: {a['title']}\n---\n# {a['title']}\n\nBody.\n")

        class _FixedDate:
            @staticmethod
            def today(): return __import__("datetime").date(2026, 4, 1)
            @classmethod
            def __getattr__(cls, name): return getattr(__import__("datetime").date, name)

        monkeypatch.setattr(m, "date", _FixedDate())
        m.build_llms_full(index)
        first = (tmp_path / "llms-full.txt").read_text(encoding="utf-8")
        m.build_llms_full(index)
        second = (tmp_path / "llms-full.txt").read_text(encoding="utf-8")
        assert first == second

    def test_llms_recent_identical_across_builds_for_fixed_date(self, monkeypatch, tmp_path):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        index = {"articles": [
            {"folder": "2026-04-01-a", "title": "A", "published_date": "2026-04-01",
             "tags": [], "topics": [], "canonical_url": "https://radar.firstaimovers.com/a"},
        ]}
        for a in index["articles"]:
            d = tmp_path / "articles" / a["folder"]
            d.mkdir(exist_ok=True)
            (d / "article.md").write_text(f"---\ntitle: {a['title']}\n---\n# {a['title']}\n\nBody.\n")

        class _FixedDate:
            @staticmethod
            def today(): return __import__("datetime").date(2026, 4, 1)
            @classmethod
            def __getattr__(cls, name): return getattr(__import__("datetime").date, name)

        monkeypatch.setattr(m, "date", _FixedDate())
        m.build_llms_recent(index)
        first = (tmp_path / "llms-recent.txt").read_text(encoding="utf-8")
        m.build_llms_recent(index)
        second = (tmp_path / "llms-recent.txt").read_text(encoding="utf-8")
        assert first == second


REPO_ROOT_FOR_LLMS_TXT = Path(__file__).resolve().parents[2]


class TestLlmsTxtPointers:
    """Hand-maintained `llms.txt` must point readers at the corpus catalog
    (`llms-index.txt`) introduced by PR #218 so an LLM landing on the
    discovery file can find the middle-context layer between
    `llms-recent.txt` and `llms-full.txt`.
    """

    def test_llms_txt_references_corpus_index(self):
        text = (REPO_ROOT_FOR_LLMS_TXT / "llms.txt").read_text(encoding="utf-8")
        assert "llms-index.txt" in text, (
            "llms.txt must list llms-index.txt so LLMs can discover the "
            "middle-context corpus catalog."
        )


# =========================================================================
# Tests: E8 hardening — XSS resistance
# =========================================================================


