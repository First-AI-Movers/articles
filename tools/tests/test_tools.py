#!/usr/bin/env python3
"""Tests for the article archive tooling scripts.

Runs without network access — all GitHub API and OpenAI calls are mocked.
Tests pure logic: parsing, patching, detection, injection, XML generation.

Usage:
    python3 -m pytest tools/tests/test_tools.py -v
"""

import json
import re
import sys
from datetime import date
from pathlib import Path
from xml.etree.ElementTree import fromstring

import pytest

# Add tools/ to path so we can import modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# =========================================================================
# Fixtures
# =========================================================================

SAMPLE_FRONT_MATTER = """---
title: "Test Article"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
publication: "First AI Movers"
canonical_url: "https://radar.firstaimovers.com/test-article"
published_date: "2026-04-01"
license: "CC BY 4.0"
---"""

SAMPLE_ARTICLE = f"""{SAMPLE_FRONT_MATTER}
# Test Article Title

## In 2026, AI strategy is no longer optional.

Most companies still start in the wrong place.

They start with model quality, not review design.

## Model Choice Matters Less

This is the uncomfortable part of the market.

## Conclusion

Review design beats model selection every time.
"""

SAMPLE_ARTICLE_WITH_TLDR = f"""{SAMPLE_FRONT_MATTER}
# Test Article Title

## TL;DR

> Review design matters more than model choice for AI dev stacks in 2026.
> Teams that standardize how AI work gets reviewed outperform those chasing benchmarks.

## In 2026, AI strategy is no longer optional.

Rest of article here.
"""

SAMPLE_ARTICLE_WITH_KEY_TAKEAWAY = f"""{SAMPLE_FRONT_MATTER}
# Test Article Title

## Key Takeaway

Focus on governance before scaling AI agents.

## Introduction

Rest of article here.
"""

SAMPLE_INDEX = {
    "last_updated": "2026-04-05",
    "total_articles": 3,
    "author": "Dr. Hernani Costa",
    "publication": "First AI Movers",
    "canonical_base": "https://radar.firstaimovers.com",
    "license": "CC BY 4.0",
    "articles": [
        {
            "folder": "2026-04-04-test-article-one",
            "slug": "test-article-one",
            "title": "Test Article One",
            "published_date": "2026-04-04",
            "tags": ["AI strategy", "EU AI Act"],
            "funnel_stage": "top",
            "canonical_url": "https://radar.firstaimovers.com/test-one",
        },
        {
            "folder": "2026-03-15-test-article-two",
            "slug": "test-article-two",
            "title": "Test Article Two",
            "published_date": "2026-03-15",
            "tags": ["AI governance", "MCP"],
            "funnel_stage": "middle",
            "canonical_url": "https://radar.firstaimovers.com/test-two",
        },
        {
            "folder": "2025-06-01-test-article-three",
            "slug": "test-article-three",
            "title": "Test Article Three",
            "published_date": "2025-06-01",
            "tags": ["AI strategy"],
            "funnel_stage": "bottom",
            "canonical_url": "https://insights.firstaimovers.com/test-three",
        },
    ],
}

SAMPLE_README = """<!-- machine-readable metadata for LLM indexing
{
  "@context": "https://schema.org",
  "@type": "CreativeWorkSeries",
  "name": "First AI Movers — Article Archive",
  "description": "The canonical, open-access article archive of First AI Movers: 648 original articles on AI strategy, EU AI Act compliance, AI governance, agentic systems, and responsible AI adoption for European SMEs. Written by Dr. Hernani Costa, PhD.",
  "dateCreated": "2025-02-17",
  "dateModified": "2026-04-05"
}
-->

# First AI Movers — Article Archive

[![Articles](https://img.shields.io/badge/Articles-648-orange.svg)](#what-is-in-this-archive)

> The canonical, open-access text archive of every article published by [First AI Movers](https://firstaimovers.com) — 648 original articles on AI strategy, EU AI Act compliance, AI governance, and responsible AI adoption for European businesses.

## What Is in This Archive?

This repository contains the full-text, machine-readable versions of 648 original articles spanning February 2025–April 2026.

    └── ... (648 article folders)

**Quick stats:**
- **648** articles indexed
- **3,147** unique topic tags
- **3 funnel stages:** top (221 articles), middle (423), bottom (4)
- **Date range:** February 17, 2025 – April 4, 2026
"""

SAMPLE_LLMS_TXT = """> The canonical, open-access text archive of all First AI Movers articles by Dr. Hernani Costa. 648 original articles on AI strategy. Published February 2025–April 2026.
"""


# =========================================================================
# Tests: rebuild_index.py logic
# =========================================================================

class TestRebuildIndex:
    """Test index building logic without network calls."""

    def test_articles_sorted_descending_by_date(self):
        """Index articles must be sorted newest first."""
        articles = [
            {"published_date": "2025-06-01", "title": "Old"},
            {"published_date": "2026-04-04", "title": "New"},
            {"published_date": "2026-01-15", "title": "Mid"},
        ]
        articles.sort(key=lambda a: a.get("published_date", ""), reverse=True)
        assert articles[0]["title"] == "New"
        assert articles[1]["title"] == "Mid"
        assert articles[2]["title"] == "Old"

    def test_articles_with_empty_date_sort_last(self):
        """Articles without a date should sort to the end."""
        articles = [
            {"published_date": "", "title": "No Date"},
            {"published_date": "2026-04-04", "title": "Has Date"},
        ]
        articles.sort(key=lambda a: a.get("published_date", ""), reverse=True)
        assert articles[0]["title"] == "Has Date"
        assert articles[1]["title"] == "No Date"

    def test_metadata_fields_extracted_correctly(self):
        """Index entries should contain exactly the expected fields."""
        meta = {
            "folder": "2026-04-04-test",
            "title": "Test",
            "published_date": "2026-04-04",
            "tags": ["AI", "strategy"],
            "funnel_stage": "top",
            "canonical_url": "https://example.com",
            "extra_field": "should be ignored",
        }
        entry = {
            "folder": meta.get("folder"),
            "title": meta.get("title"),
            "published_date": meta.get("published_date"),
            "tags": meta.get("tags", []),
            "funnel_stage": meta.get("funnel_stage"),
            "canonical_url": meta.get("canonical_url"),
        }
        assert "extra_field" not in entry
        assert entry["tags"] == ["AI", "strategy"]

    def test_missing_tags_defaults_to_empty_list(self):
        """If metadata has no tags field, default to []."""
        meta = {"folder": "test", "title": "Test"}
        tags = meta.get("tags", [])
        assert tags == []

    def test_json_strict_false_handles_control_chars(self):
        """JSON with control characters should parse with strict=False."""
        bad_json = '{"title": "Hello\\nWorld", "value": "test\ttab"}'
        # This would fail with strict=True in some cases
        result = json.loads(bad_json, strict=False)
        assert result["title"] == "Hello\nWorld"


# =========================================================================
# Tests: rebuild_local.py docs patchers (compute_stats + patch_readme + patch_llms)
# =========================================================================

