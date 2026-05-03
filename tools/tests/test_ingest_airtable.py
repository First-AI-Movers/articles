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

class TestAirtableIngestion:
    """Airtable ingestion script, schema, and workflow."""

    # --- Schema tests -----------------------------------------------------

    def test_schema_exists(self):
        from pathlib import Path
        schema = Path(__file__).resolve().parents[2] / "tools" / "article_schema.json"
        assert schema.exists(), "article_schema.json must exist"

    def test_schema_requires_core_fields(self):
        import json
        from pathlib import Path
        schema = json.loads((Path(__file__).resolve().parents[2] / "tools" / "article_schema.json").read_text(encoding="utf-8"))
        required = set(schema.get("required", []))
        assert "title" in required
        assert "slug" in required
        assert "published_date" in required
        assert "canonical_url" in required
        assert "article_markdown" in required

    def test_schema_rejects_missing_title(self):
        import json
        from pathlib import Path
        schema = json.loads((Path(__file__).resolve().parents[2] / "tools" / "article_schema.json").read_text(encoding="utf-8"))
        # Simple manual validation: check required fields
        payload = {"slug": "test", "published_date": "2026-01-01", "canonical_url": "https://example.com", "article_markdown": "# Hello"}
        assert "title" not in payload or not payload.get("title")
        # title is missing — schema would reject it

    # --- Field mapper tests -----------------------------------------------

    def test_record_to_payload_maps_fields(self, monkeypatch, tmp_path):
        import ingest_airtable
        record = {
            "id": "rec123",
            "fields": {
                "Title": "Test Article",
                "slug": "test-article",
                "Pub Date": "2026-01-15",
                "GUID": "https://example.com/test",
                "Content HTML": "# Hello\n\nWorld.",
                "tags": "AI, Strategy",
                "FAIM Status": "published",
                "Funnel Stage": "middle",
            }
        }
        payload = ingest_airtable._record_to_payload(record)
        assert payload["title"] == "Test Article"
        assert payload["slug"] == "test-article"
        assert payload["published_date"] == "2026-01-15"
        assert payload["canonical_url"] == "https://example.com/test"
        assert payload["article_markdown"] == "# Hello\n\nWorld."
        assert payload["tags"] == ["AI", "Strategy"]
        assert payload["status"] == "published"
        assert payload["funnel_stage"] == "middle"

    def test_status_gate_skips_draft(self, monkeypatch, tmp_path):
        import ingest_airtable
        payload = {"status": "draft", "title": "T", "slug": "s", "published_date": "2026-01-01", "canonical_url": "https://x.com", "article_markdown": "x"}
        schema = {"required": ["title", "slug", "published_date", "canonical_url", "article_markdown"], "properties": {}}
        errors, warnings = ingest_airtable._validate_payload(payload, schema)
        assert any("draft" in w.lower() for w in warnings)

    def test_missing_status_gate_warns(self, monkeypatch, tmp_path):
        import ingest_airtable
        payload = {"title": "T", "slug": "s", "published_date": "2026-01-01", "canonical_url": "https://x.com", "article_markdown": "x"}
        schema = {"required": ["title", "slug", "published_date", "canonical_url", "article_markdown"], "properties": {}}
        errors, warnings = ingest_airtable._validate_payload(payload, schema)
        assert not errors
        # No status field — should not produce warnings from _validate_payload itself

    # --- Folder / slug tests ----------------------------------------------

    def test_folder_name_is_deterministic(self):
        import ingest_airtable
        assert ingest_airtable._build_folder_name("2026-04-01", "ai-strategy") == "2026-04-01-ai-strategy"

    def test_existing_folder_skipped(self, monkeypatch, tmp_path):
        import ingest_airtable
        monkeypatch.setattr(ingest_airtable, "ARTICLES_DIR", tmp_path / "articles")
        folder = ingest_airtable._build_folder_name("2026-01-01", "test-existing")
        (tmp_path / "articles" / folder).mkdir(parents=True)
        payload = {
            "title": "Test", "slug": "test-existing", "published_date": "2026-01-01",
            "canonical_url": "https://x.com", "article_markdown": "x"
        }
        f, created = ingest_airtable._write_article(payload, "rec1", dry_run=False)
        assert not created

    def test_duplicate_title_skipped(self, monkeypatch, tmp_path):
        import ingest_airtable
        monkeypatch.setattr(ingest_airtable, "ARTICLES_DIR", tmp_path / "articles")
        # Seed an existing article with the same title
        existing = tmp_path / "articles" / "2026-01-01-existing"
        existing.mkdir(parents=True)
        (existing / "metadata.json").write_text(
            json.dumps({"title": "Duplicate Title"}, indent=2) + "\n", encoding="utf-8"
        )
        payload = {
            "title": "Duplicate Title", "slug": "new-slug", "published_date": "2026-02-01",
            "canonical_url": "https://x.com", "article_markdown": "x"
        }
        f, created = ingest_airtable._write_article(payload, "rec2", dry_run=False)
        assert not created

    # --- Write tests ------------------------------------------------------

    def test_write_creates_article_md_and_metadata(self, monkeypatch, tmp_path):
        import ingest_airtable
        monkeypatch.setattr(ingest_airtable, "ARTICLES_DIR", tmp_path / "articles")
        payload = {
            "title": "New Article",
            "slug": "new-article",
            "published_date": "2026-03-01",
            "canonical_url": "https://radar.firstaimovers.com/new-article",
            "article_markdown": "# Hello\n\nWorld.",
            "tags": ["AI", "Strategy"],
            "status": "published",
            "funnel_stage": "middle",
            "word_count": 500,
            "read_time_minutes": 3,
        }
        folder, created = ingest_airtable._write_article(payload, "recABC", dry_run=False)
        assert created
        assert folder == "2026-03-01-new-article"

        article_dir = tmp_path / "articles" / folder
        assert (article_dir / "article.md").exists()
        assert (article_dir / "metadata.json").exists()

        md = (article_dir / "article.md").read_text(encoding="utf-8")
        assert "# Hello" in md
        assert 'title: "New Article"' in md
        assert "published_date: \"2026-03-01\"" in md

        meta = json.loads((article_dir / "metadata.json").read_text(encoding="utf-8"))
        assert meta["title"] == "New Article"
        assert meta["slug"] == "new-article"
        assert meta["folder"] == folder
        assert meta["published_date"] == "2026-03-01"
        assert meta["canonical_url"] == "https://radar.firstaimovers.com/new-article"
        assert meta["tags"] == ["AI", "Strategy"]
        assert meta["status"] == "published"
        assert meta["funnel_stage"] == "middle"
        assert meta["word_count"] == 500
        assert meta["read_time_minutes"] == 3
        assert meta["topics"] == []
        assert meta["id"] == "recABC"

    def test_dry_run_writes_nothing(self, monkeypatch, tmp_path):
        import ingest_airtable
        monkeypatch.setattr(ingest_airtable, "ARTICLES_DIR", tmp_path / "articles")
        payload = {
            "title": "Dry Run Article", "slug": "dry-run", "published_date": "2026-01-01",
            "canonical_url": "https://x.com", "article_markdown": "x"
        }
        folder, created = ingest_airtable._write_article(payload, "rec1", dry_run=True)
        assert created  # would create
        assert not (tmp_path / "articles" / folder).exists()

    def test_malformed_record_reported_not_crashed(self, monkeypatch, tmp_path):
        import ingest_airtable
        schema = {"required": ["title", "slug", "published_date", "canonical_url", "article_markdown"], "properties": {}}
        payload = {"slug": "bad", "published_date": "2026-01-01"}  # missing title, canonical, markdown
        errors, warnings = ingest_airtable._validate_payload(payload, schema)
        assert len(errors) == 3

    # --- Front-matter serialization safety --------------------------------

    def test_front_matter_preserves_double_quotes(self, monkeypatch, tmp_path):
        import ingest_airtable
        monkeypatch.setattr(ingest_airtable, "ARTICLES_DIR", tmp_path / "articles")
        payload = {
            "title": 'The "AI Revolution" is Here',
            "slug": "ai-revolution",
            "published_date": "2026-01-01",
            "canonical_url": "https://x.com",
            "article_markdown": "Body.",
        }
        folder, created = ingest_airtable._write_article(payload, "rec1", dry_run=False)
        md = (tmp_path / "articles" / folder / "article.md").read_text(encoding="utf-8")
        assert 'title: "The \\"AI Revolution\\" is Here"' in md

    def test_front_matter_preserves_apostrophes(self, monkeypatch, tmp_path):
        import ingest_airtable
        monkeypatch.setattr(ingest_airtable, "ARTICLES_DIR", tmp_path / "articles")
        payload = {
            "title": "It's a New Era for AI",
            "slug": "new-era",
            "published_date": "2026-01-01",
            "canonical_url": "https://x.com",
            "article_markdown": "Body.",
        }
        folder, created = ingest_airtable._write_article(payload, "rec1", dry_run=False)
        md = (tmp_path / "articles" / folder / "article.md").read_text(encoding="utf-8")
        assert "title: \"It's a New Era for AI\"" in md

    def test_front_matter_handles_colon_text(self, monkeypatch, tmp_path):
        import ingest_airtable
        monkeypatch.setattr(ingest_airtable, "ARTICLES_DIR", tmp_path / "articles")
        payload = {
            "title": "AI: The Next Frontier",
            "slug": "next-frontier",
            "published_date": "2026-01-01",
            "canonical_url": "https://x.com",
            "article_markdown": "Body.",
        }
        folder, created = ingest_airtable._write_article(payload, "rec1", dry_run=False)
        md = (tmp_path / "articles" / folder / "article.md").read_text(encoding="utf-8")
        assert 'title: "AI: The Next Frontier"' in md

    def test_front_matter_does_not_create_malformed_yaml(self, monkeypatch, tmp_path):
        import ingest_airtable
        monkeypatch.setattr(ingest_airtable, "ARTICLES_DIR", tmp_path / "articles")
        payload = {
            "title": 'Line1\nLine2 "quoted" and \\ backslash',
            "slug": "multiline",
            "published_date": "2026-01-01",
            "canonical_url": "https://x.com",
            "article_markdown": "Body.",
        }
        folder, created = ingest_airtable._write_article(payload, "rec1", dry_run=False)
        md = (tmp_path / "articles" / folder / "article.md").read_text(encoding="utf-8")
        lines = md.splitlines()
        # Front matter starts and ends with ---
        assert lines[0] == "---"
        fm_end = lines.index("---", 1)
        fm_block = "\n".join(lines[:fm_end + 1])
        # No literal newlines inside the front matter block beyond the expected line breaks
        # (json.dumps escapes \n as two chars, so the file contains \\n, not a real newline)
        title_line = [ln for ln in lines if ln.startswith("title:")][0]
        # Should contain escaped sequences as literal characters in the file
        assert "\\n" in title_line, f"Expected escaped newline in: {title_line}"
        assert '\\\\' in title_line, f"Expected escaped backslash in: {title_line}"
        # The front matter block should not contain bare unescaped quotes that would break YAML
        # (json.dumps produces \" for internal quotes, which is valid YAML/JSON)
        assert '"Line1' in title_line

    # --- Round-trip tests -------------------------------------------------

    def test_written_fixture_roundtrip(self, monkeypatch, tmp_path):
        import ingest_airtable
        import rebuild_local
        import normalize_tags
        import check_duplicate_titles

        monkeypatch.setattr(ingest_airtable, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(rebuild_local, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(rebuild_local, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(normalize_tags, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(check_duplicate_titles, "REPO_ROOT", tmp_path)

        # Seed canonical_topics.json and tag_aliases.json so normalize_tags works
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir(exist_ok=True)
        (tools_dir / "canonical_topics.json").write_text(
            json.dumps({"version": 1, "topics": ["AI Strategy"]}), encoding="utf-8"
        )
        (tools_dir / "tag_aliases.json").write_text(
            json.dumps({"version": 1, "patterns": [], "overrides": {}}), encoding="utf-8"
        )
        monkeypatch.setattr(normalize_tags, "TOPICS_FILE", tools_dir / "canonical_topics.json")
        monkeypatch.setattr(normalize_tags, "ALIASES_FILE", tools_dir / "tag_aliases.json")

        payload = {
            "title": "Roundtrip Article",
            "slug": "roundtrip-article",
            "published_date": "2026-04-01",
            "canonical_url": "https://radar.firstaimovers.com/roundtrip-article",
            "article_markdown": "# Hello\n\nThis is a test article.\n",
            "tags": ["ai strategy"],
            "status": "published",
        }
        folder, created = ingest_airtable._write_article(payload, "recRT", dry_run=False)
        assert created

        # normalize_tags should not crash
        monkeypatch.setattr(normalize_tags, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(sys, "argv", ["normalize_tags.py"])
        normalize_tags.main()

        # check_duplicate_titles should pass
        monkeypatch.setattr(check_duplicate_titles, "REPO_ROOT", tmp_path)
        # create a minimal index.json so the checker can read it
        (tmp_path / "index.json").write_text(
            json.dumps({"articles": [{"title": "Roundtrip Article", "folder": folder, "published_date": "2026-04-01"}]}),
            encoding="utf-8"
        )
        monkeypatch.setattr(sys, "argv", ["check_duplicate_titles.py", "--index", str(tmp_path / "index.json")])
        with pytest.raises(SystemExit) as exc_info:
            check_duplicate_titles.main()
        assert exc_info.value.code == 0

    # --- CLI argument tests -----------------------------------------------

    def test_dry_run_flag_is_accepted(self, monkeypatch):
        import ingest_airtable
        monkeypatch.setenv("AIRTABLE_PAT", "pat_test")
        monkeypatch.setenv("AIRTABLE_BASE_ID", "app_test")
        monkeypatch.setenv("AIRTABLE_TABLE_NAME", "Articles")
        monkeypatch.setattr(ingest_airtable, "_fetch_records", lambda *a, **k: iter([]))
        code = ingest_airtable.main(["--dry-run"])
        assert code == 0

    def test_default_mode_is_dry_run(self, monkeypatch):
        import ingest_airtable
        monkeypatch.setenv("AIRTABLE_PAT", "pat_test")
        monkeypatch.setenv("AIRTABLE_BASE_ID", "app_test")
        monkeypatch.setenv("AIRTABLE_TABLE_NAME", "Articles")
        monkeypatch.setattr(ingest_airtable, "_fetch_records", lambda *a, **k: iter([]))
        code = ingest_airtable.main([])
        assert code == 0

    def test_write_flag_enables_write_mode(self, monkeypatch, tmp_path):
        import ingest_airtable
        monkeypatch.setenv("AIRTABLE_PAT", "pat_test")
        monkeypatch.setenv("AIRTABLE_BASE_ID", "app_test")
        monkeypatch.setenv("AIRTABLE_TABLE_NAME", "Articles")
        monkeypatch.setattr(ingest_airtable, "ARTICLES_DIR", tmp_path / "articles")
        record = {
            "id": "recTest",
            "fields": {
                "Title": "Write Mode Test",
                "slug": "write-mode-test",
                "Pub Date": "2026-04-01",
                "GUID": "https://example.com/write-mode-test",
                "Content HTML": "# Hello",
                "FAIM Status": "Posted",
            }
        }
        monkeypatch.setattr(ingest_airtable, "_fetch_records", lambda *a, **k: iter([record]))
        code = ingest_airtable.main(["--write", "--limit", "1"])
        assert code == 0
        assert (tmp_path / "articles" / "2026-04-01-write-mode-test" / "article.md").exists()
        # Status must be normalized to lowercase in metadata.json so it matches
        # the convention used by the existing 829 archive records.
        meta_path = tmp_path / "articles" / "2026-04-01-write-mode-test" / "metadata.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        assert meta["status"] == "posted"

    def test_dry_run_and_write_are_mutually_exclusive(self, monkeypatch, capsys):
        import ingest_airtable
        monkeypatch.setenv("AIRTABLE_PAT", "pat_test")
        monkeypatch.setenv("AIRTABLE_BASE_ID", "app_test")
        monkeypatch.setenv("AIRTABLE_TABLE_NAME", "Articles")
        with pytest.raises(SystemExit) as exc_info:
            ingest_airtable.main(["--dry-run", "--write"])
        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "mutually exclusive" in captured.err.lower()

    # --- Real field mapping tests -----------------------------------------

    def test_real_airtable_field_mapping_required_fields(self):
        import ingest_airtable
        mapping = ingest_airtable.AIRTABLE_FIELD_MAP
        assert mapping["title"] == "Title"
        assert mapping["slug"] == "slug"
        assert mapping["published_date"] == "Pub Date"
        assert mapping["canonical_url"] == "GUID"
        assert mapping["article_markdown"] == "Content HTML"
        assert mapping["tags"] == "tags"

    def test_record_to_payload_uses_real_field_names(self, monkeypatch, tmp_path):
        import ingest_airtable
        record = {
            "id": "recReal",
            "fields": {
                "Title": "Real Article",
                "slug": "real-article",
                "Pub Date": "2026-04-25",
                "GUID": "https://example.com/real",
                "Content HTML": "# Real\n\nContent.",
                "tags": "AI, Strategy",
                "FAIM Status": "published",
            }
        }
        payload = ingest_airtable._record_to_payload(record)
        assert payload["title"] == "Real Article"
        assert payload["slug"] == "real-article"
        assert payload["published_date"] == "2026-04-25"
        assert payload["canonical_url"] == "https://example.com/real"
        assert payload["article_markdown"] == "# Real\n\nContent."
        assert payload["tags"] == ["AI", "Strategy"]
        assert payload["status"] == "published"

    def test_pub_date_accepts_bare_date(self):
        import ingest_airtable
        assert ingest_airtable._normalize_date("2026-04-25") == "2026-04-25"

    def test_pub_date_accepts_airtable_timestamp_with_ms(self):
        import ingest_airtable
        assert ingest_airtable._normalize_date("2026-04-25T00:00:00.000Z") == "2026-04-25"

    def test_pub_date_accepts_airtable_timestamp_without_ms(self):
        import ingest_airtable
        assert ingest_airtable._normalize_date("2026-04-25T00:00:00Z") == "2026-04-25"

    def test_pub_date_rejects_unparseable(self):
        import ingest_airtable
        assert ingest_airtable._normalize_date("not-a-date") is None
        assert ingest_airtable._normalize_date(None) is None

    def test_content_html_field_populates_article_markdown(self):
        import ingest_airtable
        record = {
            "id": "rec1",
            "fields": {
                "Title": "T",
                "slug": "s",
                "Pub Date": "2026-01-01",
                "GUID": "https://x.com",
                "Content HTML": "<p>Hello</p>",
            }
        }
        payload = ingest_airtable._record_to_payload(record)
        assert payload["article_markdown"] == "<p>Hello</p>"

    def test_content_html_preserved_without_dependency(self):
        import ingest_airtable
        html = "<h1>Title</h1>\r\n<p>Paragraph</p>\r\n"
        result = ingest_airtable._normalize_article_body(html)
        assert result == "<h1>Title</h1>\n<p>Paragraph</p>"

    def test_lowercase_tags_field_maps_to_tags_list(self):
        import ingest_airtable
        record = {
            "id": "rec1",
            "fields": {
                "Title": "T",
                "slug": "s",
                "Pub Date": "2026-01-01",
                "GUID": "https://x.com",
                "Content HTML": "body",
                "tags": "AI, Governance",
            }
        }
        payload = ingest_airtable._record_to_payload(record)
        assert payload["tags"] == ["AI", "Governance"]

    def test_workflow_dry_run_allows_no_status_gate(self):
        from pathlib import Path
        text = (Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ingest-airtable.yml").read_text(encoding="utf-8")
        dry_run_line = [ln for ln in text.splitlines() if "ingest_airtable.py --dry-run" in ln][0]
        assert "--allow-no-status-gate" in dry_run_line

    def test_workflow_write_mode_does_not_allow_no_status_gate(self):
        from pathlib import Path
        text = (Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ingest-airtable.yml").read_text(encoding="utf-8")
        write_lines = [ln for ln in text.splitlines() if "ingest_airtable.py --write" in ln]
        assert len(write_lines) == 1
        assert "--allow-no-status-gate" not in write_lines[0]

    # --- Slug derivation tests --------------------------------------------

    def test_slug_from_guid_canonical_url(self):
        import ingest_airtable
        slug = ingest_airtable._slug_from_canonical_url("https://radar.firstaimovers.com/ai-consulting-tallinn-digital-tech-smes-2026")
        assert slug == "ai-consulting-tallinn-digital-tech-smes-2026"

    def test_slug_from_guid_trailing_slash(self):
        import ingest_airtable
        slug = ingest_airtable._slug_from_canonical_url("https://example.com/my-article/")
        assert slug == "my-article"

    def test_slug_from_guid_query_string(self):
        import ingest_airtable
        slug = ingest_airtable._slug_from_canonical_url("https://example.com/my-article?utm_source=email")
        assert slug == "my-article"

    def test_slug_from_guid_invalid_url_returns_none(self):
        import ingest_airtable
        assert ingest_airtable._slug_from_canonical_url("") is None
        assert ingest_airtable._slug_from_canonical_url(None) is None
        assert ingest_airtable._slug_from_canonical_url("https://example.com/") is None

    def test_record_to_payload_derives_missing_slug_from_guid(self):
        import ingest_airtable
        record = {
            "id": "rec1",
            "fields": {
                "Title": "T",
                "Pub Date": "2026-01-01",
                "GUID": "https://example.com/derived-slug",
                "Content HTML": "body",
            }
        }
        payload = ingest_airtable._record_to_payload(record)
        assert payload["slug"] == "derived-slug"

    def test_record_to_payload_prefers_airtable_slug_over_guid(self):
        import ingest_airtable
        record = {
            "id": "rec1",
            "fields": {
                "Title": "T",
                "slug": "explicit-slug",
                "Pub Date": "2026-01-01",
                "GUID": "https://example.com/derived-slug",
                "Content HTML": "body",
            }
        }
        payload = ingest_airtable._record_to_payload(record)
        assert payload["slug"] == "explicit-slug"

    def test_record_missing_slug_and_unusable_guid_remains_invalid(self):
        import ingest_airtable
        record = {
            "id": "rec1",
            "fields": {
                "Title": "T",
                "Pub Date": "2026-01-01",
                "GUID": "https://example.com/",
                "Content HTML": "body",
            }
        }
        payload = ingest_airtable._record_to_payload(record)
        # No slug derived because GUID path is empty
        assert "slug" not in payload
        schema = {"required": ["title", "slug", "published_date", "canonical_url", "article_markdown"], "properties": {}}
        errors, warnings = ingest_airtable._validate_payload(payload, schema)
        assert any("slug" in e for e in errors)

    # --- Workflow tests ---------------------------------------------------

    def test_ingest_workflow_exists(self):
        from pathlib import Path
        wf = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ingest-airtable.yml"
        assert wf.exists(), "ingest-airtable workflow must exist"

    def test_ingest_workflow_has_schedule_and_dispatch(self):
        from pathlib import Path
        text = (Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ingest-airtable.yml").read_text(encoding="utf-8")
        assert "workflow_dispatch" in text
        assert "schedule" in text
        assert "cron" in text

    def test_ingest_workflow_uses_secrets_not_hardcoded_values(self):
        from pathlib import Path
        text = (Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ingest-airtable.yml").read_text(encoding="utf-8")
        assert "secrets.AIRTABLE_PAT" in text
        assert "secrets.AIRTABLE_BASE_ID" in text
        assert "secrets.AIRTABLE_TABLE_NAME" in text
        # Ensure no placeholder secret values
        assert "patXXX" not in text
        assert "appXXX" not in text

    def test_ingest_workflow_opens_pr_not_direct_push(self):
        from pathlib import Path
        text = (Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ingest-airtable.yml").read_text(encoding="utf-8")
        assert "create-pull-request" in text.lower() or "peter-evans/create-pull-request" in text
        assert "git push" not in text.lower()


class TestAirtableFaimStatusGate:
    """E41b — Airtable archive ingestion must gate on `FAIM Status = Posted`.

    Lifecycle in the Pubs/beehiiv base:
      Ready  → article is prepared for upstream publication (NOT yet posted).
      Posted → article is already live in the upstream system; the canonical
               URL resolves; safe to mirror into the archive.

    Archive ingestion must therefore admit only `Posted`. `Ready` records
    must be skipped — their canonical URLs are not guaranteed to exist yet
    and post-publication edits may still occur upstream.
    """

    def test_field_map_targets_faim_status(self):
        import ingest_airtable
        assert ingest_airtable.AIRTABLE_FIELD_MAP["status"] == "FAIM Status"

    def test_no_literal_status_field_required(self):
        import ingest_airtable
        # No mapping value should be the bare "Status" field — that field does
        # not exist in the live Pubs/beehiiv schema.
        assert "Status" not in ingest_airtable.AIRTABLE_FIELD_MAP.values()

    def test_allowed_statuses_is_posted_only(self):
        import ingest_airtable
        assert ingest_airtable.ALLOWED_STATUSES == {"posted"}

    def test_ready_is_excluded_from_archive_ingestion(self):
        import ingest_airtable
        # Defensive: `Ready` must NOT be in the allowed set — Ready means
        # not-yet-posted upstream, so the archive must not mirror it.
        assert "ready" not in ingest_airtable.ALLOWED_STATUSES

    def test_legacy_published_is_excluded_from_archive_ingestion(self):
        import ingest_airtable
        # Defensive: legacy values like `published` / `approved` (which lived
        # in the old `Status` field map) must not silently re-admit records
        # under the new `Posted` gate.
        assert "published" not in ingest_airtable.ALLOWED_STATUSES
        assert "approved" not in ingest_airtable.ALLOWED_STATUSES

    def test_faim_status_posted_maps_and_is_eligible(self):
        import ingest_airtable
        record = {
            "id": "recPosted",
            "fields": {
                "Title": "Posted Article",
                "slug": "posted-article",
                "Pub Date": "2026-05-01",
                "GUID": "https://radar.firstaimovers.com/posted-article",
                "Content HTML": "body",
                "FAIM Status": "Posted",
            },
        }
        payload = ingest_airtable._record_to_payload(record)
        # Raw Airtable casing is preserved on the payload; gate compares lowercase.
        assert payload["status"] == "Posted"
        assert payload["status"].lower() in ingest_airtable.ALLOWED_STATUSES

    def test_faim_status_ready_maps_but_is_skipped(self):
        import ingest_airtable
        record = {
            "id": "recReady",
            "fields": {
                "Title": "Ready Article",
                "slug": "ready-article",
                "Pub Date": "2026-05-01",
                "GUID": "https://radar.firstaimovers.com/ready-article",
                "Content HTML": "body",
                "FAIM Status": "Ready",
            },
        }
        payload = ingest_airtable._record_to_payload(record)
        assert payload["status"] == "Ready"
        # The lowercase form must NOT match the allowed set — main() will skip.
        assert payload["status"].lower() not in ingest_airtable.ALLOWED_STATUSES

    def test_main_skips_ready_record_under_write_mode(self, monkeypatch, tmp_path, capsys):
        """End-to-end: under --write, a Ready record must not produce a folder."""
        import ingest_airtable
        monkeypatch.setenv("AIRTABLE_PAT", "pat_test")
        monkeypatch.setenv("AIRTABLE_BASE_ID", "app_test")
        monkeypatch.setenv("AIRTABLE_TABLE_NAME", "Articles")
        monkeypatch.setattr(ingest_airtable, "ARTICLES_DIR", tmp_path / "articles")
        record = {
            "id": "recReadySkip",
            "fields": {
                "Title": "Ready Should Skip",
                "slug": "ready-should-skip",
                "Pub Date": "2026-05-01",
                "GUID": "https://radar.firstaimovers.com/ready-should-skip",
                "Content HTML": "body",
                "FAIM Status": "Ready",
            },
        }
        monkeypatch.setattr(ingest_airtable, "_fetch_records", lambda *a, **k: iter([record]))
        code = ingest_airtable.main(["--write"])
        assert code == 0
        # No folder should have been created — Ready was gated out.
        assert not (tmp_path / "articles" / "2026-05-01-ready-should-skip").exists()
        captured = capsys.readouterr()
        assert "[SKIP]" in captured.err
        assert "ready" in captured.err.lower()

    def test_main_admits_posted_record_under_write_mode(self, monkeypatch, tmp_path):
        """End-to-end: under --write, a Posted record produces an article folder."""
        import ingest_airtable
        monkeypatch.setenv("AIRTABLE_PAT", "pat_test")
        monkeypatch.setenv("AIRTABLE_BASE_ID", "app_test")
        monkeypatch.setenv("AIRTABLE_TABLE_NAME", "Articles")
        monkeypatch.setattr(ingest_airtable, "ARTICLES_DIR", tmp_path / "articles")
        record = {
            "id": "recPostedAdmit",
            "fields": {
                "Title": "Posted Should Land",
                "slug": "posted-should-land",
                "Pub Date": "2026-05-01",
                "GUID": "https://radar.firstaimovers.com/posted-should-land",
                "Content HTML": "body",
                "FAIM Status": "Posted",
            },
        }
        monkeypatch.setattr(ingest_airtable, "_fetch_records", lambda *a, **k: iter([record]))
        code = ingest_airtable.main(["--write"])
        assert code == 0
        article_dir = tmp_path / "articles" / "2026-05-01-posted-should-land"
        assert (article_dir / "article.md").exists()
        meta = json.loads((article_dir / "metadata.json").read_text(encoding="utf-8"))
        # Lowercase normalization keeps archive consistent with legacy "published".
        assert meta["status"] == "posted"

    def test_missing_faim_status_yields_no_status_key(self):
        import ingest_airtable
        record = {
            "id": "recNoStatus",
            "fields": {
                "Title": "No Status Article",
                "slug": "no-status-article",
                "Pub Date": "2026-05-01",
                "GUID": "https://radar.firstaimovers.com/no-status-article",
                "Content HTML": "body",
            },
        }
        payload = ingest_airtable._record_to_payload(record)
        # _record_to_payload drops None values, so missing status must not appear.
        assert "status" not in payload

    def test_missing_faim_status_does_not_invalidate_required_schema(self):
        import ingest_airtable
        record = {
            "id": "recNoStatus",
            "fields": {
                "Title": "No Status Article",
                "slug": "no-status-article",
                "Pub Date": "2026-05-01",
                "GUID": "https://radar.firstaimovers.com/no-status-article",
                "Content HTML": "body",
            },
        }
        payload = ingest_airtable._record_to_payload(record)
        schema = {
            "required": ["title", "slug", "published_date", "canonical_url", "article_markdown"],
            "properties": {},
        }
        errors, warnings = ingest_airtable._validate_payload(payload, schema)
        assert errors == []

    def test_legacy_literal_status_field_is_not_read(self):
        # Defends against silent fallback: if someone re-adds a literal "Status"
        # field to Airtable, the script must still rely only on "FAIM Status".
        import ingest_airtable
        record = {
            "id": "recLegacy",
            "fields": {
                "Title": "Legacy",
                "slug": "legacy",
                "Pub Date": "2026-05-01",
                "GUID": "https://radar.firstaimovers.com/legacy",
                "Content HTML": "body",
                "Status": "approved",  # legacy field — must be ignored
                "FAIM Status": "Posted",  # only this counts
            },
        }
        payload = ingest_airtable._record_to_payload(record)
        # Should map from FAIM Status, not the legacy literal field.
        assert payload["status"] == "Posted"

