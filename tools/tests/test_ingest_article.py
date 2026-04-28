import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
INGEST_SCRIPT = REPO_ROOT / "tools" / "ingest_article.py"
FIXTURE = REPO_ROOT / "tools" / "fixtures" / "external_article_payload.json"


def _run(args, cwd=None, extra_env=None):
    env = {**dict(__import__("os").environ), **(extra_env or {})}
    result = subprocess.run(
        [sys.executable, str(INGEST_SCRIPT)] + args,
        capture_output=True,
        text=True,
        cwd=cwd or str(REPO_ROOT),
        env=env,
    )
    return result


class TestIngestArticleCLI:
    def test_dry_run_with_fixture_writes_nothing(self, tmp_path):
        articles_dir = tmp_path / "articles"
        result = _run(["--payload-file", str(FIXTURE), "--dry-run", "--articles-dir", str(articles_dir)], cwd=str(tmp_path))
        assert result.returncode == 0
        assert "would create" in result.stdout
        # Nothing should be written in tmp_path
        assert not articles_dir.exists() or list(articles_dir.glob("*")) == []

    def test_write_creates_article_and_metadata(self, tmp_path):
        articles_dir = tmp_path / "articles"
        result = _run(["--payload-file", str(FIXTURE), "--write", "--articles-dir", str(articles_dir)], cwd=str(tmp_path))
        assert result.returncode == 0, result.stderr
        assert "created" in result.stdout

        article_dir = articles_dir / "2026-04-28-synthetic-external-article-test"
        assert article_dir.exists()

        article_md = article_dir / "article.md"
        assert article_md.exists()
        text = article_md.read_text(encoding="utf-8")
        assert "Synthetic External Article" in text
        assert "---" in text
        assert "canonical_url" in text

        metadata_json = article_dir / "metadata.json"
        assert metadata_json.exists()
        meta = json.loads(metadata_json.read_text(encoding="utf-8"))
        assert meta["title"] == "Synthetic External Article for Testing Ingestion"
        assert meta["slug"] == "synthetic-external-article-test"
        assert meta["folder"] == "2026-04-28-synthetic-external-article-test"
        assert meta["canonical_url"] == "https://firstaimovers.com/synthetic-external-article-test"
        assert meta["tags"] == ["AI strategy", "testing", "European SME"]
        assert meta["status"] == "published"
        assert meta["topics"] == []

    def test_rejects_missing_required_fields(self, tmp_path):
        articles_dir = tmp_path / "articles"
        payload = {
            "slug": "missing-title",
            "published_date": "2026-04-28",
            "canonical_url": "https://example.com/test",
            "article_markdown": "Body",
        }
        payload_file = tmp_path / "payload.json"
        payload_file.write_text(json.dumps(payload), encoding="utf-8")

        result = _run(["--payload-file", str(payload_file), "--write", "--articles-dir", str(articles_dir)], cwd=str(tmp_path))
        assert result.returncode != 0
        assert "Missing required field: title" in result.stderr

    def test_rejects_duplicate_title(self, tmp_path):
        articles_dir = tmp_path / "articles"
        # First write
        result = _run(["--payload-file", str(FIXTURE), "--write", "--articles-dir", str(articles_dir)], cwd=str(tmp_path))
        assert result.returncode == 0

        # Second write with same title but different slug
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["slug"] = "different-slug"
        payload_file = tmp_path / "payload2.json"
        payload_file.write_text(json.dumps(payload), encoding="utf-8")

        result = _run(["--payload-file", str(payload_file), "--write", "--articles-dir", str(articles_dir)], cwd=str(tmp_path))
        assert result.returncode == 0  # script exits 0 but reports skip
        assert "skip" in result.stdout
        assert "duplicate title" in result.stdout or "already exists" in result.stdout

    def test_rejects_existing_folder(self, tmp_path):
        articles_dir = tmp_path / "articles"
        # First write
        result = _run(["--payload-file", str(FIXTURE), "--write", "--articles-dir", str(articles_dir)], cwd=str(tmp_path))
        assert result.returncode == 0

        # Second write with same payload
        result = _run(["--payload-file", str(FIXTURE), "--write", "--articles-dir", str(articles_dir)], cwd=str(tmp_path))
        assert result.returncode == 0
        assert "skip" in result.stdout
        assert "already exists" in result.stdout

    def test_date_normalization(self, tmp_path):
        articles_dir = tmp_path / "articles"
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["published_date"] = "2026-04-28T00:00:00.000Z"
        payload["slug"] = "date-normalization-test"
        payload_file = tmp_path / "payload.json"
        payload_file.write_text(json.dumps(payload), encoding="utf-8")

        result = _run(["--payload-file", str(payload_file), "--write", "--articles-dir", str(articles_dir)], cwd=str(tmp_path))
        assert result.returncode == 0

        article_dir = articles_dir / "2026-04-28-date-normalization-test"
        assert article_dir.exists()

    def test_stdin_payload(self, tmp_path):
        articles_dir = tmp_path / "articles"
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["slug"] = "stdin-test"
        raw = json.dumps(payload)

        result = subprocess.run(
            [sys.executable, str(INGEST_SCRIPT), "--dry-run", "--articles-dir", str(articles_dir)],
            input=raw,
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        assert result.returncode == 0
        assert "would create" in result.stdout
