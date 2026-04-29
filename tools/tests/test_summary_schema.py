#!/usr/bin/env python3
"""Tests for E35 summary schema validation."""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTICLE_SCHEMA = REPO_ROOT / "tools" / "article_schema.json"


class TestSummarySchema:
    def test_schema_allows_optional_summary_fields(self):
        schema = json.loads(ARTICLE_SCHEMA.read_text(encoding="utf-8"))
        assert "summary_short" in schema["properties"]
        assert "summary_medium" in schema["properties"]
        assert "summary_long" in schema["properties"]
        assert schema["properties"]["summary_short"]["type"] == "string"
        assert schema["properties"]["summary_medium"]["type"] == "string"
        assert schema["properties"]["summary_long"]["type"] == "string"

    def test_schema_rejects_non_string_summary_fields(self):
        schema = json.loads(ARTICLE_SCHEMA.read_text(encoding="utf-8"))
        for key in ("summary_short", "summary_medium", "summary_long"):
            assert schema["properties"][key]["type"] != "integer"
            assert schema["properties"][key]["type"] != "boolean"

    def test_schema_allows_summary_reviewed_at_date(self):
        schema = json.loads(ARTICLE_SCHEMA.read_text(encoding="utf-8"))
        assert "summary_reviewed_at" in schema["properties"]
        assert schema["properties"]["summary_reviewed_at"]["type"] == "string"
        pattern = schema["properties"]["summary_reviewed_at"]["pattern"]
        assert re.match(pattern, "2026-04-29")
        assert not re.match(pattern, "not-a-date")

    def test_schema_allows_summary_model_string(self):
        schema = json.loads(ARTICLE_SCHEMA.read_text(encoding="utf-8"))
        assert "summary_model" in schema["properties"]
        assert schema["properties"]["summary_model"]["type"] == "string"

    def test_summary_fields_are_not_required(self):
        schema = json.loads(ARTICLE_SCHEMA.read_text(encoding="utf-8"))
        required = schema.get("required", [])
        for key in ("summary_short", "summary_medium", "summary_long", "summary_reviewed_at", "summary_model"):
            assert key not in required


import re
