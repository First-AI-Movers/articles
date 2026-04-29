#!/usr/bin/env python3
"""Contract tests for tools/readability.py"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
READABILITY = REPO_ROOT / "tools" / "readability.py"


def _run_readability(*extra_args, cwd=REPO_ROOT):
    result = subprocess.run(
        [sys.executable, str(READABILITY), *extra_args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result


class TestStripFrontMatter:
    def test_front_matter_removed(self):
        from tools.readability import _strip_front_matter

        text = "---\ntitle: Foo\n---\n\nBody here."
        assert _strip_front_matter(text) == "Body here."

    def test_no_front_matter_unchanged(self):
        from tools.readability import _strip_front_matter

        text = "# Title\n\nBody here."
        assert _strip_front_matter(text) == text


class TestStripMarkdown:
    def test_code_blocks_removed(self):
        from tools.readability import _strip_markdown

        text = "Some text.\n\n```python\nprint(1)\n```\n\nMore text."
        stripped = _strip_markdown(text)
        assert "print" not in stripped
        assert "More text" in stripped

    def test_inline_code_removed(self):
        from tools.readability import _strip_markdown

        text = "Use `pip install` to get started."
        stripped = _strip_markdown(text)
        assert "pip install" not in stripped
        assert "Use" in stripped
        assert "to get started" in stripped

    def test_links_keep_text(self):
        from tools.readability import _strip_markdown

        text = "See [the guide](https://example.com/guide) for details."
        stripped = _strip_markdown(text)
        assert "the guide" in stripped
        assert "example.com" not in stripped

    def test_bare_urls_removed(self):
        from tools.readability import _strip_markdown

        text = "Visit https://example.com for more."
        stripped = _strip_markdown(text)
        assert "example.com" not in stripped

    def test_headings_keep_text(self):
        from tools.readability import _strip_markdown

        text = "## Section Title\n\nParagraph."
        stripped = _strip_markdown(text)
        assert "Section Title" in stripped
        assert "##" not in stripped

    def test_bold_italic_removed(self):
        from tools.readability import _strip_markdown

        text = "This is **bold** and *italic* and __also bold__ and _also italic_."
        stripped = _strip_markdown(text)
        assert "bold" in stripped
        assert "italic" in stripped
        assert "**" not in stripped
        assert "*" not in stripped
        assert "__" not in stripped

    def test_blockquote_removed(self):
        from tools.readability import _strip_markdown

        text = "> This is a quote.\n\nNormal text."
        stripped = _strip_markdown(text)
        assert "This is a quote" in stripped
        assert ">" not in stripped

    def test_list_markers_removed(self):
        from tools.readability import _strip_markdown

        text = "- First item\n- Second item\n1. Numbered item"
        stripped = _strip_markdown(text)
        assert "First item" in stripped
        assert "Second item" in stripped
        assert "Numbered item" in stripped
        assert "- First" not in stripped


class TestSyllableCounter:
    def test_simple_words(self):
        from tools.readability import _count_syllables

        assert _count_syllables("cat") == 1
        assert _count_syllables("dog") == 1
        assert _count_syllables("hello") == 2
        assert _count_syllables("beautiful") == 3

    def test_silent_e(self):
        from tools.readability import _count_syllables

        assert _count_syllables("make") == 1
        assert _count_syllables("rate") == 1

    def test_le_words(self):
        from tools.readability import _count_syllables

        assert _count_syllables("candle") == 2
        assert _count_syllables("table") == 2

    def test_empty_returns_one(self):
        from tools.readability import _count_syllables

        assert _count_syllables("a") == 1
        assert _count_syllables("I") == 1


class TestAnalyzeText:
    def test_basic_metrics(self):
        from tools.readability import _analyze_text

        text = "The cat sat on the mat. It was a sunny day."
        result = _analyze_text(text)
        assert result["word_count"] == 11
        assert result["sentence_count"] == 2
        assert result["avg_sentence_length"] == 5.5
        assert result["flesch_reading_ease"] > 0
        # Very short simple text can yield negative grade; assert it is computed
        assert isinstance(result["flesch_kincaid_grade"], float)

    def test_longer_text(self):
        from tools.readability import _analyze_text

        text = (
            "Artificial intelligence is transforming how businesses operate. "
            "Companies are investing heavily in new technologies. "
            "The pace of change is accelerating every year."
        )
        result = _analyze_text(text)
        assert result["word_count"] > 10
        assert result["sentence_count"] == 3
        assert result["avg_sentence_length"] > 5


class TestScoreArticle:
    def test_score_article_shape(self, tmp_path):
        from tools.readability import _score_article

        article_dir = tmp_path / "2024-01-01-test"
        article_dir.mkdir()
        body = "---\ntitle: Test\n---\n\n# Hello\n\nThis is a test article. It has two sentences."
        meta = {"title": "Test", "slug": "test", "published_date": "2024-01-01"}
        result = _score_article(article_dir, body, meta)
        assert result["folder"] == article_dir.name
        assert result["slug"] == "test"
        assert result["title"] == "Test"
        assert "word_count" in result
        assert "sentence_count" in result
        assert "flesch_reading_ease" in result
        assert "flesch_kincaid_grade" in result


class TestCli:
    def test_default_runs_and_exits_zero(self):
        result = _run_readability()
        assert result.returncode == 0
        assert "articles audited" in result.stdout

    def test_json_report_generated(self, tmp_path):
        json_out = tmp_path / "report.json"
        md_out = tmp_path / "report.md"
        result = _run_readability(
            "--json-out", str(json_out), "--md-out", str(md_out)
        )
        assert result.returncode == 0
        assert json_out.exists()
        assert md_out.exists()
        data = json.loads(json_out.read_text(encoding="utf-8"))
        assert "generated_at" in data
        assert "article_count" in data
        assert "summary" in data
        assert "articles" in data

    def test_markdown_report_has_summary(self, tmp_path):
        json_out = tmp_path / "report.json"
        md_out = tmp_path / "report.md"
        result = _run_readability(
            "--json-out", str(json_out), "--md-out", str(md_out)
        )
        assert result.returncode == 0
        md_text = md_out.read_text(encoding="utf-8")
        assert "# Readability Report" in md_text
        assert "Executive Summary" in md_text
        assert "Hardest-to-Read" in md_text

    def test_fail_on_threshold_exits_nonzero_when_breached(self, tmp_path):
        # Use extremely strict thresholds that will definitely trigger
        result = _run_readability(
            "--min-reading-ease", "100",
            "--max-grade", "0",
            "--fail-on-threshold",
        )
        assert result.returncode == 1
        assert "FAIL" in result.stderr

    def test_fail_on_threshold_exits_zero_when_not_breached(self, tmp_path):
        # Use an empty articles dir so no articles breach thresholds
        articles_dir = tmp_path / "empty_articles"
        articles_dir.mkdir()
        result = _run_readability(
            "--articles-dir", str(articles_dir),
            "--min-reading-ease", "0",
            "--max-grade", "100",
            "--fail-on-threshold",
        )
        assert result.returncode == 0

    def test_no_article_dir_exits_error(self, tmp_path):
        result = _run_readability(
            "--articles-dir", str(tmp_path / "nonexistent"),
        )
        assert result.returncode == 1
        assert "ERROR" in result.stderr
