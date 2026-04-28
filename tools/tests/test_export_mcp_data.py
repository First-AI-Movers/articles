#!/usr/bin/env python3
"""Contract tests for export_mcp_data.py."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import export_mcp_data as emd


class TestStripFrontMatter:
    def test_removes_yaml_front_matter(self):
        text = "---\ntitle: Foo\n---\n# Body\n"
        assert emd._strip_front_matter(text) == "# Body"

    def test_returns_plain_text_unchanged(self):
        text = "# No front matter\nBody here.\n"
        assert emd._strip_front_matter(text) == "# No front matter\nBody here."

    def test_handles_missing_closing_delimiter(self):
        text = "---\ntitle: Foo\n# Body\n"
        assert emd._strip_front_matter(text) == text.strip()


class TestExtractTldr:
    def test_extracts_tldr_blockquote(self):
        body = "> **TL;DR** This is the summary.\n\n# Heading\n"
        assert emd._extract_tldr(body) == "This is the summary."

    def test_extracts_tldr_with_colon(self):
        body = "> **TL;DR:** This is the summary.\n\n# Heading\n"
        assert emd._extract_tldr(body) == "This is the summary."

    def test_extracts_key_takeaway(self):
        body = "> Key takeaway: Focus on governance.\n\n# Heading\n"
        assert emd._extract_tldr(body) == "Focus on governance."

    def test_extracts_summary(self):
        body = "> Summary: AI strategy matters.\n\n# Heading\n"
        assert emd._extract_tldr(body) == "AI strategy matters."

    def test_returns_empty_when_no_match(self):
        body = "# Heading\nNo blockquote here.\n"
        assert emd._extract_tldr(body) == ""

    def test_joins_multiline_blockquote(self):
        body = "> **TL;DR** Line one.\n> Line two.\n\n# Heading\n"
        assert emd._extract_tldr(body) == "Line one.  Line two."


class TestBuildExcerpt:
    def test_truncates_to_max_chars(self):
        body = "A" * 1000
        excerpt = emd._build_excerpt(body)
        assert len(excerpt) == emd.MAX_EXCERPT_CHARS
        assert excerpt == "A" * emd.MAX_EXCERPT_CHARS

    def test_preserves_short_text(self):
        body = "Short text."
        assert emd._build_excerpt(body) == "Short text."

    def test_replaces_newlines(self):
        body = "Line one.\nLine two.\n"
        assert emd._build_excerpt(body) == "Line one. Line two."


class TestExportData:
    def test_export_data_creates_files(self, tmp_path: Path):
        index = {
            "articles": [
                {
                    "folder": "2026-04-01-test-article",
                    "slug": "test-article",
                    "title": "Test Article",
                    "published_date": "2026-04-01",
                    "canonical_url": "https://example.com/test",
                    "topics": ["AI strategy"],
                }
            ]
        }
        # Create a fake article markdown file
        articles_dir = tmp_path / "articles" / "2026-04-01-test-article"
        articles_dir.mkdir(parents=True)
        (articles_dir / "article.md").write_text(
            "---\ntitle: Test\n---\n# Test Article\n\nBody text here.\n", encoding="utf-8"
        )

        index_path = tmp_path / "index.json"
        index_path.write_text(json.dumps(index), encoding="utf-8")

        out_dir = tmp_path / "generated"

        with patch.object(emd, "REPO_ROOT", tmp_path):
            with patch.object(emd, "INDEX_PATH", index_path):
                with patch.object(emd, "EMBEDDINGS_PATH", tmp_path / "embeddings.parquet"):
                    rc = emd.export_data(out_dir, check_mode=False)

        assert rc == 0
        archive_path = out_dir / "archive-data.json"
        assert archive_path.exists()
        data = json.loads(archive_path.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["slug"] == "test-article"
        assert data[0]["title"] == "Test Article"
        assert data[0]["local_url"] == "/articles/test-article/"
        assert data[0]["summary"] == ""
        assert "Body text here." in data[0]["excerpt"]

    def test_export_data_check_mode_detects_stale(self, tmp_path: Path):
        index = {
            "articles": [
                {
                    "folder": "2026-04-01-test-article",
                    "slug": "test-article",
                    "title": "Test Article",
                    "published_date": "2026-04-01",
                    "canonical_url": "https://example.com/test",
                    "topics": ["AI strategy"],
                }
            ]
        }
        articles_dir = tmp_path / "articles" / "2026-04-01-test-article"
        articles_dir.mkdir(parents=True)
        (articles_dir / "article.md").write_text(
            "---\ntitle: Test\n---\n# Test Article\n\nBody text here.\n", encoding="utf-8"
        )

        index_path = tmp_path / "index.json"
        index_path.write_text(json.dumps(index), encoding="utf-8")

        out_dir = tmp_path / "generated"

        with patch.object(emd, "REPO_ROOT", tmp_path):
            with patch.object(emd, "INDEX_PATH", index_path):
                with patch.object(emd, "EMBEDDINGS_PATH", tmp_path / "embeddings.parquet"):
                    # First run: create files
                    rc = emd.export_data(out_dir, check_mode=False)
                    assert rc == 0
                    # Second run: check should pass
                    rc = emd.export_data(out_dir, check_mode=True)
                    assert rc == 0
                    # Modify index and check should fail
                    index["articles"][0]["title"] = "Modified Title"
                    index_path.write_text(json.dumps(index), encoding="utf-8")
                    rc = emd.export_data(out_dir, check_mode=True)
                    assert rc == 1

    def test_export_data_missing_index(self, tmp_path: Path):
        out_dir = tmp_path / "generated"
        with patch.object(emd, "REPO_ROOT", tmp_path):
            with patch.object(emd, "INDEX_PATH", tmp_path / "nonexistent.json"):
                with patch.object(emd, "EMBEDDINGS_PATH", tmp_path / "embeddings.parquet"):
                    rc = emd.export_data(out_dir, check_mode=False)
        assert rc == 1
