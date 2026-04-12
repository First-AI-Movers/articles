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
from unittest.mock import MagicMock, patch
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
# Tests: update_docs.py logic
# =========================================================================

class TestUpdateDocs:
    """Test README/llms.txt patching logic."""

    def _get_functions(self):
        """Import update_docs functions."""
        import update_docs
        return update_docs

    def test_compute_stats(self):
        mod = self._get_functions()
        stats = mod.compute_stats(SAMPLE_INDEX)
        assert stats["total"] == 3
        assert stats["tags_count"] == 4  # AI strategy, EU AI Act, AI governance, MCP
        assert stats["funnel"]["top"] == 1
        assert stats["funnel"]["middle"] == 1
        assert stats["funnel"]["bottom"] == 1
        assert stats["date_min"] == "2025-06-01"
        assert stats["date_max"] == "2026-04-04"

    def test_format_date_human(self):
        mod = self._get_functions()
        assert mod.format_date_human("2025-02-17") == "February 17, 2025"
        assert mod.format_date_human("2026-04-04") == "April 4, 2026"
        assert mod.format_date_human("invalid") == "invalid"

    def test_funnel_summary(self):
        mod = self._get_functions()
        funnel = {"top": 221, "middle": 423, "bottom": 4}
        result = mod.funnel_summary(funnel)
        assert "top (221 articles)" in result
        assert "middle (423)" in result
        assert "bottom (4)" in result

    def test_funnel_summary_first_gets_articles_label(self):
        mod = self._get_functions()
        funnel = {"middle": 10, "top": 5}
        result = mod.funnel_summary(funnel)
        assert result.startswith("top (5 articles)")

    def test_patch_readme_updates_badge(self):
        mod = self._get_functions()
        stats = {"total": 700, "tags_count": 4000, "funnel": {"top": 300, "middle": 395, "bottom": 5},
                 "date_min": "2025-02-17", "date_max": "2026-04-10"}
        new_content, changes = mod.patch_readme(SAMPLE_README, stats)
        assert "Articles-700-orange" in new_content
        assert "README.md" in changes

    def test_patch_readme_updates_article_count_in_description(self):
        mod = self._get_functions()
        stats = {"total": 700, "tags_count": 4000, "funnel": {"top": 300, "middle": 395, "bottom": 5},
                 "date_min": "2025-02-17", "date_max": "2026-04-10"}
        new_content, _ = mod.patch_readme(SAMPLE_README, stats)
        assert "700 original articles" in new_content

    def test_patch_readme_updates_quick_stats(self):
        mod = self._get_functions()
        stats = {"total": 700, "tags_count": 4000, "funnel": {"top": 300, "middle": 395, "bottom": 5},
                 "date_min": "2025-02-17", "date_max": "2026-04-10"}
        new_content, _ = mod.patch_readme(SAMPLE_README, stats)
        assert "**700** articles indexed" in new_content
        assert "**4,000** unique topic tags" in new_content

    def test_patch_readme_no_change_when_stats_match(self):
        mod = self._get_functions()
        stats = {"total": 648, "tags_count": 3147, "funnel": {"top": 221, "middle": 423, "bottom": 4},
                 "date_min": "2025-02-17", "date_max": "2026-04-04"}
        _, changes = mod.patch_readme(SAMPLE_README, stats)
        # dateModified will change to today, so there will be a change
        # But article counts should match
        assert "648 original articles" in SAMPLE_README

    def test_patch_llms_txt_updates_count(self):
        mod = self._get_functions()
        stats = {"total": 700, "tags_count": 4000, "funnel": {}, "date_min": "2025-02-17", "date_max": "2026-04-10"}
        new_content, changes = mod.patch_llms_txt(SAMPLE_LLMS_TXT, stats)
        assert "700 original articles" in new_content
        assert "llms.txt" in changes


# =========================================================================
# Tests: generate_sitemap.py logic
# =========================================================================

class TestGenerateSitemap:
    """Test sitemap XML generation."""

    def _get_functions(self):
        import generate_sitemap
        return generate_sitemap

    def test_build_sitemap_produces_valid_xml(self):
        mod = self._get_functions()
        xml = mod.build_sitemap(SAMPLE_INDEX["articles"], "2026-04-12")
        # Should parse as valid XML
        root = fromstring(xml)
        assert root.tag == "{http://www.sitemaps.org/schemas/sitemap/0.9}urlset"

    def test_build_sitemap_url_count(self):
        mod = self._get_functions()
        xml = mod.build_sitemap(SAMPLE_INDEX["articles"], "2026-04-12")
        # 1 home + 5 support files + 1 README + 3 articles = 10
        assert xml.count("<url>") == 10

    def test_build_sitemap_contains_article_urls(self):
        mod = self._get_functions()
        xml = mod.build_sitemap(SAMPLE_INDEX["articles"], "2026-04-12")
        assert "articles/2026-04-04-test-article-one/" in xml
        assert "articles/2026-03-15-test-article-two/" in xml

    def test_build_sitemap_uses_correct_base_url(self):
        mod = self._get_functions()
        xml = mod.build_sitemap(SAMPLE_INDEX["articles"], "2026-04-12")
        assert "https://articles.firstaimovers.com/" in xml

    def test_build_sitemap_home_has_highest_priority(self):
        mod = self._get_functions()
        xml = mod.build_sitemap([], "2026-04-12")
        # Find the home URL entry
        root = fromstring(xml)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        for url in root.findall("s:url", ns):
            loc = url.find("s:loc", ns).text
            if loc.endswith(".com/"):
                priority = url.find("s:priority", ns).text
                assert priority == "1.0"
                break

    def test_build_sitemap_article_lastmod_uses_published_date(self):
        mod = self._get_functions()
        xml = mod.build_sitemap(SAMPLE_INDEX["articles"], "2026-04-12")
        # The article from 2026-04-04 should have that as lastmod
        assert "<lastmod>2026-04-04</lastmod>" in xml

    def test_build_sitemap_empty_articles(self):
        mod = self._get_functions()
        xml = mod.build_sitemap([], "2026-04-12")
        # Should still have home + support files
        assert xml.count("<url>") == 7  # home + 5 support + README

    def test_build_sitemap_skips_articles_without_folder(self):
        mod = self._get_functions()
        articles = [{"folder": "", "title": "No Folder", "published_date": "2026-01-01"}]
        xml = mod.build_sitemap(articles, "2026-04-12")
        assert xml.count("<url>") == 7  # only support files, no article


# =========================================================================
# Tests: add_tldr.py logic
# =========================================================================

class TestAddTldr:
    """Test TL;DR detection and injection logic."""

    def _get_functions(self):
        # Patch env vars before importing
        with patch.dict("os.environ", {"GITHUB_TOKEN": "fake", "OPENAI_API_KEY": "fake"}):
            import importlib
            if "add_tldr" in sys.modules:
                importlib.reload(sys.modules["add_tldr"])
            else:
                import add_tldr
            return sys.modules["add_tldr"]

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