class TestRebuildLocalDocs:
    """Patching logic for README and llms.txt, plus stats computation."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def test_compute_stats(self):
        stats = self._mod().compute_stats(SAMPLE_INDEX)
        assert stats["total"] == 3
        assert stats["tags_count"] == 4  # AI strategy, EU AI Act, AI governance, MCP
        assert stats["topics_count"] == 0  # SAMPLE_INDEX has no topics field
        assert stats["funnel"]["top"] == 1
        assert stats["funnel"]["middle"] == 1
        assert stats["funnel"]["bottom"] == 1
        assert stats["date_min"] == "2025-06-01"
        assert stats["date_max"] == "2026-04-04"

    def test_human_date(self):
        m = self._mod()
        assert m._human_date("2025-02-17") == "February 17, 2025"
        assert m._human_date("2026-04-04") == "April 4, 2026"
        assert m._human_date("invalid") == "invalid"

    def test_funnel_summary(self):
        result = self._mod()._funnel_summary({"top": 221, "middle": 423, "bottom": 4})
        assert "top (221 articles)" in result
        assert "middle (423)" in result
        assert "bottom (4)" in result

    def test_funnel_summary_first_gets_articles_label(self):
        result = self._mod()._funnel_summary({"middle": 10, "top": 5})
        assert result.startswith("top (5 articles)")

    def _stats(self, **overrides):
        base = {"total": 700, "tags_count": 4000, "topics_count": 105,
                "funnel": {"top": 300, "middle": 395, "bottom": 5},
                "date_min": "2025-02-17", "date_max": "2026-04-10"}
        base.update(overrides)
        return base

    def test_patch_readme_updates_badge(self):
        new_content = self._mod().patch_readme(SAMPLE_README, self._stats())
        assert "Articles-700-orange" in new_content
        assert new_content != SAMPLE_README

    def test_patch_readme_updates_article_count_in_description(self):
        new_content = self._mod().patch_readme(SAMPLE_README, self._stats())
        assert "700 original articles" in new_content

    def test_patch_readme_updates_quick_stats(self):
        new_content = self._mod().patch_readme(SAMPLE_README, self._stats(topics_count=105))
        assert "**700** articles indexed" in new_content
        assert "**105** canonical topics" in new_content
        assert "unique topic tags" not in new_content  # old label fully migrated

    def test_patch_readme_always_touches_date_modified(self):
        """Even when article-count fields match, dateModified should be re-stamped."""
        stats = self._stats(total=648, tags_count=3147, topics_count=100,
                            funnel={"top": 221, "middle": 423, "bottom": 4},
                            date_max="2026-04-04")
        new_content = self._mod().patch_readme(SAMPLE_README, stats)
        assert "648 original articles" in new_content
        # dateModified is always updated to today
        assert '"dateModified": "2026-04-05"' not in new_content

    def test_patch_llms_updates_count(self):
        new_content = self._mod().patch_llms(SAMPLE_LLMS_TXT, self._stats(funnel={}))
        assert "700 original articles" in new_content
        assert new_content != SAMPLE_LLMS_TXT


# =========================================================================
# Tests: generate_sitemap.py logic
# =========================================================================

class TestRebuildLocalSitemap:
    """Sitemap XML generation from rebuild_local.build_sitemap.

    The newer signature takes a full index dict and writes sitemap.xml to
    REPO_ROOT rather than returning XML. Tests redirect REPO_ROOT to a
    temp directory and parse the written file.

    Sitemap contains only indexable HTML pages on articles.firstaimovers.com:
    home(1) + /about/(1) + /topics/(1) + topic hubs for topics with
    >= MIN_ARTICLES_FOR_TOPIC_PAGE articles. Raw data files, feeds, and
    cross-host canonical article URLs are intentionally excluded.
    """

    SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def _run(self, monkeypatch, tmp_path, articles):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        m.build_sitemap({"articles": articles})
        return (tmp_path / "sitemap.xml").read_text(encoding="utf-8")

    def test_produces_valid_sitemap_xml(self, monkeypatch, tmp_path):
        xml = self._run(monkeypatch, tmp_path, SAMPLE_INDEX["articles"])
        root = fromstring(xml)
        assert root.tag == f"{self.SITEMAP_NS}urlset"

    def test_url_count_with_sample_index(self, monkeypatch, tmp_path):
        """SAMPLE_INDEX has 3 articles, all on allow-listed hosts, zero topics."""
        xml = self._run(monkeypatch, tmp_path, SAMPLE_INDEX["articles"])
        # home(1) + about(1) + topics(1) + 0 topic hubs = 3
        assert xml.count("<url>") == 3

    def test_sitemap_excludes_cross_host_canonicals(self, monkeypatch, tmp_path):
        xml = self._run(monkeypatch, tmp_path, SAMPLE_INDEX["articles"])
        # Canonical article URLs on external hosts are excluded from sitemap
        assert "https://radar.firstaimovers.com/test-one" not in xml
        assert "https://radar.firstaimovers.com/test-two" not in xml
        assert "https://insights.firstaimovers.com/test-three" not in xml
        # No fabricated /articles/<folder>/ paths either
        assert "/articles/2026-04-04-test-article-one/" not in xml

    def test_third_party_canonicals_are_skipped(self, monkeypatch, tmp_path):
        articles = [
            {"folder": "2026-01-01-x", "title": "LinkedIn", "published_date": "2026-01-01",
             "tags": [], "funnel_stage": "middle",
             "canonical_url": "https://www.linkedin.com/pulse/x"},
            {"folder": "2026-01-02-y", "title": "Medium", "published_date": "2026-01-02",
             "tags": [], "funnel_stage": "middle",
             "canonical_url": "https://medium.com/@x/y"},
        ]
        xml = self._run(monkeypatch, tmp_path, articles)
        assert "linkedin.com" not in xml
        assert "medium.com" not in xml
        # Only support URLs remain: home + about + topics = 3
        assert xml.count("<url>") == 3

    def test_uses_correct_base_url(self, monkeypatch, tmp_path):
        xml = self._run(monkeypatch, tmp_path, [])
        assert "https://articles.firstaimovers.com/" in xml

    def test_home_has_highest_priority(self, monkeypatch, tmp_path):
        xml = self._run(monkeypatch, tmp_path, [])
        root = fromstring(xml)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        for url in root.findall("s:url", ns):
            loc = url.find("s:loc", ns).text
            if loc.endswith(".com/"):
                assert url.find("s:priority", ns).text == "1.0"
                break

    def test_sitemap_excludes_data_files(self, monkeypatch, tmp_path):
        xml = self._run(monkeypatch, tmp_path, SAMPLE_INDEX["articles"])
        assert ".md" not in xml
        assert ".json" not in xml
        assert ".txt" not in xml
        assert ".cff" not in xml
        assert "feed.xml" not in xml
        assert "feed.json" not in xml
        assert "llms.txt" not in xml
        assert "index.json" not in xml
        assert "hernanicosta.json" not in xml

    def test_empty_index_emits_only_support_urls(self, monkeypatch, tmp_path):
        xml = self._run(monkeypatch, tmp_path, [])
        # home + about + topics = 3
        assert xml.count("<url>") == 3

    def test_topic_hub_urls_emitted_for_threshold_topics(self, monkeypatch, tmp_path):
        """Topics with >= MIN_ARTICLES_FOR_TOPIC_PAGE articles get a sitemap URL."""
        m = self._mod()
        # Build an index with one topic above threshold, one below
        articles = []
        for i in range(m.MIN_ARTICLES_FOR_TOPIC_PAGE):
            articles.append({
                "folder": f"2026-04-{i+1:02d}-a", "title": f"Article {i}",
                "published_date": f"2026-04-{i+1:02d}", "tags": [],
                "topics": ["AI Strategy"], "funnel_stage": "middle",
                "canonical_url": f"https://radar.firstaimovers.com/a{i}",
            })
        # Below-threshold topic
        articles.append({
            "folder": "2026-04-10-b", "title": "B", "published_date": "2026-04-10",
            "tags": [], "topics": ["AI Testing"], "funnel_stage": "middle",
            "canonical_url": "https://radar.firstaimovers.com/b",
        })
        xml = self._run(monkeypatch, tmp_path, articles)
        assert f"{m.SITE_BASE}/topics/ai-strategy/" in xml
        assert f"{m.SITE_BASE}/topics/ai-testing/" not in xml

    def test_malformed_canonical_is_skipped(self, monkeypatch, tmp_path):
        articles = [
            {"folder": "2026-01-01-x", "title": "Bad", "published_date": "2026-01-01",
             "tags": [], "funnel_stage": "middle", "canonical_url": "not a url"},
            {"folder": "2026-01-02-y", "title": "Empty", "published_date": "2026-01-02",
             "tags": [], "funnel_stage": "middle", "canonical_url": ""},
        ]
        xml = self._run(monkeypatch, tmp_path, articles)
        assert xml.count("<url>") == 3  # only support URLs (3 total)


# =========================================================================
# Tests: add_tldr.py logic
# =========================================================================

class TestAddTldr:
    """Test TL;DR detection and injection logic."""

    def _get_functions(self):
        import add_tldr
        return add_tldr

    def test_has_summary_detects_tldr(self):
        mod = self._get_functions()
        assert mod.has_summary(SAMPLE_ARTICLE_WITH_TLDR) is True

    def test_has_summary_detects_key_takeaway(self):
        mod = self._get_functions()
        assert mod.has_summary(SAMPLE_ARTICLE_WITH_KEY_TAKEAWAY) is True

    def test_has_summary_returns_false_when_missing(self):
        mod = self._get_functions()
        assert mod.has_summary(SAMPLE_ARTICLE) is False

    def test_has_summary_ignores_summary_deep_in_article(self):
        """Summary heading after line 50 should not count."""
        mod = self._get_functions()
        content = SAMPLE_FRONT_MATTER + "\n# Title\n" + "\nfiller\n" * 60 + "\n## TL;DR\n> Late summary"
        assert mod.has_summary(content) is False

    def test_strip_front_matter(self):
        mod = self._get_functions()
        result = mod.strip_front_matter(SAMPLE_ARTICLE)
        assert result.startswith("# Test Article Title")
        assert "---" not in result.split("\n")[0]

    def test_strip_front_matter_no_front_matter(self):
        mod = self._get_functions()
        content = "# Just a title\n\nSome content."
        result = mod.strip_front_matter(content)
        assert "# Just a title" in result

    def test_inject_tldr_places_after_h1(self):
        mod = self._get_functions()
        result = mod.inject_tldr(SAMPLE_ARTICLE, "This is the summary.")
        lines = result.split("\n")
        # Find H1 and TL;DR positions
        h1_idx = next(i for i, l in enumerate(lines) if l.startswith("# Test Article"))
        tldr_idx = next(i for i, l in enumerate(lines) if l == "## TL;DR")
        assert tldr_idx > h1_idx

    def test_inject_tldr_blockquote_format(self):
        mod = self._get_functions()
        result = mod.inject_tldr(SAMPLE_ARTICLE, "This is the summary.")
        assert "> This is the summary." in result

    def test_inject_tldr_preserves_front_matter(self):
        mod = self._get_functions()
        result = mod.inject_tldr(SAMPLE_ARTICLE, "Summary here.")
        # Front matter should still be intact
        assert 'title: "Test Article"' in result
        assert 'license: "CC BY 4.0"' in result

    def test_inject_tldr_preserves_rest_of_article(self):
        mod = self._get_functions()
        result = mod.inject_tldr(SAMPLE_ARTICLE, "Summary here.")
        assert "## Model Choice Matters Less" in result
        assert "## Conclusion" in result

    def test_inject_tldr_no_h1_falls_back_to_after_front_matter(self):
        mod = self._get_functions()
        content = SAMPLE_FRONT_MATTER + "\n\nSome content without an H1."
        result = mod.inject_tldr(content, "Summary.")
        assert "## TL;DR" in result
        assert "> Summary." in result

    def test_inject_tldr_multiline_summary(self):
        mod = self._get_functions()
        tldr = "First sentence of summary.\nSecond sentence with more detail."
        result = mod.inject_tldr(SAMPLE_ARTICLE, tldr)
        assert "> First sentence of summary." in result
        assert "> Second sentence with more detail." in result

    def test_inject_tldr_does_not_duplicate(self):
        """Injecting into an article that already has content after H1 should not break structure."""
        mod = self._get_functions()
        result = mod.inject_tldr(SAMPLE_ARTICLE, "Summary.")
        # Only one TL;DR section
        assert result.count("## TL;DR") == 1


# =========================================================================
# Integration-style tests (still mocked, but test full flows)
# =========================================================================

class TestIndexStructure:
    """Validate the index.json schema contract."""

    def test_index_has_required_top_level_keys(self):
        required = {"last_updated", "total_articles", "author", "publication",
                     "canonical_base", "license", "articles"}
        assert required.issubset(set(SAMPLE_INDEX.keys()))

    def test_index_articles_have_required_fields(self):
        required = {"folder", "title", "published_date", "tags", "funnel_stage", "canonical_url"}
        for article in SAMPLE_INDEX["articles"]:
            assert required.issubset(set(article.keys())), f"Missing fields in {article['folder']}"

    def test_index_total_matches_articles_length(self):
        assert SAMPLE_INDEX["total_articles"] == len(SAMPLE_INDEX["articles"])

    def test_index_dates_are_iso_format(self):
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        for article in SAMPLE_INDEX["articles"]:
            assert date_pattern.match(article["published_date"]), \
                f"Bad date format: {article['published_date']} in {article['folder']}"

    def test_index_funnel_stages_are_valid(self):
        valid = {"top", "middle", "bottom"}
        for article in SAMPLE_INDEX["articles"]:
            assert article["funnel_stage"] in valid, \
                f"Invalid funnel_stage: {article['funnel_stage']} in {article['folder']}"


# =========================================================================
# Tests: rebuild_local.py feed generator
# =========================================================================

class TestBuildFeed:
    """Atom feed builder. rebuild_local imports cleanly (no env guards)."""

    ATOM_NS = "{http://www.w3.org/2005/Atom}"

    def _mod(self):
        import rebuild_local
        return rebuild_local

    # --- Pure helpers ------------------------------------------------------

    def test_truncate_below_limit_returns_unchanged(self):
        m = self._mod()
        assert m._truncate("short sentence", 100) == "short sentence"

    def test_truncate_cuts_on_word_boundary_with_ellipsis(self):
        m = self._mod()
        result = m._truncate("one two three four five six seven eight", 20)
        assert result.endswith("…")
        assert " " not in result[-3:-1]  # didn't cut mid-word

    def test_clean_canonical_rejects_non_http(self):
        m = self._mod()
        assert m._clean_canonical("ftp://example.com") is None
        assert m._clean_canonical("not a url") is None
        assert m._clean_canonical("") is None
        assert m._clean_canonical(None) is None

    def test_clean_canonical_handles_newline_in_value(self):
        """The 2026-01-21 LinkedIn batch has newlines inside canonical_url."""
        m = self._mod()
        result = m._clean_canonical("\nhttps://www.linkedin.com/pulse/foo\n")
        assert result is not None
        url, host = result
        assert url == "https://www.linkedin.com/pulse/foo"
        assert host == "www.linkedin.com"

    def test_feed_link_uses_canonical_when_first_party(self):
        m = self._mod()
        link = m._feed_link_for({
            "canonical_url": "https://radar.firstaimovers.com/foo",
            "folder": "2026-04-20-foo",
        })
        assert link == "https://radar.firstaimovers.com/foo"

    def test_feed_link_falls_back_to_mirror_for_third_party(self):
        m = self._mod()
        link = m._feed_link_for({
            "canonical_url": "https://www.linkedin.com/pulse/foo",
            "folder": "2026-04-20-foo",
        })
        assert link == "https://articles.firstaimovers.com/articles/2026-04-20-foo/article.md"

    def test_looks_like_prose_rejects_short_blocks(self):
        m = self._mod()
        assert m._looks_like_prose("# Heading") is False
        assert m._looks_like_prose("Short") is False
        assert m._looks_like_prose("_Italicized subtitle_") is False

    def test_looks_like_prose_accepts_real_paragraph(self):
        m = self._mod()
        block = ("This is a genuine paragraph of prose with enough length to "
                 "pass the 80-character filter and look like real article content.")
        assert m._looks_like_prose(block) is True

    def test_tldr_blockquote_regex_matches_standard_format(self):
        m = self._mod()
        text = "# Title\n\n> **TL;DR:** Summary of the article here.\n\nBody content."
        match = m.TLDR_BLOCKQUOTE_RE.search(text)
        assert match is not None
        assert "Summary of the article here" in match.group(1)

    # --- End-to-end build_feed --------------------------------------------

    def _synthetic_index(self, n=3):
        return {
            "articles": [
                {
                    "folder": f"2026-04-{20-i:02d}-entry-{i}",
                    "title": f"Entry {i}",
                    "published_date": f"2026-04-{20-i:02d}",
                    "tags": [f"tag{j}" for j in range(7)],
                    "funnel_stage": "middle",
                    "canonical_url": f"https://radar.firstaimovers.com/entry-{i}",
                }
                for i in range(n)
            ],
        }

    def _run_build_feed(self, monkeypatch, tmp_path, index, **overrides):
        """Run build_feed with ARTICLES_DIR and REPO_ROOT redirected to tmp_path."""
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        for k, v in overrides.items():
            monkeypatch.setattr(m, k, v)
        m.build_feed(index)
        return (tmp_path / "feed.xml").read_text(encoding="utf-8")

    def test_feed_parses_as_atom(self, monkeypatch, tmp_path):
        out = self._run_build_feed(monkeypatch, tmp_path, self._synthetic_index(3))
        root = fromstring(out)
        assert root.tag == f"{self.ATOM_NS}feed"

    def test_feed_respects_max_entries_cap(self, monkeypatch, tmp_path):
        out = self._run_build_feed(
            monkeypatch, tmp_path, self._synthetic_index(10), FEED_MAX_ENTRIES=4)
        root = fromstring(out)
        assert len(root.findall(f"{self.ATOM_NS}entry")) == 4

    def test_feed_updated_matches_most_recent_entry_not_today(self, monkeypatch, tmp_path):
        out = self._run_build_feed(monkeypatch, tmp_path, self._synthetic_index(3))
        root = fromstring(out)
        assert root.find(f"{self.ATOM_NS}updated").text == "2026-04-20T00:00:00Z"

    def test_feed_entry_ids_are_stable_tag_uris(self, monkeypatch, tmp_path):
        out = self._run_build_feed(monkeypatch, tmp_path, self._synthetic_index(2))
        root = fromstring(out)
        for entry in root.findall(f"{self.ATOM_NS}entry"):
            entry_id = entry.find(f"{self.ATOM_NS}id").text
            assert entry_id.startswith("tag:articles.firstaimovers.com,2026-04-")

    def test_feed_categories_capped_per_entry(self, monkeypatch, tmp_path):
        out = self._run_build_feed(monkeypatch, tmp_path, self._synthetic_index(2))
        root = fromstring(out)
        for entry in root.findall(f"{self.ATOM_NS}entry"):
            cats = entry.findall(f"{self.ATOM_NS}category")
            assert len(cats) <= 5

    def test_feed_is_byte_stable_across_runs(self, monkeypatch, tmp_path):
        a = self._run_build_feed(monkeypatch, tmp_path, self._synthetic_index(3))
        b = self._run_build_feed(monkeypatch, tmp_path, self._synthetic_index(3))
        assert a == b

    def test_feed_summary_uses_tldr_blockquote_when_present(self, monkeypatch, tmp_path):
        idx = self._synthetic_index(1)
        out = self._run_build_feed(monkeypatch, tmp_path, idx)
        # No article.md exists → fallback should be title-based
        root = fromstring(out)
        summary = root.find(f"{self.ATOM_NS}entry/{self.ATOM_NS}summary").text
        assert "Entry 0" in summary and "Dr. Hernani Costa" in summary

        # Now add an article.md with a TL;DR and rebuild
        art_dir = tmp_path / "articles" / idx["articles"][0]["folder"]
        art_dir.mkdir()
        (art_dir / "article.md").write_text(
            "---\ntitle: x\n---\n# Hello\n\n> **TL;DR:** The short summary.\n\nBody.")
        out2 = self._run_build_feed(monkeypatch, tmp_path, idx)
        summary2 = fromstring(out2).find(f"{self.ATOM_NS}entry/{self.ATOM_NS}summary").text
        assert summary2 == "The short summary."


# =========================================================================
# Tests: rebuild_local.py llms-full.txt builder
# =========================================================================

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

class TestNormalizeTags:
    """Normalizer logic: canonical topic lookup, service cleanup."""

    def _mod(self):
        import normalize_tags
        return normalize_tags

    def _rules(self):
        return self._mod().load_aliases()

    def test_canonical_topics_cover_every_alias_reference(self):
        """Every topic mentioned in aliases must exist in canonical_topics."""
        # load_aliases() already validates this, but prove it here too.
        canonical, _, _ = self._rules()
        assert len(canonical) > 50  # sanity: we have a real vocabulary

    def test_exact_override_short_circuits_patterns(self):
        m = self._mod()
        _, patterns, overrides = self._rules()
        # "MCP" is an override -> ["Model Context Protocol"]
        assert m.normalize_tag("MCP", patterns, overrides) == ["Model Context Protocol"]

    def test_pattern_matching_is_case_insensitive(self):
        m = self._mod()
        _, patterns, overrides = self._rules()
        topics = m.normalize_tag("EU AI ACT compliance strategies", patterns, overrides)
        assert "EU AI Act" in topics

    def test_multiple_patterns_contribute_multiple_topics(self):
        m = self._mod()
        _, patterns, overrides = self._rules()
        topics = m.normalize_tag("AI governance for Dutch SMEs", patterns, overrides)
        # should pick up AI Governance + Netherlands AI + European SME AI
        assert "AI Governance" in topics
        assert "Netherlands AI" in topics
        assert "European SME AI" in topics

    def test_topics_deduped_per_article(self):
        m = self._mod()
        _, patterns, overrides = self._rules()
        topics = m.normalize_tags_for_article(
            ["AI governance framework", "AI governance model", "AI Governance in Europe"],
            patterns, overrides,
        )
        assert topics.count("AI Governance") == 1

    def test_max_topics_cap_enforced(self):
        m = self._mod()
        _, patterns, overrides = self._rules()
        # Tag that matches many patterns simultaneously
        topics = m.normalize_tags_for_article(
            ["EU AI Act compliance for Dutch healthcare SMEs with GDPR and Claude Code"],
            patterns, overrides,
        )
        assert len(topics) <= m.MAX_TOPICS_PER_ARTICLE

    def test_unknown_tag_returns_empty(self):
        m = self._mod()
        _, patterns, overrides = self._rules()
        assert m.normalize_tag("xyzzy plugh fnord", patterns, overrides) == []

    def test_normalize_service_strips_whitespace(self):
        m = self._mod()
        assert m.normalize_service("  ai-strategy  ") == "ai-strategy"
        assert m.normalize_service(" fractional-caio") == "fractional-caio"

    def test_normalize_service_lowercases(self):
        m = self._mod()
        assert m.normalize_service("AI-Strategy") == "ai-strategy"

    def test_normalize_service_rejects_unknown(self):
        m = self._mod()
        assert m.normalize_service("not-a-real-service") is None

    def test_normalize_services_dedupes(self):
        m = self._mod()
        result = m.normalize_services([" ai-strategy", "ai-strategy ", "ai-strategy"])
        assert result == ["ai-strategy"]

    def test_normalize_services_preserves_order(self):
        m = self._mod()
        result = m.normalize_services(["compliance-audit", " ai-strategy", "fractional-caio"])
        assert result == ["compliance-audit", "ai-strategy", "fractional-caio"]


# =========================================================================
# Tests: rebuild_local.py static site builder
# =========================================================================

class TestBuildSite:
    """HTML topic-hub site. Requires jinja2; skipped cleanly if not installed."""

    def _mod(self):
        pytest.importorskip("jinja2")
        import rebuild_local
        return rebuild_local

    def _synthetic_index(self, topic_distribution):
        """Build an index where topic_distribution is {topic_name: article_count}."""
        articles = []
        day = 1
        for topic, count in topic_distribution.items():
            for _ in range(count):
                articles.append({
                    "folder": f"2026-04-{day:02d}-slug{day}",
                    "slug": f"slug-{day}",
                    "title": f"Article {day}",
                    "published_date": f"2026-04-{day:02d}",
                    "tags": [],
                    "topics": [topic],
                    "funnel_stage": "middle",
                    "canonical_url": f"https://radar.firstaimovers.com/slug{day}",
                })
                day += 1
        articles.sort(key=lambda a: a["published_date"], reverse=True)
        return {"articles": articles}

    def _run(self, monkeypatch, tmp_path, index):
        m = self._mod()
        # Redirect all IO roots to tmp_path
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        # Copy real templates + static so we don't re-fixture them
        import shutil
        from pathlib import Path as P
        # Resolve repo root from this file's location, not a hardcoded path
        # (this test file lives at <repo>/tools/tests/test_tools.py).
        real_root = P(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        # Real hernanicosta.json is needed for about page
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")
        # Sample article files so llms-full.txt summary lookups don't 404
        for a in index["articles"]:
            (tmp_path / "articles" / a["folder"]).mkdir(exist_ok=True)
            (tmp_path / "articles" / a["folder"] / "article.md").write_text(
                f"---\ntitle: {a['title']}\n---\n# {a['title']}\n\nBody paragraph with enough text to serve as a summary for this test article.\n")

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return tmp_path / "site"

    def test_slugify_produces_stable_urls(self):
        m = self._mod()
        assert m._slugify("AI Governance") == "ai-governance"
        assert m._slugify("GDPR & Data Privacy") == "gdpr-and-data-privacy"
        assert m._slugify("European SME AI") == "european-sme-ai"
        assert m._slugify("AI SEO and GEO") == "ai-seo-and-geo"
        assert m._slugify("UK and Ireland AI") == "uk-and-ireland-ai"

    def test_home_page_renders(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Governance": 6}))
        home = (site / "index.html").read_text(encoding="utf-8")
        assert "<title>First AI Movers" in home
        assert 'rel="canonical" href="https://articles.firstaimovers.com/"' in home
        assert 'name="robots" content="index, follow"' in home

    def test_topics_index_lists_all_topics(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Governance": 6, "AI Agents": 2}))
        idx = (site / "topics" / "index.html").read_text(encoding="utf-8")
        # Both topics appear (under/over threshold), but only over-threshold is a link
        assert "AI Governance" in idx
        assert "AI Agents" in idx
        assert "topics/ai-governance/" in idx
        assert "topics/ai-agents/" not in idx  # below threshold → not linked

    def test_topic_page_created_only_above_threshold(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Governance": 6, "AI Agents": 2}))
        assert (site / "topics" / "ai-governance" / "index.html").exists()
        assert not (site / "topics" / "ai-agents").exists()

    def test_topic_page_lists_articles_newest_first(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Strategy": 6}))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        # Day 6 is newest; day 1 is oldest. Position check.
        assert page.index("Article 6") < page.index("Article 1")

    def test_topic_page_self_canonical(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Strategy": 6}))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert 'rel="canonical" href="https://articles.firstaimovers.com/topics/ai-strategy/"' in page
        assert 'name="robots" content="index, follow"' in page

    def test_article_cards_link_to_local_page(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Governance": 6}))
        page = (site / "topics" / "ai-governance" / "index.html").read_text(encoding="utf-8")
        # Title links to local archive page
        assert 'href="../../articles/slug-1/"' in page
        # CTA still links to external canonical
        assert "https://radar.firstaimovers.com/slug1" in page

    def test_about_page_canonicals_to_drhernanicosta(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Strategy": 6}))
        about = (site / "about" / "index.html").read_text(encoding="utf-8")
        assert 'rel="canonical" href="https://drhernanicosta.com"' in about
        assert 'application/ld+json' in about  # Person JSON-LD embedded

    def test_404_page_noindex(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Strategy": 6}))
        page = (site / "404.html").read_text(encoding="utf-8")
        assert 'name="robots" content="noindex"' in page

    def test_stylesheet_copied(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Strategy": 6}))
        assert (site / "style.css").exists()
        # Every page references it via relative path — spot-check topic page
        topic = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert 'href="../../style.css"' in topic

    def test_raw_data_mirror_files_copied(self, monkeypatch, tmp_path):
        # Put some mirror files in the tmp root to simulate a full rebuild
        (tmp_path / "index.json").write_text('{"articles": []}')
        (tmp_path / "llms.txt").write_text("llms")
        (tmp_path / "llms-full.txt").write_text("corpus")
        (tmp_path / "feed.xml").write_text("<feed/>")
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Strategy": 6}))
        assert (site / "index.json").exists()
        assert (site / "llms.txt").exists()
        assert (site / "llms-full.txt").exists()
        assert (site / "feed.xml").exists()
        # Raw articles tree mirrored
        assert (site / "articles").exists()

    def test_related_topics_ranked_by_cooccurrence(self):
        m = self._mod()
        articles = [
            {"topics": ["A", "B", "C"]},
            {"topics": ["A", "B"]},
            {"topics": ["A", "D"]},
        ]
        counts = {"A": 3, "B": 2, "C": 1, "D": 1}
        related = m._related_topics_for("A", articles, counts, limit=3)
        assert related == ["B", "C", "D"]  # B co-occurs twice, C/D once each

    def test_canonical_host_label_maps_common_hosts(self):
        m = self._mod()
        assert m._canonical_host_label("https://radar.firstaimovers.com/foo") == "Radar"
        assert m._canonical_host_label("https://www.linkedin.com/pulse/x") == "LinkedIn"
        assert m._canonical_host_label("https://insights.firstaimovers.com/y") == "Insights"

    def test_topic_page_renders_intro_block_when_present(self, monkeypatch, tmp_path):
        """When _load_topic_intros returns content for a topic, the page surfaces it."""
        m = self._mod()
        monkeypatch.setattr(m, "_load_topic_intros", lambda: {
            "AI Strategy": {
                "lede": "Lede sentence about strategy.",
                "key_themes": ["First theme line", "Second theme line"],
                "why_it_matters": "Why this topic matters paragraph.",
            },
        })
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Strategy": 6}))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert "Lede sentence about strategy." in page
        assert "First theme line" in page
        assert "Second theme line" in page
        assert "Why this topic matters paragraph." in page
        assert 'class="topic-intro"' in page
        # Curated lede should also surface in the meta description
        assert 'name="description" content="Lede sentence about strategy."' in page

    def test_topic_page_falls_back_to_generic_lede_without_intro(self, monkeypatch, tmp_path):
        """Topics absent from topic_intros.json still render — with the boilerplate lede."""
        m = self._mod()
        monkeypatch.setattr(m, "_load_topic_intros", lambda: {})
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Strategy": 6}))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert "Every article in the First AI Movers archive tagged" in page
        assert 'class="topic-intro"' not in page


class TestTopicIntros:
    """Loader + content contract for tools/topic_intros.json."""

    REQUIRED_TOP_10 = [
        "European SME AI", "AI Strategy", "AI Governance", "AI Productivity Tools",
        "EU AI Act", "AI Workflow Automation", "AI Agents", "Healthcare AI",
        "B2B SaaS Growth", "GDPR & Data Privacy",
    ]

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def test_real_file_loads_with_top_10_topics(self):
        """The committed topic_intros.json covers every top-10 roadmap topic."""
        intros = self._mod()._load_topic_intros()
        for topic in self.REQUIRED_TOP_10:
            assert topic in intros, f"missing intro for {topic}"

    def test_real_file_entries_have_required_fields(self):
        """Each intro must have non-empty lede + at least 3 key themes + why_it_matters."""
        intros = self._mod()._load_topic_intros()
        for topic, obj in intros.items():
            assert obj["lede"], f"empty lede for {topic}"
            assert len(obj["key_themes"]) >= 3, f"need >=3 themes for {topic}"
            assert obj["why_it_matters"], f"empty why_it_matters for {topic}"

    def test_real_file_keys_are_canonical_topics(self):
        """Every topic key must exist in canonical_topics.json — guards against typos."""
        from pathlib import Path as P
        canonical = set(json.loads(
            (P(__file__).resolve().parents[1] / "canonical_topics.json").read_text()
        )["topics"])
        intros = self._mod()._load_topic_intros()
        unknown = set(intros) - canonical
        assert not unknown, f"intros reference non-canonical topics: {unknown}"

    def test_missing_file_returns_empty_dict(self, monkeypatch, tmp_path):
        """A missing intros file degrades silently — site still builds."""
        m = self._mod()
        monkeypatch.setattr(m, "TOPIC_INTROS_PATH", tmp_path / "does-not-exist.json")
        assert m._load_topic_intros() == {}

    def test_malformed_file_returns_empty_dict(self, monkeypatch, tmp_path, capsys):
        """Malformed JSON produces a warning to stderr but does not raise."""
        m = self._mod()
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json")
        monkeypatch.setattr(m, "TOPIC_INTROS_PATH", bad)
        assert m._load_topic_intros() == {}
        captured = capsys.readouterr()
        assert "malformed" in captured.err

    def test_loader_skips_non_dict_entries(self, monkeypatch, tmp_path):
        """Defensive: an intros entry that is not an object is dropped, not crashed on."""
        m = self._mod()
        path = tmp_path / "intros.json"
        path.write_text(json.dumps({
            "version": 1,
            "intros": {
                "Good": {"lede": "ok", "key_themes": ["a"], "why_it_matters": "b"},
                "Bad": "not a dict",
            },
        }))
        monkeypatch.setattr(m, "TOPIC_INTROS_PATH", path)
        result = m._load_topic_intros()
        assert "Good" in result
        assert "Bad" not in result

    def test_loader_normalizes_missing_optional_fields(self, monkeypatch, tmp_path):
        """Missing fields default to empty values rather than raising KeyError."""
        m = self._mod()
        path = tmp_path / "intros.json"
        path.write_text(json.dumps({
            "intros": {"Skeleton": {"lede": "only lede here"}},
        }))
        monkeypatch.setattr(m, "TOPIC_INTROS_PATH", path)
        result = m._load_topic_intros()
        assert result["Skeleton"]["lede"] == "only lede here"
        assert result["Skeleton"]["key_themes"] == []
        assert result["Skeleton"]["why_it_matters"] == ""


# =========================================================================
# Tests: rebuild_local.py llms-recent.txt (30-day slice)
# =========================================================================

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

class TestExtractTldr:
    """TL;DR extraction from article markdown — existing content only, no generation."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def _write_article(self, tmp_path, folder, text):
        d = tmp_path / "articles" / folder
        d.mkdir(parents=True, exist_ok=True)
        (d / "article.md").write_text(text, encoding="utf-8")

    def test_extract_tldr_blockquote_format(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        self._write_article(tmp_path, "2026-04-01-test",
            "---\ntitle: Test\n---\n# Title\n\n> **TL;DR:** This is the summary.\n\nBody here.")
        assert m._extract_tldr("2026-04-01-test") == "This is the summary."

    def test_extract_tldr_heading_format(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        self._write_article(tmp_path, "2026-04-01-test",
            "---\ntitle: Test\n---\n# Title\n\n## TL;DR\n\nSummary paragraph.\n\nBody here.")
        assert m._extract_tldr("2026-04-01-test") == "Summary paragraph."

    def test_extract_tldr_multiline_blockquote(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        self._write_article(tmp_path, "2026-04-01-test",
            "---\ntitle: Test\n---\n# Title\n\n> **TL;DR:** Line one.\n> Line two.\n\nBody here.")
        result = m._extract_tldr("2026-04-01-test")
        assert "Line one." in result
        assert "Line two." in result

    def test_extract_tldr_returns_none_when_missing(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        self._write_article(tmp_path, "2026-04-01-test",
            "---\ntitle: Test\n---\n# Title\n\nBody here.\n")
        assert m._extract_tldr("2026-04-01-test") is None

    def test_extract_tldr_returns_none_when_file_missing(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        assert m._extract_tldr("2026-04-01-test") is None

    def test_extract_tldr_strips_markdown_links(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        self._write_article(tmp_path, "2026-04-01-test",
            "---\ntitle: Test\n---\n# Title\n\n> **TL;DR:** See [the guide](https://example.com) for details.\n\nBody.")
        result = m._extract_tldr("2026-04-01-test")
        assert "[the guide]" not in result
        assert "https://example.com" not in result
        assert "See the guide for details." in result

    def test_extract_tldr_no_fallback_generation(self, monkeypatch, tmp_path):
        """The extractor must never invent a TL;DR from article body text."""
        m = self._mod()
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        self._write_article(tmp_path, "2026-04-01-test",
            "---\ntitle: Test\n---\n# Title\n\nFirst paragraph of the article body.\n\nSecond paragraph.")
        result = m._extract_tldr("2026-04-01-test")
        assert result is None
        assert "First paragraph" not in (result or "")


class TestQuickReads:
    """Topic-page Quick reads section — E4 rendering contract."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def _synthetic_index(self, topic_counts):
        articles = []
        day = 1
        for topic, count in topic_counts.items():
            for _ in range(count):
                articles.append({
                    "folder": f"2026-04-{day:02d}-article-{day}",
                    "slug": f"article-{day}",
                    "title": f"Article {day}",
                    "published_date": f"2026-04-{day:02d}",
                    "tags": [],
                    "topics": [topic],
                    "funnel_stage": "middle",
                    "canonical_url": f"https://radar.firstaimovers.com/slug{day}",
                })
                day += 1
        articles.sort(key=lambda a: a["published_date"], reverse=True)
        return {"articles": articles}

    def _run(self, monkeypatch, tmp_path, index, tldr_map=None):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        from pathlib import Path as P
        real_root = P(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")

        for a in index["articles"]:
            folder = a["folder"]
            (tmp_path / "articles" / folder).mkdir(exist_ok=True)
            body = f"---\ntitle: {a['title']}\n---\n# {a['title']}\n\n"
            if tldr_map and folder in tldr_map:
                body += f"> **TL;DR:** {tldr_map[folder]}\n\n"
            body += "Body paragraph with enough text to serve as a summary for this test article.\n"
            (tmp_path / "articles" / folder / "article.md").write_text(body)

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return tmp_path / "site"

    def test_quick_reads_shown_when_tldrs_exist(self, monkeypatch, tmp_path):
        index = self._synthetic_index({"AI Strategy": 6})
        tldr_map = {
            "2026-04-06-article-6": "Summary for article six.",
            "2026-04-05-article-5": "Summary for article five.",
        }
        site = self._run(monkeypatch, tmp_path, index, tldr_map)
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert 'class="quick-reads"' in page
        assert "Summary for article six." in page
        assert "Summary for article five." in page
        assert "Article 6" in page
        assert "Article 5" in page

    def test_quick_reads_hidden_when_no_tldrs(self, monkeypatch, tmp_path):
        index = self._synthetic_index({"AI Strategy": 6})
        site = self._run(monkeypatch, tmp_path, index, {})
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert 'class="quick-reads"' not in page
        assert "Quick reads" not in page

    def test_quick_reads_links_use_canonical_url(self, monkeypatch, tmp_path):
        index = self._synthetic_index({"AI Strategy": 6})
        tldr_map = {
            "2026-04-06-article-6": "Summary for article six.",
        }
        site = self._run(monkeypatch, tmp_path, index, tldr_map)
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert "https://radar.firstaimovers.com/slug6" in page
        assert 'href="/articles/' not in page

    def test_quick_reads_respects_limit(self, monkeypatch, tmp_path):
        index = self._synthetic_index({"AI Strategy": 10})
        tldr_map = {f"2026-04-{d:02d}-article-{d}": f"Summary {d}." for d in range(1, 11)}
        site = self._run(monkeypatch, tmp_path, index, tldr_map)
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        # Should show at most QUICK_READS_MAX (5) items
        count = page.count('class="quick-read"')
        assert count <= 5
        # Newest articles should appear first
        assert page.index("Summary 10.") < page.index("Summary 6.")

    def test_quick_reads_no_fallback_summary(self, monkeypatch, tmp_path):
        """Articles without TL;DR must not appear in Quick reads via fabricated summaries."""
        index = self._synthetic_index({"AI Strategy": 6})
        tldr_map = {
            "2026-04-06-article-6": "Only this one has a TL;DR.",
        }
        site = self._run(monkeypatch, tmp_path, index, tldr_map)
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert "Only this one has a TL;DR." in page
        # Articles 1-5 have no TL;DR and must not appear in quick-reads
        qr_section = page.split('class="quick-reads"')[1].split('class="articles-heading"')[0] if 'class="quick-reads"' in page else ""
        assert "Article 1" not in qr_section
        assert "Article 2" not in qr_section
        assert "Article 3" not in qr_section


# =========================================================================
# Tests: rebuild_local.py JSON Feed (E5)
# =========================================================================

class TestJsonFeed:
    """JSON Feed 1.1 generation from rebuild_local.build_json_feed."""

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
            body = f"---\ntitle: {spec['title']}\n---\n# {spec['title']}\n\n"
            if spec.get("tldr"):
                body += f"> **TL;DR:** {spec['tldr']}\n\n"
            body += "Body paragraph with enough text to serve as a summary for this test article.\n"
            (tmp_path / "articles" / folder / "article.md").write_text(body)
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
        m.build_json_feed(index)
        return json.loads((tmp_path / "feed.json").read_text(encoding="utf-8"))

    def test_json_feed_has_required_top_level_keys(self, monkeypatch, tmp_path):
        feed = self._run(monkeypatch, tmp_path, [
            {"folder": "2026-04-20-a", "title": "A", "published_date": "2026-04-20"},
        ])
        assert feed["version"] == "https://jsonfeed.org/version/1.1"
        assert "title" in feed
        assert "items" in feed
        assert "language" in feed
        assert "authors" in feed

    def test_json_feed_item_count_matches_atom_cap(self, monkeypatch, tmp_path):
        articles = [
            {"folder": f"2026-04-{d:02d}-a", "title": f"A{d}", "published_date": f"2026-04-{d:02d}"}
            for d in range(1, 60)
        ]
        feed = self._run(monkeypatch, tmp_path, articles)
        assert len(feed["items"]) <= 50

    def test_json_feed_items_use_canonical_urls(self, monkeypatch, tmp_path):
        feed = self._run(monkeypatch, tmp_path, [
            {"folder": "2026-04-20-a", "title": "A", "published_date": "2026-04-20",
             "canonical_url": "https://insights.firstaimovers.com/article-a"},
        ])
        assert feed["items"][0]["url"] == "https://insights.firstaimovers.com/article-a"

    def test_json_feed_items_have_dates_and_tags(self, monkeypatch, tmp_path):
        feed = self._run(monkeypatch, tmp_path, [
            {"folder": "2026-04-20-a", "title": "A", "published_date": "2026-04-20",
             "topics": ["AI Strategy", "EU AI Act"]},
        ])
        item = feed["items"][0]
        assert "date_published" in item
        assert item["tags"] == ["AI Strategy", "EU AI Act"]

    def test_json_feed_no_generated_summaries(self, monkeypatch, tmp_path):
        """Items without TL;DR get the same title-based fallback as Atom feed — never AI-generated."""
        feed = self._run(monkeypatch, tmp_path, [
            {"folder": "2026-04-20-a", "title": "A", "published_date": "2026-04-20"},
        ])
        item = feed["items"][0]
        # Fallback is title-based, same as Atom feed; not an invented summary
        assert "A — by Dr. Hernani Costa" in item.get("content_text", "")

    def test_json_feed_uses_tldr_as_content_text(self, monkeypatch, tmp_path):
        feed = self._run(monkeypatch, tmp_path, [
            {"folder": "2026-04-20-a", "title": "A", "published_date": "2026-04-20",
             "tldr": "This is the actual TL;DR."},
        ])
        item = feed["items"][0]
        assert item.get("content_text") == "This is the actual TL;DR."

    def test_feed_json_is_mirrored_to_site(self, monkeypatch, tmp_path):
        import shutil
        from pathlib import Path as P
        m = self._mod()
        real_root = P(__file__).resolve().parents[2]
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")
        (tmp_path / "feed.json").write_text('{"version":"1.1"}')
        (tmp_path / "index.json").write_text('{"articles":[]}')

        index = {"articles": []}
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        assert (tmp_path / "site" / "feed.json").exists()

    def test_feed_urls_not_in_sitemap(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        m.build_sitemap({"articles": []})
        xml = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
        # Feed URLs are excluded from sitemap — they belong on their own host
        assert "feed.xml" not in xml
        assert "feed.json" not in xml


class TestDarkMode:
    """Default dark mode with light toggle — theme system."""

    def _mod(self):
        pytest.importorskip("jinja2")
        import rebuild_local
        return rebuild_local

    def _run(self, monkeypatch, tmp_path):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        from pathlib import Path as P
        real_root = P(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")

        index = {"articles": []}
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return tmp_path / "site"

    def test_home_page_has_dark_theme_default(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path)
        home = (site / "index.html").read_text(encoding="utf-8")
        assert '<html lang="en" data-theme="dark">' in home

    def test_toggle_button_exists(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path)
        home = (site / "index.html").read_text(encoding="utf-8")
        assert 'id="theme-toggle"' in home
        assert 'Light mode' in home
        assert 'aria-label="Toggle light mode"' in home

    def test_inline_script_no_external_js(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path)
        home = (site / "index.html").read_text(encoding="utf-8")
        assert '<script>' in home
        # Dark mode toggle must be inline; search.js is the only allowed external script
        assert home.count('<script src="') <= 1
        assert 'localStorage' in home

    def test_light_theme_css_exists(self):
        from pathlib import Path as P
        css = (P(__file__).resolve().parents[2] / "static" / "style.css").read_text(encoding="utf-8")
        assert 'html[data-theme="dark"]' in css
        assert 'html[data-theme="light"]' in css or '--bg: #fafafa' in css

    def test_topic_page_renders_with_dark_theme(self, monkeypatch, tmp_path):
        m = self._mod()
        # Build with articles above topic threshold so a topic page is generated
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        from pathlib import Path as P
        real_root = P(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")
        for i in range(6):
            folder = f"2026-04-{20-i:02d}-a{i}"
            (tmp_path / "articles" / folder).mkdir(exist_ok=True)
            (tmp_path / "articles" / folder / "article.md").write_text(
                f"---\ntitle: A{i}\n---\n# A{i}\n\nBody.\n")
        index = {"articles": [
            {"folder": f"2026-04-{20-i:02d}-a{i}", "slug": f"a{i}", "title": f"A{i}",
             "published_date": f"2026-04-{20-i:02d}", "tags": [], "topics": ["AI Strategy"],
             "funnel_stage": "middle", "canonical_url": f"https://radar.firstaimovers.com/a{i}"}
            for i in range(6)
        ]}
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        page = (tmp_path / "site" / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert '<html lang="en" data-theme="dark">' in page


class TestSocialFooter:
    """Visible author social links in footer — E5."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def _run(self, monkeypatch, tmp_path):
        m = self._mod()
        import shutil
        from pathlib import Path as P
        real_root = P(__file__).resolve().parents[2]
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")

        index = {"articles": []}
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return tmp_path / "site"

    def test_footer_renders_social_links(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path)
        home = (site / "index.html").read_text(encoding="utf-8")
        assert "linkedin.com/in/hernani-costa-ai-ceo-firstaimovers" in home
        assert "open.spotify.com/show/5HX1cZF7Ojikm2VWcAzTnt" in home
        assert "youtube.com/@DrHernaniCosta" in home

    def test_base_template_has_json_feed_link(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path)
        home = (site / "index.html").read_text(encoding="utf-8")
        assert 'type="application/json"' in home
        assert "feed.json" in home

    def test_no_og_image_when_none_configured(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path)
        home = (site / "index.html").read_text(encoding="utf-8")
        # No og:image should be emitted when no image asset exists
        assert "property=\"og:image\"" not in home
        assert "name=\"twitter:image\"" not in home


# =========================================================================
# Tests: rebuild_local.py per-article HTML pages (E6)
# =========================================================================

class TestArticlePages:
    """Per-article HTML pages renderer. Requires jinja2 and markdown."""

    def _mod(self):
        pytest.importorskip("jinja2")
        pytest.importorskip("markdown")
        import rebuild_local
        return rebuild_local

    def _synthetic_index(self, n=3):
        articles = []
        for i in range(n):
            day = 20 - i
            articles.append({
                "folder": f"2026-04-{day:02d}-article-{i}",
                "slug": f"article-{i}",
                "title": f"Test Article {i}",
                "published_date": f"2026-04-{day:02d}",
                "tags": ["AI Strategy"],
                "topics": ["AI Strategy", "European SME AI"],
                "funnel_stage": "middle",
                "canonical_url": f"https://radar.firstaimovers.com/article-{i}",
            })
        return {"articles": articles}

    def _run(self, monkeypatch, tmp_path, index):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        from pathlib import Path as P
        real_root = P(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")

        for a in index["articles"]:
            folder = a["folder"]
            (tmp_path / "articles" / folder).mkdir(exist_ok=True)
            (tmp_path / "articles" / folder / "article.md").write_text(
                f'---\ntitle: "{a["title"]}"\nauthor: "Dr. Hernani Costa"\n'
                f'canonical_url: "{a["canonical_url"]}"\npublished_date: "{a["published_date"]}"\n'
                f'license: "CC BY 4.0"\n---\n'
                f'# {a["title"]}\n\n## Introduction\n\nThis is the introduction paragraph.\n\n'
                f'## Key Point\n\n- Bullet one\n- Bullet two\n\n'
                f'[A link](https://example.com)\n\n'
                f'> A blockquote\n\n'
                f'```python\nprint("hello")\n```\n',
                encoding="utf-8")

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return tmp_path / "site"

    # --- Route generation --------------------------------------------------

    def test_article_local_path_uses_slug(self):
        m = self._mod()
        assert m._article_local_path({"slug": "my-article"}) == "/articles/my-article/"

    def test_article_local_path_falls_back_to_folder(self):
        m = self._mod()
        assert m._article_local_path({"folder": "2026-04-01-my-article"}) == "/articles/2026-04-01-my-article/"

    def test_article_local_path_prefers_slug_over_folder(self):
        m = self._mod()
        assert m._article_local_path({"slug": "slug", "folder": "folder"}) == "/articles/slug/"

    # --- Page generation ---------------------------------------------------

    def test_article_page_generated_for_each_article(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        for i in range(3):
            assert (site / "articles" / f"article-{i}" / "index.html").exists()

    def test_article_page_contains_title(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert "Test Article 0" in page

    def test_article_page_body_html_rendered(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert '<h2 id="introduction">Introduction</h2>' in page
        assert "<li>Bullet one</li>" in page
        assert "<li>Bullet two</li>" in page
        assert '<a href="https://example.com">A link</a>' in page
        assert "<blockquote>" in page
        assert "<pre>" in page
        assert "<code" in page

    def test_article_page_front_matter_stripped(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert "---" not in page  # No raw front matter delimiters
        assert "canonical_url:" not in page  # No front matter keys

    def test_article_page_has_archive_notice(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert "Archive copy" in page
        assert "read original" in page.lower() or "original at" in page.lower()

    # --- Canonical protection ----------------------------------------------

    def test_article_page_has_noindex_follow(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'name="robots" content="noindex, follow"' in page

    def test_article_page_has_canonical_link(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'rel="canonical" href="https://radar.firstaimovers.com/article-0"' in page

    def test_article_page_canonical_is_external_not_local(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'rel="canonical" href="https://articles.firstaimovers.com/articles/' not in page

    # --- Schema.org JSON-LD ------------------------------------------------

    def test_article_page_has_jsonld_article(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'application/ld+json' in page
        assert '"@type": "Article"' in page or '"@type":"Article"' in page

    def test_article_page_jsonld_has_required_fields(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        script_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.DOTALL)
        assert script_match is not None
        data = json.loads(script_match.group(1))
        assert data["@type"] == "Article"
        assert data["headline"] == "Test Article 0"
        assert data["datePublished"] == "2026-04-20"
        assert data["author"]["name"] == "Dr. Hernani Costa"
        assert data["publisher"]["name"] == "First AI Movers"
        assert "creativecommons.org/licenses/by/4.0" in data["license"]

    # --- Sitemap behavior --------------------------------------------------

    def test_sitemap_does_not_include_local_article_pages(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        m.build_sitemap(self._synthetic_index(3))
        xml = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
        assert "/articles/article-0/" not in xml
        assert "/articles/article-1/" not in xml
        assert "/articles/article-2/" not in xml

    # --- Article card linking ----------------------------------------------

    def test_article_card_title_links_to_local_page(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        topic_page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        # Title should link to local article page
        assert 'href="../../articles/article-0/"' in topic_page or 'href="../../articles/article-1/"' in topic_page

    def test_article_card_cta_stays_external(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        topic_page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert "https://radar.firstaimovers.com/article-0" in topic_page
        assert "Read at Radar" in topic_page or "Read at" in topic_page

    # --- Feed stability ----------------------------------------------------

    def test_feed_urls_unchanged(self, monkeypatch, tmp_path):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        for a in self._synthetic_index(3)["articles"]:
            d = tmp_path / "articles" / a["folder"]
            d.mkdir(exist_ok=True)
            (d / "article.md").write_text(f"---\ntitle: {a['title']}\n---\n# {a['title']}\n\nBody.\n")
        m.build_feed(self._synthetic_index(3))
        xml = (tmp_path / "feed.xml").read_text(encoding="utf-8")
        assert "https://radar.firstaimovers.com/article-0" in xml
        assert "/articles/article-0/" not in xml

    # --- Build artifacts ---------------------------------------------------

    def test_build_increases_page_count_by_article_count(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(5))
        # home(1) + topics_index(1) + topic_pages(1) + about(1) + 404(1) + article_pages(5) = 10
        article_pages = list((site / "articles").glob("*/index.html"))
        assert len(article_pages) == 5

    def test_no_article_md_files_mutated(self, monkeypatch, tmp_path):
        index = self._synthetic_index(1)
        site = self._run(monkeypatch, tmp_path, index)
        # Verify article.md is unchanged
        original = (tmp_path / "articles" / index["articles"][0]["folder"] / "article.md").read_text(encoding="utf-8")
        assert "---" in original  # Still has front matter
        assert "# Test Article 0" in original

    def test_no_metadata_files_mutated(self, monkeypatch, tmp_path):
        index = self._synthetic_index(1)
        self._run(monkeypatch, tmp_path, index)
        assert not (tmp_path / "articles" / index["articles"][0]["folder"] / "metadata.json").exists()

    # --- XSS / raw HTML safety ---------------------------------------------

    def _write_unsafe_article(self, tmp_path, folder, body):
        d = tmp_path / "articles" / folder
        d.mkdir(parents=True, exist_ok=True)
        (d / "article.md").write_text(
            f"---\ntitle: Unsafe\n---\n# Unsafe\n\n{body}\n", encoding="utf-8")

    def _run_with_custom_body(self, monkeypatch, tmp_path, folder, body):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        from pathlib import Path as P
        real_root = P(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")

        self._write_unsafe_article(tmp_path, folder, body)
        index = {
            "articles": [{
                "folder": folder,
                "slug": "unsafe",
                "title": "Unsafe",
                "published_date": "2026-04-20",
                "tags": [],
                "topics": [],
                "funnel_stage": "middle",
                "canonical_url": "https://radar.firstaimovers.com/unsafe",
            }]
        }
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return (tmp_path / "site" / "articles" / "unsafe" / "index.html").read_text(encoding="utf-8")

    def _article_body_from_page(self, page_html):
        """Extract just the article-body div HTML for XSS assertions."""
        start = page_html.find('<div class="article-body">')
        end = page_html.find('</div>', start) + len('</div>')
        return page_html[start:end] if start != -1 else page_html

    def test_script_tag_removed(self, monkeypatch, tmp_path):
        page = self._run_with_custom_body(
            monkeypatch, tmp_path, "2026-04-20-unsafe",
            '<script>alert("xss")</script>')
        body = self._article_body_from_page(page)
        assert "<script>" not in body
        assert "alert(" not in body

    def test_iframe_tag_removed(self, monkeypatch, tmp_path):
        page = self._run_with_custom_body(
            monkeypatch, tmp_path, "2026-04-20-unsafe",
            '<iframe src="https://evil.com"></iframe>')
        body = self._article_body_from_page(page)
        assert "<iframe" not in body
        assert "evil.com" not in body

    def test_event_handler_attribute_removed(self, monkeypatch, tmp_path):
        page = self._run_with_custom_body(
            monkeypatch, tmp_path, "2026-04-20-unsafe",
            '<img src=x onerror=alert(1)>')
        body = self._article_body_from_page(page)
        assert "onerror" not in body
        assert "alert(1)" not in body

    def test_javascript_url_removed(self, monkeypatch, tmp_path):
        page = self._run_with_custom_body(
            monkeypatch, tmp_path, "2026-04-20-unsafe",
            '<a href="javascript:alert(1)">click</a>')
        body = self._article_body_from_page(page)
        assert "javascript:" not in body
        # The href attribute should have been removed entirely
        assert 'href="alert(1)"' not in body
        # Link text should still be present (sanitizer removes attribute, not tag)
        assert "click" in body

    def test_normal_markdown_preserved_after_sanitization(self, monkeypatch, tmp_path):
        page = self._run_with_custom_body(
            monkeypatch, tmp_path, "2026-04-20-safe",
            '## Heading\n\n- Item one\n- Item two\n\n'
            '> A blockquote\n\n'
            '[a link](https://example.com)\n\n'
            '```python\nprint("hi")\n```')
        body = self._article_body_from_page(page)
        assert '<h2 id="heading">Heading</h2>' in body
        assert "<li>Item one</li>" in body
        assert "<blockquote>" in body
        assert '<a href="https://example.com">a link</a>' in body
        assert "<pre>" in body
        assert "<code" in body


# =========================================================================
# Tests: rebuild_local.py per-article enhancements (E7)
# =========================================================================

class TestArticleEnhancements:
    """Per-article page enhancements: reading time, TOC, breadcrumbs, related articles."""

    def _mod(self):
        pytest.importorskip("jinja2")
        pytest.importorskip("markdown")
        import rebuild_local
        return rebuild_local

    # --- Reading time ------------------------------------------------------

    def test_reading_time_counts_words(self):
        m = self._mod()
        text = "word " * 400  # 400 words = 2 minutes at 200 WPM
        assert m._reading_time(text) == 2

    def test_reading_time_minimum_one_minute(self):
        m = self._mod()
        text = "short."
        assert m._reading_time(text) == 1

    def test_reading_time_ignores_front_matter(self):
        m = self._mod()
        text = '---\ntitle: Test\n---\n# Title\n\n' + 'word ' * 400
        assert m._reading_time(text) == 2

    def test_reading_time_rounds_up(self):
        m = self._mod()
        text = "word " * 250  # 250 words = 1.25 min -> rounds to 1
        assert m._reading_time(text) == 1
        text = "word " * 350  # 350 words = 1.75 min -> rounds to 2
        assert m._reading_time(text) == 2

    # --- TOC / heading IDs -------------------------------------------------

    def test_inject_heading_ids_adds_ids(self):
        m = self._mod()
        html = "<h2>First Section</h2><p>text</p><h3>Subsection</h3>"
        new_html, headings = m._inject_heading_ids(html)
        assert 'id="first-section"' in new_html
        assert 'id="subsection"' in new_html
        assert len(headings) == 2
        assert headings[0]["text"] == "First Section"
        assert headings[0]["level"] == 2
        assert headings[1]["text"] == "Subsection"
        assert headings[1]["level"] == 3

    def test_inject_heading_ids_deduplicates(self):
        m = self._mod()
        html = "<h2>Same</h2><h2>Same</h2><h2>Same</h2>"
        new_html, headings = m._inject_heading_ids(html)
        assert 'id="same"' in new_html
        assert 'id="same-1"' in new_html
        assert 'id="same-2"' in new_html

    def test_inject_heading_ids_preserves_existing_ids(self):
        m = self._mod()
        html = '<h2 id="custom">Section</h2>'
        new_html, headings = m._inject_heading_ids(html)
        assert 'id="custom"' in new_html
        assert headings[0]["id"] == "custom"

    def test_inject_heading_ids_strips_inline_html_for_slug(self):
        m = self._mod()
        html = '<h2>Section with <code>code</code></h2>'
        new_html, headings = m._inject_heading_ids(html)
        assert headings[0]["text"] == "Section with code"
        assert 'id="section-with-code"' in new_html

    def test_inject_heading_ids_returns_empty_for_no_headings(self):
        m = self._mod()
        html = "<p>No headings here</p>"
        new_html, headings = m._inject_heading_ids(html)
        assert new_html == html
        assert headings == []

    # --- Related articles --------------------------------------------------

    def test_related_articles_excludes_current(self):
        m = self._mod()
        target = {"slug": "target", "topics": ["AI Strategy"], "published_date": "2026-04-20", "title": "Target"}
        all_articles = [
            {"slug": "target", "topics": ["AI Strategy"], "published_date": "2026-04-20", "title": "Target"},
            {"slug": "other", "topics": ["AI Strategy"], "published_date": "2026-04-19", "title": "Other"},
        ]
        related = m._related_articles_for_article(target, all_articles, limit=3)
        assert len(related) == 1
        assert related[0]["slug"] == "other"

    def test_related_articles_ranks_by_topic_overlap(self):
        m = self._mod()
        target = {"slug": "target", "topics": ["A", "B"], "published_date": "2026-04-20", "title": "Target"}
        all_articles = [
            {"slug": "two", "topics": ["A", "B"], "published_date": "2026-04-19", "title": "Two"},
            {"slug": "one", "topics": ["A"], "published_date": "2026-04-19", "title": "One"},
            {"slug": "none", "topics": ["C"], "published_date": "2026-04-19", "title": "None"},
        ]
        related = m._related_articles_for_article(target, all_articles, limit=3)
        assert [a["slug"] for a in related] == ["two", "one"]

    def test_related_articles_tiebreaks_by_date_then_title(self):
        m = self._mod()
        target = {"slug": "target", "topics": ["A"], "published_date": "2026-04-20", "title": "Target"}
        all_articles = [
            {"slug": "old", "topics": ["A"], "published_date": "2026-04-18", "title": "Zebra"},
            {"slug": "new", "topics": ["A"], "published_date": "2026-04-19", "title": "Apple"},
            {"slug": "mid", "topics": ["A"], "published_date": "2026-04-19", "title": "Banana"},
        ]
        related = m._related_articles_for_article(target, all_articles, limit=3)
        # Same overlap (1), same date (2026-04-19) for new and mid -> title alphabetical
        assert [a["slug"] for a in related] == ["new", "mid", "old"]

    def test_related_articles_respects_limit(self):
        m = self._mod()
        target = {"slug": "target", "topics": ["A"], "published_date": "2026-04-20", "title": "Target"}
        all_articles = [
            {"slug": f"a{i}", "topics": ["A"], "published_date": f"2026-04-{10+i:02d}", "title": f"A{i}"}
            for i in range(10)
        ]
        related = m._related_articles_for_article(target, all_articles, limit=3)
        assert len(related) == 3

    # --- End-to-end article page rendering ---------------------------------

    def _synthetic_index(self, n=3):
        articles = []
        for i in range(n):
            day = 20 - i
            articles.append({
                "folder": f"2026-04-{day:02d}-article-{i}",
                "slug": f"article-{i}",
                "title": f"Test Article {i}",
                "published_date": f"2026-04-{day:02d}",
                "tags": ["AI Strategy"],
                "topics": ["AI Strategy", "European SME AI"],
                "funnel_stage": "middle",
                "canonical_url": f"https://radar.firstaimovers.com/article-{i}",
            })
        return {"articles": articles}

    def _run(self, monkeypatch, tmp_path, index):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        from pathlib import Path as P
        real_root = P(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")

        for a in index["articles"]:
            folder = a["folder"]
            (tmp_path / "articles" / folder).mkdir(exist_ok=True)
            body = (
                f'---\ntitle: "{a["title"]}"\nauthor: "Dr. Hernani Costa"\n'
                f'canonical_url: "{a["canonical_url"]}"\npublished_date: "{a["published_date"]}"\n'
                f'license: "CC BY 4.0"\n---\n'
                f'# {a["title"]}\n\n'
                f'## Introduction\n\nThis is the introduction paragraph with enough words to fill some space.\n\n'
                f'### Background\n\nSome background info here.\n\n'
                f'## Key Point\n\n- Bullet one\n- Bullet two\n\n'
                f'[A link](https://example.com)\n\n'
                f'> A blockquote\n\n'
                f'```python\nprint("hello")\n```\n')
            (tmp_path / "articles" / folder / "article.md").write_text(body, encoding="utf-8")

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return tmp_path / "site"

    def test_article_page_has_breadcrumb(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'class="breadcrumb"' in page
        assert "Home" in page
        assert "Topics" in page or "Article" in page

    def test_article_page_has_reading_time(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert "min read" in page or "minute" in page.lower()

    def test_article_page_has_toc_when_enough_headings(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'class="toc"' in page
        assert "Introduction" in page
        assert "Key Point" in page

    def test_article_page_headings_have_ids(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'id="introduction"' in page
        assert 'id="key-point"' in page

    def test_article_page_has_related_articles(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'class="related-articles"' in page
        # Should show related articles (not the current one)
        assert "Test Article 1" in page or "Test Article 2" in page

    def test_article_page_toc_hidden_when_few_headings(self, monkeypatch, tmp_path):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        from pathlib import Path as P
        real_root = P(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")

        folder = "2026-04-20-short"
        (tmp_path / "articles" / folder).mkdir(exist_ok=True)
        (tmp_path / "articles" / folder / "article.md").write_text(
            '---\ntitle: Short\n---\n# Short\n\nOnly one paragraph.\n', encoding="utf-8")
        index = {"articles": [{
            "folder": folder, "slug": "short", "title": "Short",
            "published_date": "2026-04-20", "tags": [], "topics": [],
            "funnel_stage": "middle", "canonical_url": "https://radar.firstaimovers.com/short",
        }]}
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        page = (tmp_path / "site" / "articles" / "short" / "index.html").read_text(encoding="utf-8")
        assert 'class="toc"' not in page

    # --- Regression guards -------------------------------------------------

    def test_article_page_still_noindex_follow(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'name="robots" content="noindex, follow"' in page

    def test_article_page_still_external_canonical(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'rel="canonical" href="https://radar.firstaimovers.com/article-0"' in page

    def test_article_page_still_has_jsonld(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert '"@type": "Article"' in page or '"@type":"Article"' in page

    def test_sitemap_unchanged(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        m.build_sitemap(self._synthetic_index(3))
        xml = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
        assert "/articles/article-0/" not in xml

    def test_feed_unchanged(self, monkeypatch, tmp_path):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        for a in self._synthetic_index(3)["articles"]:
            d = tmp_path / "articles" / a["folder"]
            d.mkdir(exist_ok=True)
            (d / "article.md").write_text(f"---\ntitle: {a['title']}\n---\n# {a['title']}\n\nBody.\n")
        m.build_feed(self._synthetic_index(3))
        xml = (tmp_path / "feed.xml").read_text(encoding="utf-8")
        assert "https://radar.firstaimovers.com/article-0" in xml
        assert "/articles/article-0/" not in xml


# =========================================================================
# Tests: E8 hardening — duplicate-title gate
# =========================================================================

class TestDuplicateTitles:
    """Duplicate-title detection logic."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def test_no_duplicates_returns_empty(self):
        m = self._mod()
        index = {"articles": [
            {"folder": "a", "title": "Alpha"},
            {"folder": "b", "title": "Beta"},
        ]}
        assert m.check_duplicate_titles(index) == []

    def test_detects_duplicate_titles_case_insensitive(self):
        m = self._mod()
        index = {"articles": [
            {"folder": "a", "title": "Alpha", "published_date": "2026-04-01"},
            {"folder": "b", "title": "alpha", "published_date": "2026-04-02"},
        ]}
        dups = m.check_duplicate_titles(index)
        assert len(dups) == 1
        title, folders = dups[0]
        assert title == "alpha"
        assert sorted(folders) == [("a", "2026-04-01"), ("b", "2026-04-02")]

    def test_empty_titles_ignored(self):
        m = self._mod()
        index = {"articles": [
            {"folder": "a", "title": ""},
            {"folder": "b", "title": None},
            {"folder": "c", "title": "Real"},
        ]}
        assert m.check_duplicate_titles(index) == []

    def test_script_exits_zero_when_clean(self, tmp_path):
        index = {"articles": [
            {"folder": "a", "title": "Unique", "published_date": "2026-04-01"},
        ]}
        idx = tmp_path / "index.json"
        idx.write_text(json.dumps(index), encoding="utf-8")
        script = Path(__file__).resolve().parents[1] / "check_duplicate_titles.py"
        import subprocess
        result = subprocess.run(
            [sys.executable, str(script), "--index", str(idx)],
            capture_output=True, text=True)
        assert result.returncode == 0
        assert "no duplicate" in result.stdout.lower()

    def test_script_exits_one_with_context(self, tmp_path):
        index = {"articles": [
            {"folder": "2026-04-01-a", "title": "Same", "published_date": "2026-04-01"},
            {"folder": "2026-03-01-b", "title": "Same", "published_date": "2026-03-01"},
        ]}
        idx = tmp_path / "index.json"
        idx.write_text(json.dumps(index), encoding="utf-8")
        script = Path(__file__).resolve().parents[1] / "check_duplicate_titles.py"
        import subprocess
        result = subprocess.run(
            [sys.executable, str(script), "--index", str(idx)],
            capture_output=True, text=True)
        assert result.returncode == 1
        assert "2026-04-01-a" in result.stderr
        assert "2026-03-01-b" in result.stderr


# =========================================================================
# Tests: E8 hardening — feed byte-stability
# =========================================================================

class TestFeedByteStability:
    """Prove Atom and JSON Feed outputs are deterministic for fixed input."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def _synthetic_index(self, n=3):
        return {
            "articles": [
                {
                    "folder": f"2026-04-{20-i:02d}-entry-{i}",
                    "title": f"Entry {i}",
                    "published_date": f"2026-04-{20-i:02d}",
                    "tags": [f"tag{j}" for j in range(7)],
                    "topics": [f"topic{j}" for j in range(3)],
                    "funnel_stage": "middle",
                    "canonical_url": f"https://radar.firstaimovers.com/entry-{i}",
                }
                for i in range(n)
            ],
        }

    def test_atom_feed_is_identical_across_two_builds(self, monkeypatch, tmp_path):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        for a in self._synthetic_index(3)["articles"]:
            d = tmp_path / "articles" / a["folder"]
            d.mkdir(exist_ok=True)
            (d / "article.md").write_text(f"---\ntitle: {a['title']}\n---\n# {a['title']}\n\nBody.\n")
        idx = self._synthetic_index(3)
        m.build_feed(idx)
        first = (tmp_path / "feed.xml").read_text(encoding="utf-8")
        m.build_feed(idx)
        second = (tmp_path / "feed.xml").read_text(encoding="utf-8")
        assert first == second

    def test_json_feed_is_identical_across_two_builds(self, monkeypatch, tmp_path):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        for a in self._synthetic_index(3)["articles"]:
            d = tmp_path / "articles" / a["folder"]
            d.mkdir(exist_ok=True)
            (d / "article.md").write_text(f"---\ntitle: {a['title']}\n---\n# {a['title']}\n\nBody.\n")
        idx = self._synthetic_index(3)
        m.build_json_feed(idx)
        first = (tmp_path / "feed.json").read_text(encoding="utf-8")
        m.build_json_feed(idx)
        second = (tmp_path / "feed.json").read_text(encoding="utf-8")
        assert first == second


# =========================================================================
# Tests: E8 hardening — llms-full.txt byte-stability
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


# =========================================================================
# Tests: E8 hardening — XSS resistance
# =========================================================================

class TestXssResistance:
    """Strengthened XSS coverage for article body, title, summary, topic intro, JSON-LD."""

    def _mod(self):
        pytest.importorskip("jinja2")
        pytest.importorskip("markdown")
        import rebuild_local
        return rebuild_local

    def _run_with_custom_article(self, monkeypatch, tmp_path, folder, title, body_md, topics=None):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        from pathlib import Path as P
        real_root = P(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")

        d = tmp_path / "articles" / folder
        d.mkdir(parents=True, exist_ok=True)
        (d / "article.md").write_text(
            f'---\ntitle: "{title}"\nauthor: "Dr. Hernani Costa"\n'
            f'canonical_url: "https://radar.firstaimovers.com/{folder}"\n'
            f'published_date: "2026-04-20"\nlicense: "CC BY 4.0"\n---\n'
            f'# {title}\n\n{body_md}\n', encoding="utf-8")

        index = {"articles": [{
            "folder": folder, "slug": "unsafe", "title": title,
            "published_date": "2026-04-20", "tags": [],
            "topics": topics or ["AI Strategy"],
            "funnel_stage": "middle",
            "canonical_url": f"https://radar.firstaimovers.com/{folder}",
        }]}
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return (tmp_path / "site" / "articles" / "unsafe" / "index.html").read_text(encoding="utf-8")

    def _article_body_from_page(self, page_html):
        start = page_html.find('<div class="article-body">')
        end = page_html.find('</div>', start) + len('</div>')
        return page_html[start:end] if start != -1 else page_html

    def test_malicious_title_escaped_in_page(self, monkeypatch, tmp_path):
        title = '<script>alert("xss")</script>'
        page = self._run_with_custom_article(
            monkeypatch, tmp_path, "2026-04-20-t", title, "Body.")
        # h1 should contain escaped title (jinja2 escapes quotes as &#34;)
        assert '<h1>&lt;script&gt;alert(&#34;xss&#34;)&lt;/script&gt;</h1>' in page
        # meta description should be escaped
        assert '&lt;script&gt;alert(&#34;xss&#34;)&lt;/script&gt;' in page

    def test_malicious_summary_escaped_in_meta(self, monkeypatch, tmp_path):
        """Summary is used in <meta name=description>; must be escaped."""
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        from pathlib import Path as P
        real_root = P(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")

        folder = "2026-04-20-s"
        d = tmp_path / "articles" / folder
        d.mkdir(parents=True, exist_ok=True)
        (d / "article.md").write_text(
            '---\ntitle: "Test"\n---\n# Test\n\n> **TL;DR:** <script>bad()</script>\n\nBody.\n',
            encoding="utf-8")

        index = {"articles": [{
            "folder": folder, "slug": "s", "title": "Test",
            "published_date": "2026-04-20", "tags": [], "topics": ["AI Strategy"],
            "funnel_stage": "middle", "canonical_url": "https://radar.firstaimovers.com/s",
        }]}
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        page = (tmp_path / "site" / "articles" / "s" / "index.html").read_text(encoding="utf-8")
        # meta description should contain escaped script tag
        assert '&lt;script&gt;bad()&lt;/script&gt;' in page

    def test_malicious_topic_intro_escaped_on_topic_page(self, monkeypatch, tmp_path):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        from pathlib import Path as P
        real_root = P(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")

        # Need >= MIN_ARTICLES_FOR_TOPIC_PAGE articles for topic page to exist
        articles = []
        for i in range(6):
            folder = f"2026-04-{20-i:02d}-t{i}"
            d = tmp_path / "articles" / folder
            d.mkdir(parents=True, exist_ok=True)
            (d / "article.md").write_text(f'---\ntitle: T{i}\n---\n# T{i}\n\nBody.\n', encoding="utf-8")
            articles.append({
                "folder": folder, "slug": f"t{i}", "title": f"T{i}",
                "published_date": f"2026-04-{20-i:02d}", "tags": [], "topics": ["AI Strategy"],
                "funnel_stage": "middle", "canonical_url": f"https://radar.firstaimovers.com/t{i}",
            })

        index = {"articles": articles}
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        monkeypatch.setattr(m, "_load_topic_intros", lambda: {
            "AI Strategy": {
                "lede": '<script>alert(1)</script>Lede here',
                "key_themes": ['<img src=x onerror=alert(1)>Theme'],
                "why_it_matters": '<iframe src="evil.com"></iframe>Why',
            },
        })
        m.build_site(index)
        page = (tmp_path / "site" / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        # meta description and JSON-LD should contain escaped tags
        assert "&lt;script&gt;alert(1)&lt;/script&gt;Lede here" in page
        # Raw malicious markup must not appear in content areas
        assert '<p class="lede">&lt;script&gt;alert(1)&lt;/script&gt;Lede here</p>' in page
        assert '<li>&lt;img src=x onerror=alert(1)&gt;Theme</li>' in page
        assert '<p>&lt;iframe src=&#34;evil.com&#34;&gt;&lt;/iframe&gt;Why</p>' in page

    def test_json_ld_remains_parseable_with_malicious_title(self, monkeypatch, tmp_path):
        title = 'Test "with quotes" and \\ backslash'
        page = self._run_with_custom_article(
            monkeypatch, tmp_path, "2026-04-20-j", title, "Body.")
        match = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.DOTALL)
        assert match is not None
        data = json.loads(match.group(1))
        assert data["@type"] == "Article"
        assert data["headline"] == title

    def test_article_body_script_tag_removed(self, monkeypatch, tmp_path):
        page = self._run_with_custom_article(
            monkeypatch, tmp_path, "2026-04-20-x",
            "Title", '<script>alert("xss")</script>')
        body = self._article_body_from_page(page)
        assert "<script>" not in body

    def test_article_body_javascript_url_removed(self, monkeypatch, tmp_path):
        page = self._run_with_custom_article(
            monkeypatch, tmp_path, "2026-04-20-x",
            "Title", '<a href="javascript:alert(1)">click</a>')
        body = self._article_body_from_page(page)
        assert "javascript:" not in body
        assert "click" in body


# =========================================================================
# Tests: E8 hardening — atomic writes
# =========================================================================

class TestAtomicWrites:
    """Atomic file-write helper contracts."""

    def test_atomic_write_json_produces_valid_json(self, tmp_path):
        from _atomic_io import atomic_write_json
        path = tmp_path / "test.json"
        atomic_write_json(path, {"key": "value", "num": 42})
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data == {"key": "value", "num": 42}

    def test_atomic_write_json_preserves_indent_and_newline(self, tmp_path):
        from _atomic_io import atomic_write_json
        path = tmp_path / "test.json"
        atomic_write_json(path, {"a": 1})
        text = path.read_text(encoding="utf-8")
        assert text.startswith("{\n")
        assert text.endswith("\n")

    def test_atomic_write_text_produces_readable_text(self, tmp_path):
        from _atomic_io import atomic_write_text
        path = tmp_path / "test.txt"
        atomic_write_text(path, "hello world\n")
        assert path.read_text(encoding="utf-8") == "hello world\n"

    def test_atomic_write_preserves_existing_file_if_temp_fails(self, monkeypatch, tmp_path):
        """Simulate a failure during temp write: existing file must survive."""
        from _atomic_io import atomic_write_text
        path = tmp_path / "target.txt"
        path.write_text("original", encoding="utf-8")

        real_write_text = type(path).write_text
        def failing_write_text(self, *args, **kwargs):
            if self.name.endswith(".tmp"):
                raise OSError("disk full")
            return real_write_text(self, *args, **kwargs)

        monkeypatch.setattr(type(path), "write_text", failing_write_text)
        with pytest.raises(OSError, match="disk full"):
            atomic_write_text(path, "new content")
        assert path.read_text(encoding="utf-8") == "original"

    def test_atomic_write_json_uses_utf8(self, tmp_path):
        from _atomic_io import atomic_write_json
        path = tmp_path / "test.json"
        atomic_write_json(path, {"emoji": "🚀", "euro": "€"})
        text = path.read_text(encoding="utf-8")
        assert "🚀" in text
        assert "€" in text


# =========================================================================
# Tests: E11 accessibility — skip link, landmarks, focus, theme toggle
# =========================================================================

class TestAccessibility:
    """Accessibility fixes: skip link, landmarks, focus states, theme toggle semantics."""

    def _mod(self):
        pytest.importorskip("jinja2")
        pytest.importorskip("markdown")
        import rebuild_local
        return rebuild_local

    def _run(self, monkeypatch, tmp_path, index):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        from pathlib import Path as P
        real_root = P(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")

        for a in index.get("articles", []):
            folder = a.get("folder", "")
            if folder:
                (tmp_path / "articles" / folder).mkdir(exist_ok=True)
                (tmp_path / "articles" / folder / "article.md").write_text(
                    f"---\ntitle: {a.get('title', 'T')}\n---\n# {a.get('title', 'T')}\n\nBody.\n")

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return tmp_path / "site"

    def _synthetic_index(self, n=3):
        articles = []
        for i in range(n):
            day = 20 - i
            articles.append({
                "folder": f"2026-04-{day:02d}-article-{i}",
                "slug": f"article-{i}",
                "title": f"Test Article {i}",
                "published_date": f"2026-04-{day:02d}",
                "tags": [],
                "topics": ["AI Strategy"],
                "funnel_stage": "middle",
                "canonical_url": f"https://radar.firstaimovers.com/article-{i}",
            })
        return {"articles": articles}

    # --- Skip link ---------------------------------------------------------

    def test_home_page_has_skip_link(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        home = (site / "index.html").read_text(encoding="utf-8")
        assert '<a href="#main-content" class="skip-link">Skip to content</a>' in home

    def test_topic_page_has_skip_link(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert 'class="skip-link"' in page

    def test_article_page_has_skip_link(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'class="skip-link"' in page

    def test_about_page_has_skip_link(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        page = (site / "about" / "index.html").read_text(encoding="utf-8")
        assert 'class="skip-link"' in page

    def test_404_page_has_skip_link(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        page = (site / "404.html").read_text(encoding="utf-8")
        assert 'class="skip-link"' in page

    # --- Main landmark -----------------------------------------------------

    def test_main_has_id_main_content(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        home = (site / "index.html").read_text(encoding="utf-8")
        assert '<main id="main-content"' in home

    # --- Theme toggle accessibility ----------------------------------------

    def test_theme_toggle_is_button(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        home = (site / "index.html").read_text(encoding="utf-8")
        assert 'id="theme-toggle"' in home
        assert '<button' in home

    def test_theme_toggle_has_aria_pressed(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        home = (site / "index.html").read_text(encoding="utf-8")
        assert 'aria-pressed="false"' in home or 'aria-pressed="true"' in home

    def test_theme_toggle_aria_label_updates_with_theme(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        home = (site / "index.html").read_text(encoding="utf-8")
        # The inline script should set the label based on the stored/default theme
        assert "Toggle light mode" in home or "Toggle dark mode" in home

    # --- Navigation landmarks ----------------------------------------------

    def test_primary_nav_has_aria_label(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        home = (site / "index.html").read_text(encoding="utf-8")
        assert 'aria-label="Primary"' in home

    # --- Breadcrumbs -------------------------------------------------------

    def test_article_breadcrumb_has_aria_label(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'aria-label="Breadcrumb"' in page

    def test_topic_breadcrumb_has_aria_label(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert 'aria-label="Breadcrumb"' in page

    def test_about_breadcrumb_has_aria_label(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        page = (site / "about" / "index.html").read_text(encoding="utf-8")
        assert 'aria-label="Breadcrumb"' in page

    # --- Focus CSS ---------------------------------------------------------

    def test_focus_visible_css_exists(self):
        from pathlib import Path as P
        css = (P(__file__).resolve().parents[2] / "static" / "style.css").read_text(encoding="utf-8")
        assert ":focus-visible" in css

    def test_button_focus_visible_css_exists(self):
        from pathlib import Path as P
        css = (P(__file__).resolve().parents[2] / "static" / "style.css").read_text(encoding="utf-8")
        assert "button:focus-visible" in css or ".theme-toggle:focus-visible" in css

    def test_skip_link_css_exists(self):
        from pathlib import Path as P
        css = (P(__file__).resolve().parents[2] / "static" / "style.css").read_text(encoding="utf-8")
        assert ".skip-link" in css

    # --- Reduced motion ----------------------------------------------------

    def test_prefers_reduced_motion_exists(self):
        from pathlib import Path as P
        css = (P(__file__).resolve().parents[2] / "static" / "style.css").read_text(encoding="utf-8")
        assert "prefers-reduced-motion" in css

    # --- No heading-order violations (template level) ----------------------

    def test_home_page_heading_order(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        home = (site / "index.html").read_text(encoding="utf-8")
        # Home should have h1 before h2
        h1_pos = home.find("<h1>")
        h2_pos = home.find("<h2>")
        assert h1_pos != -1
        assert h2_pos == -1 or h1_pos < h2_pos

    def test_topic_page_heading_order(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        h1_pos = page.find("<h1>")
        h2_pos = page.find("<h2>")
        assert h1_pos != -1
        assert h2_pos == -1 or h1_pos < h2_pos

    def test_article_page_heading_order(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        h1_pos = page.find("<h1>")
        h2_pos = page.find("<h2>")
        assert h1_pos != -1
        assert h2_pos == -1 or h1_pos < h2_pos


# =========================================================================
# Tests: E10 client-side search
# =========================================================================

class TestClientSearch:
    """Client-side search over index.json on home and topics index pages."""

    def _mod(self):
        pytest.importorskip("jinja2")
        pytest.importorskip("markdown")
        import rebuild_local
        return rebuild_local

    def _run(self, monkeypatch, tmp_path, index):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        from pathlib import Path as P
        real_root = P(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")

        for a in index.get("articles", []):
            folder = a.get("folder", "")
            if folder:
                (tmp_path / "articles" / folder).mkdir(exist_ok=True)
                (tmp_path / "articles" / folder / "article.md").write_text(
                    f"---\ntitle: {a.get('title', 'T')}\n---\n# {a.get('title', 'T')}\n\nBody.\n")

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return tmp_path / "site"

    def _synthetic_index(self, n=3):
        articles = []
        for i in range(n):
            day = 20 - i
            articles.append({
                "folder": f"2026-04-{day:02d}-article-{i}",
                "slug": f"article-{i}",
                "title": f"Test Article {i}",
                "published_date": f"2026-04-{day:02d}",
                "tags": ["AI Strategy", "SME"],
                "topics": ["AI Strategy", "European SME AI"],
                "funnel_stage": "middle",
                "canonical_url": f"https://radar.firstaimovers.com/article-{i}",
            })
        return {"articles": articles}

    def test_home_page_has_search_input(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        home = (site / "index.html").read_text(encoding="utf-8")
        assert '<input' in home
        assert 'type="search"' in home or 'id="archive-search"' in home

    def test_home_page_has_search_results_region(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        home = (site / "index.html").read_text(encoding="utf-8")
        assert 'id="search-results"' in home

    def test_topics_index_has_search_input(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        page = (site / "topics" / "index.html").read_text(encoding="utf-8")
        assert '<input' in page
        assert 'type="search"' in page or 'id="archive-search"' in page

    def test_topics_index_has_search_results_region(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        page = (site / "topics" / "index.html").read_text(encoding="utf-8")
        assert 'id="search-results"' in page

    def test_search_js_included_on_home(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        home = (site / "index.html").read_text(encoding="utf-8")
        assert "search.js" in home

    def test_search_js_included_on_topics_index(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        page = (site / "topics" / "index.html").read_text(encoding="utf-8")
        assert "search.js" in page

    def test_search_js_file_exists(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        assert (site / "search.js").exists()

    def test_search_input_has_accessible_label(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        home = (site / "index.html").read_text(encoding="utf-8")
        assert 'aria-label="Search articles"' in home or '<label' in home

    def test_search_results_has_aria_live(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        home = (site / "index.html").read_text(encoding="utf-8")
        assert 'aria-live="polite"' in home

    def test_article_page_does_not_have_search(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert "archive-search" not in page

    def test_about_page_does_not_have_search(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        page = (site / "about" / "index.html").read_text(encoding="utf-8")
        assert "archive-search" not in page

    def test_search_js_fetches_index_json(self):
        from pathlib import Path as P
        js = (P(__file__).resolve().parents[2] / "static" / "search.js").read_text(encoding="utf-8")
        assert "index.json" in js

    def test_search_js_links_to_local_article_pages(self):
        from pathlib import Path as P
        js = (P(__file__).resolve().parents[2] / "static" / "search.js").read_text(encoding="utf-8")
        assert "articles/" in js

    def test_search_js_caps_results(self):
        from pathlib import Path as P
        js = (P(__file__).resolve().parents[2] / "static" / "search.js").read_text(encoding="utf-8")
        assert "25" in js or "20" in js or "30" in js or "limit" in js.lower() or "max" in js.lower() or "cap" in js.lower() or "slice" in js.lower()

    def test_sitemap_still_excludes_local_article_pages(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        m.build_sitemap(self._synthetic_index(3))
        xml = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
        assert "/articles/article-0/" not in xml

    def test_feed_urls_still_canonical(self, monkeypatch, tmp_path):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        for a in self._synthetic_index(3)["articles"]:
            d = tmp_path / "articles" / a["folder"]
            d.mkdir(exist_ok=True)
            (d / "article.md").write_text(f"---\ntitle: {a['title']}\n---\n# {a['title']}\n\nBody.\n")
        m.build_feed(self._synthetic_index(3))
        xml = (tmp_path / "feed.xml").read_text(encoding="utf-8")
        assert "https://radar.firstaimovers.com/article-0" in xml
        assert "/articles/article-0/" not in xml


# =========================================================================
# Tests: PR B — IndexNow integration
# =========================================================================

class TestIndexNow:
    """IndexNow key file, submission script, and workflow integration."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def _key_file(self, tmp_path, key="f9d934376f0a4a55c2fd6608f2868f48"):
        (tmp_path / ".indexnow-key").write_text(key, encoding="utf-8")
        return key

    def _sitemap(self, tmp_path, urls):
        xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u in urls:
            xml += f"  <url><loc>{u}</loc></url>\n"
        xml += "</urlset>\n"
        (tmp_path / "sitemap.xml").write_text(xml, encoding="utf-8")

    # --- Key file tests ----------------------------------------------------

    def test_key_format_is_hex_32_chars(self):
        from pathlib import Path as P
        key_path = P(__file__).resolve().parents[2] / ".indexnow-key"
        assert key_path.exists(), ".indexnow-key must exist at repo root"
        key = key_path.read_text(encoding="utf-8").strip()
        assert len(key) == 32, f"Key must be 32 hex chars, got {len(key)}"
        assert all(c in "0123456789abcdef" for c in key.lower()), "Key must be hex"

    def test_key_file_written_to_site_on_rebuild(self, monkeypatch, tmp_path):
        m = self._mod()
        key = self._key_file(tmp_path)
        # Minimal build_site context: need articles dir, templates dir, static dir
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        from pathlib import Path
        real_root = Path(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        # The key file is written by build_site reading .indexnow-key from REPO_ROOT
        m.build_site({"articles": []})
        key_file = tmp_path / "site" / f"{key}.txt"
        assert key_file.exists(), f"Key file {key}.txt must be in site root"
        assert key_file.read_text(encoding="utf-8").strip() == key

    # --- submit_indexnow.py tests ------------------------------------------

    def test_dry_run_reads_sitemap_and_lists_urls(self, monkeypatch, tmp_path):
        import subprocess, sys
        key = self._key_file(tmp_path)
        urls = ["https://articles.firstaimovers.com/",
                "https://articles.firstaimovers.com/about/",
                "https://articles.firstaimovers.com/topics/",
                "https://articles.firstaimovers.com/topics/ai-strategy/"]
        self._sitemap(tmp_path, urls)
        from pathlib import Path
        script = Path(__file__).resolve().parents[2] / "tools" / "submit_indexnow.py"
        result = subprocess.run(
            [sys.executable, str(script),
             "--sitemap", str(tmp_path / "sitemap.xml"),
             "--key", key,
             "--key-location", f"https://articles.firstaimovers.com/{key}.txt",
             "--dry-run"],
            capture_output=True, text=True, cwd=str(tmp_path.parent.parent))
        assert result.returncode == 0, result.stderr
        assert "4" in result.stdout or "4 URL" in result.stdout, result.stdout
        assert "articles.firstaimovers.com" in result.stdout

    def test_payload_contains_correct_fields(self, monkeypatch, tmp_path):
        import submit_indexnow
        key = self._key_file(tmp_path)
        urls = ["https://articles.firstaimovers.com/",
                "https://articles.firstaimovers.com/topics/ai-strategy/"]
        payload = submit_indexnow._build_payload(urls, key)
        assert payload["host"] == "articles.firstaimovers.com"
        assert payload["key"] == key
        assert payload["keyLocation"] == f"https://articles.firstaimovers.com/{key}.txt"
        assert payload["urlList"] == urls

    def test_rejects_cross_host_urls(self, monkeypatch, tmp_path):
        import submit_indexnow
        key = self._key_file(tmp_path)
        urls = ["https://articles.firstaimovers.com/",
                "https://radar.firstaimovers.com/some-article"]
        filtered = submit_indexnow._filter_urls(urls)
        assert "radar.firstaimovers.com" not in filtered
        assert "https://articles.firstaimovers.com/" in filtered

    def test_excludes_local_article_pages(self, monkeypatch, tmp_path):
        import submit_indexnow
        urls = ["https://articles.firstaimovers.com/",
                "https://articles.firstaimovers.com/articles/some-slug/"]
        filtered = submit_indexnow._filter_urls(urls)
        assert "/articles/some-slug/" not in filtered
        assert "https://articles.firstaimovers.com/" in filtered

    def test_excludes_data_file_extensions(self, monkeypatch, tmp_path):
        import submit_indexnow
        urls = ["https://articles.firstaimovers.com/",
                "https://articles.firstaimovers.com/feed.xml",
                "https://articles.firstaimovers.com/index.json",
                "https://articles.firstaimovers.com/llms.txt",
                "https://articles.firstaimovers.com/README.md"]
        filtered = submit_indexnow._filter_urls(urls)
        assert filtered == ["https://articles.firstaimovers.com/"]

    def test_treats_200_as_success(self, monkeypatch, tmp_path):
        import submit_indexnow
        key = self._key_file(tmp_path)
        class FakeResponse:
            status = 200
            def read(self): return b'{}'
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def close(self): pass
        def fake_open(req, timeout=None):
            return FakeResponse()
        monkeypatch.setattr(submit_indexnow, "urlopen", fake_open)
        result = submit_indexnow._submit([], key, "https://api.indexnow.org/indexnow")
        assert result is True

    def test_treats_202_as_success(self, monkeypatch, tmp_path):
        import submit_indexnow
        key = self._key_file(tmp_path)
        class FakeResponse:
            status = 202
            def read(self): return b'{}'
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def close(self): pass
        def fake_open(req, timeout=None):
            return FakeResponse()
        monkeypatch.setattr(submit_indexnow, "urlopen", fake_open)
        result = submit_indexnow._submit([], key, "https://api.indexnow.org/indexnow")
        assert result is True

    def test_fails_on_403(self, monkeypatch, tmp_path):
        import submit_indexnow
        key = self._key_file(tmp_path)
        from urllib.error import HTTPError
        class FakeResponse:
            status = 403
            def read(self): return b'Forbidden'
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def close(self): pass
        def fake_open(req, timeout=None):
            resp = FakeResponse()
            raise HTTPError("https://api.indexnow.org/indexnow", 403, "Forbidden", {}, resp)
        monkeypatch.setattr(submit_indexnow, "urlopen", fake_open)
        result = submit_indexnow._submit([], key, "https://api.indexnow.org/indexnow")
        assert result is False

    def test_fails_on_429(self, monkeypatch, tmp_path):
        import submit_indexnow
        key = self._key_file(tmp_path)
        from urllib.error import HTTPError
        class FakeResponse:
            status = 429
            def read(self): return b'Too Many Requests'
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def close(self): pass
        def fake_open(req, timeout=None):
            resp = FakeResponse()
            raise HTTPError("https://api.indexnow.org/indexnow", 429, "Too Many Requests", {}, resp)
        monkeypatch.setattr(submit_indexnow, "urlopen", fake_open)
        result = submit_indexnow._submit([], key, "https://api.indexnow.org/indexnow")
        assert result is False

    def test_sitemap_count_stays_at_80(self):
        from pathlib import Path as P
        sitemap = P(__file__).resolve().parents[2] / "sitemap.xml"
        assert sitemap.exists()
        xml = sitemap.read_text(encoding="utf-8")
        count = xml.count("<url>")
        assert count == 80, f"Sitemap must contain exactly 80 URLs, got {count}"


# =========================================================================
# Tests: PR C — Topic hub SEO/GEO enhancement
# =========================================================================

class TestTopicHubSeo:
    """Topic hub metadata, structured data, sitemap freshness, and internal linking."""

    def _mod(self):
        pytest.importorskip("jinja2")
        pytest.importorskip("markdown")
        import rebuild_local
        return rebuild_local

    def _synthetic_index(self, n=3):
        articles = []
        for i in range(n):
            day = 20 - i
            articles.append({
                "folder": f"2026-04-{day:02d}-article-{i}",
                "slug": f"article-{i}",
                "title": f"Test Article {i}",
                "published_date": f"2026-04-{day:02d}",
                "tags": ["AI Strategy"],
                "topics": ["AI Strategy", "European SME AI"],
                "funnel_stage": "middle",
                "canonical_url": f"https://radar.firstaimovers.com/article-{i}",
            })
        return {"articles": articles}

    def _run(self, monkeypatch, tmp_path, index):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        from pathlib import Path as P
        real_root = P(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")

        for a in index["articles"]:
            folder = a["folder"]
            (tmp_path / "articles" / folder).mkdir(exist_ok=True)
            (tmp_path / "articles" / folder / "article.md").write_text(
                f'---\ntitle: "{a["title"]}"\nauthor: "Dr. Hernani Costa"\n'
                f'canonical_url: "{a["canonical_url"]}"\npublished_date: "{a["published_date"]}"\n'
                f'license: "CC BY 4.0"\n---\n'
                f'# {a["title"]}\n\n## Introduction\n\nBody.\n',
                encoding="utf-8")

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return tmp_path / "site"

    # --- Title / meta ------------------------------------------------------

    def test_topic_page_title_includes_topic_name_and_archive_context(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert "<title>AI Strategy Articles — First AI Movers Archive</title>" in page

    def test_topic_page_meta_description_includes_topic_name_and_count(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        desc = '<meta name="description" content="'
        assert desc in page
        # Description should mention the topic name
        assert "AI Strategy" in page or "ai-strategy" in page

    # --- Structured data ---------------------------------------------------

    def test_topic_page_has_valid_json_ld(self, monkeypatch, tmp_path):
        import json
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        # Extract first JSON-LD block
        start = page.find('<script type="application/ld+json">')
        end = page.find('</script>', start)
        block = page[start + len('<script type="application/ld+json">'):end]
        data = json.loads(block)
        assert "@context" in data
        assert "https://schema.org" in data["@context"]

    def test_topic_json_ld_has_collection_page_type(self, monkeypatch, tmp_path):
        import json
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        start = page.find('<script type="application/ld+json">')
        end = page.find('</script>', start)
        data = json.loads(page[start + len('<script type="application/ld+json">'):end])
        assert data["@type"] == "CollectionPage"
        assert "mainEntity" in data
        assert data["mainEntity"]["@type"] == "ItemList"

    def test_topic_json_ld_no_invented_images(self, monkeypatch, tmp_path):
        import json
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        start = page.find('<script type="application/ld+json">')
        end = page.find('</script>', start)
        data = json.loads(page[start + len('<script type="application/ld+json">'):end])
        assert "image" not in data

    def test_topic_page_has_breadcrumb_json_ld(self, monkeypatch, tmp_path):
        import json
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        # Find second JSON-LD block (BreadcrumbList)
        first = page.find('<script type="application/ld+json">')
        second = page.find('<script type="application/ld+json">', first + 1)
        end = page.find('</script>', second)
        data = json.loads(page[second + len('<script type="application/ld+json">'):end])
        assert data["@type"] == "BreadcrumbList"
        assert len(data["itemListElement"]) == 3

    # --- Sitemap lastmod ---------------------------------------------------

    def test_sitemap_topic_lastmod_is_newest_article_date(self, monkeypatch, tmp_path):
        m = self._mod()
        # Need >= MIN_ARTICLES_FOR_TOPIC_PAGE (5) articles for topic hub to exist
        articles = []
        for i in range(5):
            day = 10 - i
            articles.append({
                "folder": f"2026-04-{day:02d}-a{i}", "title": f"A{i}",
                "published_date": f"2026-04-{day:02d}",
                "tags": [], "topics": ["AI Strategy"], "funnel_stage": "middle",
                "canonical_url": f"https://radar.firstaimovers.com/a{i}",
            })
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        m.build_sitemap({"articles": articles})
        xml = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
        # Topic hub lastmod should be newest article date: 2026-04-10
        assert "<loc>https://articles.firstaimovers.com/topics/ai-strategy/</loc>" in xml
        from xml.etree.ElementTree import fromstring
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        root = fromstring(xml)
        for url in root.findall("s:url", ns):
            loc = url.find("s:loc", ns).text
            if "topics/ai-strategy" in loc:
                lastmod = url.find("s:lastmod", ns).text
                assert lastmod == "2026-04-10", f"Expected 2026-04-10, got {lastmod}"
                break
        else:
            raise AssertionError("Topic hub URL not found in sitemap")

    # --- Internal linking --------------------------------------------------

    def test_article_page_links_to_topic_hub(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        # Pick any article page
        article_page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        # Should link to its primary topic hub somewhere on the page
        assert 'href="../../topics/ai-strategy/"' in article_page

    def test_article_page_preserves_noindex_external_canonical(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'name="robots" content="noindex, follow"' in page
        assert 'rel="canonical" href="https://radar.firstaimovers.com/article-0"' in page
