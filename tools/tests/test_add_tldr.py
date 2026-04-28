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

from _fixtures import *

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


