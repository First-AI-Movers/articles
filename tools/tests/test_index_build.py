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


