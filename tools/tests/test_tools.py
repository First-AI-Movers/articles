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
            "title": "Test Article One",
            "published_date": "2026-04-04",
            "tags": ["AI strategy", "EU AI Act"],
            "funnel_stage": "top",
            "canonical_url": "https://radar.firstaimovers.com/test-one",
        },
        {
            "folder": "2026-03-15-test-article-two",
            "title": "Test Article Two",
            "published_date": "2026-03-15",
            "tags": ["AI governance", "MCP"],
            "funnel_stage": "middle",
            "canonical_url": "https://radar.firstaimovers.com/test-two",
        },
        {
            "folder": "2025-06-01-test-article-three",
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

    Support-files block emits 11 URLs: home(1) + /about/(1) + /topics/(1) +
    8 weekly (ABOUT, CITATION, hernanicosta.json, llms.txt, llms-full.txt,
    llms-recent.txt, index.json, feed.xml) + README.md(1) = 12 support
    URLs. Article URLs are emitted only when the canonical_url host is in
    CANONICAL_ALLOWED_HOSTS. Topic hub URLs are emitted for every topic
    with >= MIN_ARTICLES_FOR_TOPIC_PAGE articles in the index
    (SAMPLE_INDEX has no `topics` field, so zero).
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
        # home(1) + about(1) + topics(1) + 8 weekly + README(1) = 12 support
        # + 3 allow-listed articles + 0 topic hubs = 15
        assert xml.count("<url>") == 15

    def test_article_entries_use_canonical_urls(self, monkeypatch, tmp_path):
        xml = self._run(monkeypatch, tmp_path, SAMPLE_INDEX["articles"])
        assert "https://radar.firstaimovers.com/test-one" in xml
        assert "https://radar.firstaimovers.com/test-two" in xml
        assert "https://insights.firstaimovers.com/test-three" in xml
        # No fabricated /articles/<folder>/ paths
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
        # Only support URLs remain: home + about + topics + 8 weekly + README = 12
        assert xml.count("<url>") == 12

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

    def test_article_lastmod_uses_published_date(self, monkeypatch, tmp_path):
        xml = self._run(monkeypatch, tmp_path, SAMPLE_INDEX["articles"])
        assert "<lastmod>2026-04-04</lastmod>" in xml

    def test_empty_index_emits_only_support_urls(self, monkeypatch, tmp_path):
        xml = self._run(monkeypatch, tmp_path, [])
        # home + about + topics + 8 weekly + README = 12
        assert xml.count("<url>") == 12

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
        assert xml.count("<url>") == 12  # only support URLs (12 total)


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

    def test_article_cards_link_to_canonical_not_self(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Governance": 6}))
        page = (site / "topics" / "ai-governance" / "index.html").read_text(encoding="utf-8")
        assert "https://radar.firstaimovers.com/slug1" in page
        # No self-links back to /articles/ paths on the site
        assert 'href="/articles/' not in page

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
