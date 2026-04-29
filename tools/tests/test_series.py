#!/usr/bin/env python3
"""Contract tests for article series / learning-path infrastructure."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestRegistry:
    def test_series_registry_exists(self):
        assert (REPO_ROOT / "tools" / "series_registry.json").exists()

    def test_series_registry_has_series_key(self):
        data = json.loads((REPO_ROOT / "tools" / "series_registry.json").read_text(encoding="utf-8"))
        assert "series" in data
        assert isinstance(data["series"], dict)

    def test_registry_entries_have_title_and_description(self):
        data = json.loads((REPO_ROOT / "tools" / "series_registry.json").read_text(encoding="utf-8"))
        for slug, info in data.get("series", {}).items():
            assert "title" in info, f"Series {slug} missing title"
            assert "description" in info, f"Series {slug} missing description"


class TestSchema:
    def test_article_schema_allows_series(self):
        schema = json.loads((REPO_ROOT / "tools" / "article_schema.json").read_text(encoding="utf-8"))
        props = schema.get("properties", {})
        assert "series" in props
        assert props["series"].get("type") == "string"

    def test_article_schema_allows_series_order(self):
        schema = json.loads((REPO_ROOT / "tools" / "article_schema.json").read_text(encoding="utf-8"))
        props = schema.get("properties", {})
        assert "series_order" in props
        assert props["series_order"].get("type") == "integer"

    def test_series_is_not_required(self):
        schema = json.loads((REPO_ROOT / "tools" / "article_schema.json").read_text(encoding="utf-8"))
        required = schema.get("required", [])
        assert "series" not in required
        assert "series_order" not in required


class TestCheckSeries:
    def test_passes_when_no_series_exist(self, tmp_path):
        articles_dir = tmp_path / "articles"
        articles_dir.mkdir()
        # Create a minimal article without series
        folder = articles_dir / "2024-01-01-test"
        folder.mkdir()
        (folder / "metadata.json").write_text(
            json.dumps({"title": "Test", "published_date": "2024-01-01", "canonical_url": "https://example.com"}),
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "check_series.py"), "--articles-dir", str(articles_dir)],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert result.returncode == 0
        assert "OK" in result.stdout

    def test_catches_unknown_series_slug(self, tmp_path):
        articles_dir = tmp_path / "articles"
        folder = articles_dir / "2024-01-01-test"
        folder.mkdir(parents=True)
        (folder / "metadata.json").write_text(
            json.dumps({"title": "Test", "published_date": "2024-01-01", "canonical_url": "https://example.com",
                        "series": "nonexistent-series", "series_order": 1}),
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "check_series.py"), "--articles-dir", str(articles_dir)],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert result.returncode == 1
        assert "unknown series slug" in result.stdout.lower()

    def test_catches_duplicate_order(self, tmp_path):
        articles_dir = tmp_path / "articles"
        for name in ("a", "b"):
            folder = articles_dir / f"2024-01-0{name}-test"
            folder.mkdir(parents=True)
            (folder / "metadata.json").write_text(
                json.dumps({"title": "Test", "published_date": "2024-01-01", "canonical_url": "https://example.com",
                            "series": "prompt-engineering-10-day", "series_order": 1}),
                encoding="utf-8",
            )
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "check_series.py"), "--articles-dir", str(articles_dir)],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert result.returncode == 1
        assert "duplicate series_order" in result.stdout.lower()

    def test_catches_order_without_series(self, tmp_path):
        articles_dir = tmp_path / "articles"
        folder = articles_dir / "2024-01-01-test"
        folder.mkdir(parents=True)
        (folder / "metadata.json").write_text(
            json.dumps({"title": "Test", "published_date": "2024-01-01", "canonical_url": "https://example.com",
                        "series_order": 1}),
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "check_series.py"), "--articles-dir", str(articles_dir)],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert result.returncode == 1
        assert "series_order without series" in result.stdout.lower()


class TestRebuildIntegration:
    def test_rebuild_preserves_non_series_pages(self, tmp_path, monkeypatch):
        pytest.importorskip("jinja2")
        import tools.rebuild_local as m
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "TOPIC_INTROS_PATH", REPO_ROOT / "tools" / "topic_intros.json")
        monkeypatch.setattr(m, "COMMENTS_CONFIG_PATH", REPO_ROOT / "tools" / "comments_config.json")

        # Create fixture article
        art_dir = tmp_path / "articles" / "2024-01-01-test"
        art_dir.mkdir(parents=True)
        (art_dir / "metadata.json").write_text(json.dumps({
            "title": "Test", "slug": "test", "published_date": "2024-01-01",
            "canonical_url": "https://example.com/test", "folder": "2024-01-01-test",
            "topics": ["AI Strategy"], "tags": ["test"], "word_count": 100,
        }), encoding="utf-8")
        (art_dir / "article.md").write_text("# Test\n\nBody.", encoding="utf-8")

        idx = {"articles": [
            {"title": "Test", "slug": "test", "published_date": "2024-01-01",
             "canonical_url": "https://example.com/test", "folder": "2024-01-01-test",
             "topics": ["AI Strategy"], "tags": ["test"], "word_count": 100}
        ]}
        m.build_site(idx)
        assert (tmp_path / "site" / "articles" / "test" / "index.html").exists()


class TestArticleTemplate:
    def test_series_chip_renders_for_fixture(self, tmp_path, monkeypatch):
        pytest.importorskip("jinja2")
        import tools.rebuild_local as m
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "TOPIC_INTROS_PATH", REPO_ROOT / "tools" / "topic_intros.json")
        monkeypatch.setattr(m, "COMMENTS_CONFIG_PATH", REPO_ROOT / "tools" / "comments_config.json")

        # Create fixture article with series metadata
        art_dir = tmp_path / "articles" / "2024-01-01-fixture"
        art_dir.mkdir(parents=True)
        (art_dir / "metadata.json").write_text(json.dumps({
            "title": "Fixture Part 1", "slug": "fixture-part-1",
            "published_date": "2024-01-01", "canonical_url": "https://example.com/1",
            "folder": "2024-01-01-fixture", "topics": ["AI Strategy"],
            "tags": ["test"], "word_count": 100, "series": "test-series", "series_order": 1,
        }), encoding="utf-8")
        (art_dir / "article.md").write_text("# Fixture Part 1\n\nBody.", encoding="utf-8")

        # Create second fixture article in same series
        art_dir2 = tmp_path / "articles" / "2024-01-02-fixture"
        art_dir2.mkdir(parents=True)
        (art_dir2 / "metadata.json").write_text(json.dumps({
            "title": "Fixture Part 2", "slug": "fixture-part-2",
            "published_date": "2024-01-02", "canonical_url": "https://example.com/2",
            "folder": "2024-01-02-fixture", "topics": ["AI Strategy"],
            "tags": ["test"], "word_count": 100, "series": "test-series", "series_order": 2,
        }), encoding="utf-8")
        (art_dir2 / "article.md").write_text("# Fixture Part 2\n\nBody.", encoding="utf-8")

        # Temporarily extend registry
        reg_path = REPO_ROOT / "tools" / "series_registry.json"
        original_reg = json.loads(reg_path.read_text(encoding="utf-8"))
        modified_reg = {**original_reg, "series": {**original_reg.get("series", {}), "test-series": {
            "title": "Test Series", "description": "A test series.", "topics": ["AI Strategy"]
        }}}
        reg_path.write_text(json.dumps(modified_reg, indent=2), encoding="utf-8")
        try:
            idx = {"articles": [
                {"title": "Fixture Part 1", "slug": "fixture-part-1", "published_date": "2024-01-01",
                 "canonical_url": "https://example.com/1", "folder": "2024-01-01-fixture",
                 "topics": ["AI Strategy"], "tags": ["test"], "word_count": 100,
                 "series": "test-series", "series_order": 1},
                {"title": "Fixture Part 2", "slug": "fixture-part-2", "published_date": "2024-01-02",
                 "canonical_url": "https://example.com/2", "folder": "2024-01-02-fixture",
                 "topics": ["AI Strategy"], "tags": ["test"], "word_count": 100,
                 "series": "test-series", "series_order": 2},
            ]}
            m.build_site(idx)
            html1 = (tmp_path / "site" / "articles" / "fixture-part-1" / "index.html").read_text(encoding="utf-8")
            html2 = (tmp_path / "site" / "articles" / "fixture-part-2" / "index.html").read_text(encoding="utf-8")
            assert "Part 1 of 2" in html1
            assert "Continue reading" in html1
            assert "Previous in series" in html2
        finally:
            reg_path.write_text(json.dumps(original_reg, indent=2), encoding="utf-8")

    def test_first_article_has_no_previous_link(self, tmp_path, monkeypatch):
        pytest.importorskip("jinja2")
        import tools.rebuild_local as m
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "TOPIC_INTROS_PATH", REPO_ROOT / "tools" / "topic_intros.json")
        monkeypatch.setattr(m, "COMMENTS_CONFIG_PATH", REPO_ROOT / "tools" / "comments_config.json")

        art_dir = tmp_path / "articles" / "2024-01-01-fixture"
        art_dir.mkdir(parents=True)
        (art_dir / "metadata.json").write_text(json.dumps({
            "title": "Fixture Part 1", "slug": "fixture-part-1",
            "published_date": "2024-01-01", "canonical_url": "https://example.com/1",
            "folder": "2024-01-01-fixture", "topics": ["AI Strategy"],
            "tags": ["test"], "word_count": 100, "series": "test-series", "series_order": 1,
        }), encoding="utf-8")
        (art_dir / "article.md").write_text("# Fixture\n\nBody.", encoding="utf-8")

        reg_path = REPO_ROOT / "tools" / "series_registry.json"
        original_reg = json.loads(reg_path.read_text(encoding="utf-8"))
        modified_reg = {**original_reg, "series": {**original_reg.get("series", {}), "test-series": {
            "title": "Test Series", "description": "A test series.", "topics": ["AI Strategy"]
        }}}
        reg_path.write_text(json.dumps(modified_reg, indent=2), encoding="utf-8")
        try:
            idx = {"articles": [
                {"title": "Fixture Part 1", "slug": "fixture-part-1", "published_date": "2024-01-01",
                 "canonical_url": "https://example.com/1", "folder": "2024-01-01-fixture",
                 "topics": ["AI Strategy"], "tags": ["test"], "word_count": 100,
                 "series": "test-series", "series_order": 1},
            ]}
            m.build_site(idx)
            html = (tmp_path / "site" / "articles" / "fixture-part-1" / "index.html").read_text(encoding="utf-8")
            assert "series-prev" not in html or "Previous in series" not in html
        finally:
            reg_path.write_text(json.dumps(original_reg, indent=2), encoding="utf-8")


class TestTopicTemplate:
    def test_series_section_renders_when_topic_has_series(self, tmp_path, monkeypatch):
        pytest.importorskip("jinja2")
        import tools.rebuild_local as m
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "TOPIC_INTROS_PATH", REPO_ROOT / "tools" / "topic_intros.json")
        monkeypatch.setattr(m, "COMMENTS_CONFIG_PATH", REPO_ROOT / "tools" / "comments_config.json")
        monkeypatch.setattr(m, "MIN_ARTICLES_FOR_TOPIC_PAGE", 1)

        art_dir = tmp_path / "articles" / "2024-01-01-fixture"
        art_dir.mkdir(parents=True)
        (art_dir / "metadata.json").write_text(json.dumps({
            "title": "Fixture Part 1", "slug": "fixture-part-1",
            "published_date": "2024-01-01", "canonical_url": "https://example.com/1",
            "folder": "2024-01-01-fixture", "topics": ["AI Strategy"],
            "tags": ["test"], "word_count": 100, "series": "test-series", "series_order": 1,
        }), encoding="utf-8")
        (art_dir / "article.md").write_text("# Fixture\n\nBody.", encoding="utf-8")

        reg_path = REPO_ROOT / "tools" / "series_registry.json"
        original_reg = json.loads(reg_path.read_text(encoding="utf-8"))
        modified_reg = {**original_reg, "series": {**original_reg.get("series", {}), "test-series": {
            "title": "Test Series", "description": "A test series.", "topics": ["AI Strategy"]
        }}}
        reg_path.write_text(json.dumps(modified_reg, indent=2), encoding="utf-8")
        try:
            idx = {"articles": [
                {"title": "Fixture Part 1", "slug": "fixture-part-1", "published_date": "2024-01-01",
                 "canonical_url": "https://example.com/1", "folder": "2024-01-01-fixture",
                 "topics": ["AI Strategy"], "tags": ["test"], "word_count": 100,
                 "series": "test-series", "series_order": 1},
            ]}
            m.build_site(idx)
            html = (tmp_path / "site" / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
            assert "Series in this topic" in html
            assert "Test Series" in html
        finally:
            reg_path.write_text(json.dumps(original_reg, indent=2), encoding="utf-8")


class TestJsonLd:
    def test_includes_creativeworkseries_for_series_article(self, tmp_path, monkeypatch):
        pytest.importorskip("jinja2")
        import tools.rebuild_local as m
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "TOPIC_INTROS_PATH", REPO_ROOT / "tools" / "topic_intros.json")
        monkeypatch.setattr(m, "COMMENTS_CONFIG_PATH", REPO_ROOT / "tools" / "comments_config.json")

        art_dir = tmp_path / "articles" / "2024-01-01-fixture"
        art_dir.mkdir(parents=True)
        (art_dir / "metadata.json").write_text(json.dumps({
            "title": "Fixture Part 1", "slug": "fixture-part-1",
            "published_date": "2024-01-01", "canonical_url": "https://example.com/1",
            "folder": "2024-01-01-fixture", "topics": ["AI Strategy"],
            "tags": ["test"], "word_count": 100, "series": "test-series", "series_order": 1,
        }), encoding="utf-8")
        (art_dir / "article.md").write_text("# Fixture\n\nBody.", encoding="utf-8")

        reg_path = REPO_ROOT / "tools" / "series_registry.json"
        original_reg = json.loads(reg_path.read_text(encoding="utf-8"))
        modified_reg = {**original_reg, "series": {**original_reg.get("series", {}), "test-series": {
            "title": "Test Series", "description": "A test series.", "topics": ["AI Strategy"]
        }}}
        reg_path.write_text(json.dumps(modified_reg, indent=2), encoding="utf-8")
        try:
            idx = {"articles": [
                {"title": "Fixture Part 1", "slug": "fixture-part-1", "published_date": "2024-01-01",
                 "canonical_url": "https://example.com/1", "folder": "2024-01-01-fixture",
                 "topics": ["AI Strategy"], "tags": ["test"], "word_count": 100,
                 "series": "test-series", "series_order": 1},
            ]}
            m.build_site(idx)
            html = (tmp_path / "site" / "articles" / "fixture-part-1" / "index.html").read_text(encoding="utf-8")
            assert "CreativeWorkSeries" in html
            assert "isPartOf" in html
        finally:
            reg_path.write_text(json.dumps(original_reg, indent=2), encoding="utf-8")

    def test_no_isPartOf_for_non_series_article(self, tmp_path, monkeypatch):
        pytest.importorskip("jinja2")
        import tools.rebuild_local as m
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "TOPIC_INTROS_PATH", REPO_ROOT / "tools" / "topic_intros.json")
        monkeypatch.setattr(m, "COMMENTS_CONFIG_PATH", REPO_ROOT / "tools" / "comments_config.json")

        art_dir = tmp_path / "articles" / "2024-01-01-fixture"
        art_dir.mkdir(parents=True)
        (art_dir / "metadata.json").write_text(json.dumps({
            "title": "Fixture", "slug": "fixture",
            "published_date": "2024-01-01", "canonical_url": "https://example.com/1",
            "folder": "2024-01-01-fixture", "topics": ["AI Strategy"],
            "tags": ["test"], "word_count": 100,
        }), encoding="utf-8")
        (art_dir / "article.md").write_text("# Fixture\n\nBody.", encoding="utf-8")

        idx = {"articles": [
            {"title": "Fixture", "slug": "fixture", "published_date": "2024-01-01",
             "canonical_url": "https://example.com/1", "folder": "2024-01-01-fixture",
             "topics": ["AI Strategy"], "tags": ["test"], "word_count": 100},
        ]}
        m.build_site(idx)
        html = (tmp_path / "site" / "articles" / "fixture" / "index.html").read_text(encoding="utf-8")
        # isPartOf should not appear in the Article JSON-LD (it may appear in CollectionPage on topic pages)
        # Check that the article JSON-LD block does not contain isPartOf
        article_ld_start = html.find('"@type": "Article"')
        if article_ld_start != -1:
            block_end = html.find('</script>', article_ld_start)
            block = html[article_ld_start:block_end]
            assert "isPartOf" not in block


class TestDocs:
    def test_series_docs_exist(self):
        assert (REPO_ROOT / "docs" / "SERIES.md").exists()

    def test_series_candidates_exist(self):
        assert (REPO_ROOT / "docs" / "SERIES_CANDIDATES.md").exists()

    def test_series_docs_mention_editorial_approval(self):
        text = (REPO_ROOT / "docs" / "SERIES.md").read_text(encoding="utf-8")
        assert "editorial approval" in text.lower()

    def test_operations_doc_references_series(self):
        text = (REPO_ROOT / "docs" / "OPERATIONS.md").read_text(encoding="utf-8")
        assert "SERIES.md" in text or "series" in text.lower()


class TestRealMetadataActivation:
    def test_approved_series_have_metadata(self):
        """Verify the two editorially approved series are present in real metadata."""
        articles_dir = REPO_ROOT / "articles"
        prompt_engineering = []
        model_guide = []
        for folder in articles_dir.iterdir():
            if not folder.is_dir():
                continue
            meta_path = folder / "metadata.json"
            if not meta_path.exists():
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            series = meta.get("series")
            if series == "prompt-engineering-10-day":
                prompt_engineering.append((folder.name, meta.get("series_order")))
            elif series == "ai-model-guide-smbs-2026":
                model_guide.append((folder.name, meta.get("series_order")))
        assert len(prompt_engineering) == 10, f"Expected 10 prompt-engineering articles, got {len(prompt_engineering)}"
        assert len(model_guide) == 2, f"Expected 2 model-guide articles, got {len(model_guide)}"
        pe_orders = sorted(o for _, o in prompt_engineering)
        assert pe_orders == list(range(1, 11)), f"Unexpected prompt-engineering orders: {pe_orders}"
        mg_orders = sorted(o for _, o in model_guide)
        assert mg_orders == [1, 2], f"Unexpected model-guide orders: {mg_orders}"
