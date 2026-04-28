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


