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

class TestSecurityTooling:
    """Gitleaks config, Dependabot config, and content scrubber."""

    # --- Gitleaks config --------------------------------------------------

    def test_gitleaks_config_exists(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        config = root / ".gitleaks.toml"
        assert config.exists(), ".gitleaks.toml must exist at repo root"

    def test_gitleaks_config_has_allowlist_sections(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        text = (root / ".gitleaks.toml").read_text(encoding="utf-8")
        assert "[allowlist]" in text
        assert "IndexNow" in text or "indexnow" in text.lower()
        # Should allowlist the known Beehiiv presigned URL article
        assert "beehiiv" in text.lower() or "2025-09-28" in text

    def test_gitleaks_workflow_exists(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        workflow = root / ".github" / "workflows" / "gitleaks.yml"
        assert workflow.exists(), "gitleaks workflow must exist"
        text = workflow.read_text(encoding="utf-8")
        assert "gitleaks" in text.lower()
        assert "pull_request" in text or "push" in text

    # --- Dependabot config ------------------------------------------------

    def test_dependabot_config_exists(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        config = root / ".github" / "dependabot.yml"
        assert config.exists(), ".github/dependabot.yml must exist"

    def test_dependabot_has_pip_and_github_actions(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        text = (root / ".github" / "dependabot.yml").read_text(encoding="utf-8")
        assert "package-ecosystem: \"pip\"" in text or "package-ecosystem: pip" in text, "Dependabot must cover pip"
        assert "package-ecosystem: \"github-actions\"" in text or "package-ecosystem: github-actions" in text, "Dependabot must cover GitHub Actions"

    # --- Content scrubber -------------------------------------------------

    def test_scrubber_dry_run_idempotent(self, monkeypatch, tmp_path):
        import scrub_presigned_urls
        # Create a synthetic article with a Beehiiv audio block
        article_dir = tmp_path / "articles" / "test-article"
        article_dir.mkdir(parents=True)
        md = article_dir / "article.md"
        audio_block = (
            '<audio controls preload="auto" class="w-full" id="beehiiv-audio-tts-id">'
            '<source src="https://example.com/audio.mp3?X-Amz-Signature=abc123" type="audio/mpeg"/>'
            'Your browser does not support the audio element.</audio>'
        )
        md.write_text(f"# Title\n\n{audio_block}\n\nSome text.\n", encoding="utf-8")

        monkeypatch.setattr(scrub_presigned_urls, "ARTICLES_DIR", tmp_path / "articles")
        result1 = scrub_presigned_urls.main(["--dry-run"])
        assert result1 == 1  # dry-run returns 1 when changes would be made

        # File must be unchanged after dry-run
        content = md.read_text(encoding="utf-8")
        assert audio_block in content
        assert "<!-- Audio embed removed" not in content

    def test_scrubber_removes_targeted_audio_block(self, monkeypatch, tmp_path):
        import scrub_presigned_urls
        article_dir = tmp_path / "articles" / "test-article"
        article_dir.mkdir(parents=True)
        md = article_dir / "article.md"
        audio_block = (
            '<audio controls preload="auto" class="w-full" id="beehiiv-audio-tts-id">'
            '<source src="https://example.com/audio.mp3?X-Amz-Signature=abc123" type="audio/mpeg"/>'
            'Your browser does not support the audio element.</audio>'
        )
        md.write_text(f"# Title\n\n{audio_block}\n\nSome text.\n", encoding="utf-8")

        monkeypatch.setattr(scrub_presigned_urls, "ARTICLES_DIR", tmp_path / "articles")
        result = scrub_presigned_urls.main([])
        assert result == 0  # live run returns 0 when changes are made

        content = md.read_text(encoding="utf-8")
        assert audio_block not in content
        assert "<!-- Audio embed removed: third-party presigned URL expired -->" in content
        assert "Some text." in content  # surrounding text preserved

    def test_scrubber_preserves_normal_links_and_text(self, monkeypatch, tmp_path):
        import scrub_presigned_urls
        article_dir = tmp_path / "articles" / "test-article"
        article_dir.mkdir(parents=True)
        md = article_dir / "article.md"
        original = (
            "# Title\n\n"
            'Read more at [example](https://example.com/some-path).\n\n'
            "Normal paragraph.\n"
        )
        md.write_text(original, encoding="utf-8")

        monkeypatch.setattr(scrub_presigned_urls, "ARTICLES_DIR", tmp_path / "articles")
        result = scrub_presigned_urls.main([])
        assert result == 0  # no changes

        assert md.read_text(encoding="utf-8") == original

    def test_scrubber_reports_count(self, monkeypatch, tmp_path, capsys):
        import scrub_presigned_urls
        article_dir = tmp_path / "articles" / "test-article"
        article_dir.mkdir(parents=True)
        md = article_dir / "article.md"
        audio_block = (
            '<audio controls preload="auto" class="w-full" id="beehiiv-audio-tts-id">'
            '<source src="https://example.com/audio.mp3?X-Amz-Signature=abc123" type="audio/mpeg"/>'
            'Your browser does not support the audio element.</audio>'
        )
        md.write_text(f"# Title\n\n{audio_block}\n", encoding="utf-8")

        monkeypatch.setattr(scrub_presigned_urls, "ARTICLES_DIR", tmp_path / "articles")
        scrub_presigned_urls.main(["--dry-run"])
        captured = capsys.readouterr()
        assert "Scrubbed 1 article(s)" in captured.out
        assert "article.md" in captured.out

    def test_scrubber_finds_real_beehiiv_audio_block(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        article = root / "articles" / "2025-09-28-llm-limits-solved-ai-workarounds-guide-2025" / "article.md"
        if not article.exists():
            pytest.skip("Target article not found")
        text = article.read_text(encoding="utf-8")
        assert '<audio' in text
        assert 'X-Amz-Signature' in text
        assert 'beehiiv-audio-tts-id' in text


    def test_duplicate_title_gate_is_hard(self):
        from pathlib import Path
        workflow = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "tests.yml"
        text = workflow.read_text(encoding="utf-8")
        assert "check_duplicate_titles.py" in text
        assert "continue-on-error" not in text, "Duplicate-title gate must not be soft"

    def test_no_duplicate_titles_in_index(self):
        import json
        from pathlib import Path
        from collections import defaultdict
        index = json.loads((Path(__file__).resolve().parents[2] / "index.json").read_text(encoding="utf-8"))
        by_title = defaultdict(list)
        for a in index.get("articles", []):
            title = a.get("title")
            if title:
                by_title[title.lower()].append(a.get("folder", ""))
        duplicates = {t: folders for t, folders in by_title.items() if len(folders) > 1}
        assert not duplicates, f"Duplicate titles found: {duplicates}"


# Tests: E20a — Self-hosted Airtable cron ingestion
# =========================================================================


