#!/usr/bin/env python3
"""Tests for E39b translated page rendering: routes, hreflang, canonical, inLanguage."""

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
REBUILD_LOCAL = REPO_ROOT / "tools" / "rebuild_local.py"


class TestMultilingualPages:
    def _import_rebuild(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("rebuild_local", REBUILD_LOCAL)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["rebuild_local"] = mod
        spec.loader.exec_module(mod)
        return mod

    def _setup_article_with_translation(self, tmp_path, mod, slug="test", status="published"):
        folder = "2026-04-01-test"
        (tmp_path / "articles" / folder).mkdir(parents=True)
        meta = {
            "folder": folder,
            "slug": slug,
            "title": "Test Article",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com/test",
            "topics": ["AI Strategy"],
        }
        (tmp_path / "articles" / folder / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        (tmp_path / "articles" / folder / "article.md").write_text(
            "---\ntitle: Test\n---\n\n# Test Article\n\nBody text here.\n",
            encoding="utf-8",
        )
        # Spanish translation
        (tmp_path / "articles" / folder / "article.es.md").write_text(
            "# Artículo de prueba\n\nTexto del cuerpo.\n",
            encoding="utf-8",
        )
        # Translation sidecar
        translations = {
            "es": {
                "status": status,
                "title": "Artículo de prueba",
                "reviewed_at": "2026-04-30",
                "reviewer": "Dr. Hernani Costa",
                "model": "deepl",
                "source_chars": 100,
            }
        }
        (tmp_path / "articles" / folder / "translations.json").write_text(
            json.dumps(translations), encoding="utf-8"
        )
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")
        return folder, meta

    def test_unapproved_translation_does_not_render(self, tmp_path, monkeypatch):
        mod = self._import_rebuild()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")

        monkeypatch.setattr(mod, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(mod, "TEMPLATE_DIR", REPO_ROOT / "templates")
        monkeypatch.setattr(mod, "STATIC_DIR", REPO_ROOT / "static")
        monkeypatch.setattr(mod, "TOPIC_INTROS_PATH", tmp_path / "tools" / "topic_intros.json")
        monkeypatch.setattr(mod, "COMMENTS_CONFIG_PATH", tmp_path / "tools" / "comments_config.json")
        monkeypatch.setattr(mod, "OG_CONFIG_PATH", tmp_path / "tools" / "og_config.json")
        monkeypatch.setattr(mod, "CITATION_GRAPH_PATH", tmp_path / "citation_graph.json")

        self._setup_article_with_translation(tmp_path, mod, status="draft")

        idx = mod.build_index()
        mod.build_site(idx)

        assert not (tmp_path / "site" / "es" / "articles" / "test" / "index.html").exists()

    def test_approved_translation_renders_route(self, tmp_path, monkeypatch):
        mod = self._import_rebuild()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")

        monkeypatch.setattr(mod, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(mod, "TEMPLATE_DIR", REPO_ROOT / "templates")
        monkeypatch.setattr(mod, "STATIC_DIR", REPO_ROOT / "static")
        monkeypatch.setattr(mod, "TOPIC_INTROS_PATH", tmp_path / "tools" / "topic_intros.json")
        monkeypatch.setattr(mod, "COMMENTS_CONFIG_PATH", tmp_path / "tools" / "comments_config.json")
        monkeypatch.setattr(mod, "OG_CONFIG_PATH", tmp_path / "tools" / "og_config.json")
        monkeypatch.setattr(mod, "CITATION_GRAPH_PATH", tmp_path / "citation_graph.json")

        self._setup_article_with_translation(tmp_path, mod, status="published")

        idx = mod.build_index()
        mod.build_site(idx)

        es_path = tmp_path / "site" / "es" / "articles" / "test" / "index.html"
        assert es_path.exists()
        html = es_path.read_text(encoding="utf-8")
        assert "Artículo de prueba" in html

    def test_english_page_has_hreflang_alternates(self, tmp_path, monkeypatch):
        mod = self._import_rebuild()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")

        monkeypatch.setattr(mod, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(mod, "TEMPLATE_DIR", REPO_ROOT / "templates")
        monkeypatch.setattr(mod, "STATIC_DIR", REPO_ROOT / "static")
        monkeypatch.setattr(mod, "TOPIC_INTROS_PATH", tmp_path / "tools" / "topic_intros.json")
        monkeypatch.setattr(mod, "COMMENTS_CONFIG_PATH", tmp_path / "tools" / "comments_config.json")
        monkeypatch.setattr(mod, "OG_CONFIG_PATH", tmp_path / "tools" / "og_config.json")
        monkeypatch.setattr(mod, "CITATION_GRAPH_PATH", tmp_path / "citation_graph.json")

        self._setup_article_with_translation(tmp_path, mod, status="published")

        idx = mod.build_index()
        mod.build_site(idx)

        en_path = tmp_path / "site" / "articles" / "test" / "index.html"
        html = en_path.read_text(encoding="utf-8")
        assert 'hreflang="es"' in html
        assert 'hreflang="x-default"' in html

    def test_translated_page_has_hreflang_alternates(self, tmp_path, monkeypatch):
        mod = self._import_rebuild()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")

        monkeypatch.setattr(mod, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(mod, "TEMPLATE_DIR", REPO_ROOT / "templates")
        monkeypatch.setattr(mod, "STATIC_DIR", REPO_ROOT / "static")
        monkeypatch.setattr(mod, "TOPIC_INTROS_PATH", tmp_path / "tools" / "topic_intros.json")
        monkeypatch.setattr(mod, "COMMENTS_CONFIG_PATH", tmp_path / "tools" / "comments_config.json")
        monkeypatch.setattr(mod, "OG_CONFIG_PATH", tmp_path / "tools" / "og_config.json")
        monkeypatch.setattr(mod, "CITATION_GRAPH_PATH", tmp_path / "citation_graph.json")

        self._setup_article_with_translation(tmp_path, mod, status="published")

        idx = mod.build_index()
        mod.build_site(idx)

        es_path = tmp_path / "site" / "es" / "articles" / "test" / "index.html"
        html = es_path.read_text(encoding="utf-8")
        assert 'hreflang="en"' in html
        assert 'hreflang="es"' in html
        assert 'hreflang="x-default"' in html

    def test_english_page_is_noindex_external_canonical(self, tmp_path, monkeypatch):
        mod = self._import_rebuild()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")

        monkeypatch.setattr(mod, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(mod, "TEMPLATE_DIR", REPO_ROOT / "templates")
        monkeypatch.setattr(mod, "STATIC_DIR", REPO_ROOT / "static")
        monkeypatch.setattr(mod, "TOPIC_INTROS_PATH", tmp_path / "tools" / "topic_intros.json")
        monkeypatch.setattr(mod, "COMMENTS_CONFIG_PATH", tmp_path / "tools" / "comments_config.json")
        monkeypatch.setattr(mod, "OG_CONFIG_PATH", tmp_path / "tools" / "og_config.json")
        monkeypatch.setattr(mod, "CITATION_GRAPH_PATH", tmp_path / "citation_graph.json")

        self._setup_article_with_translation(tmp_path, mod, status="published")

        idx = mod.build_index()
        mod.build_site(idx)

        en_path = tmp_path / "site" / "articles" / "test" / "index.html"
        html = en_path.read_text(encoding="utf-8")
        assert 'content="noindex, follow"' in html
        assert 'href="https://example.com/test"' in html

    def test_translated_page_is_index_self_canonical(self, tmp_path, monkeypatch):
        mod = self._import_rebuild()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")

        monkeypatch.setattr(mod, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(mod, "TEMPLATE_DIR", REPO_ROOT / "templates")
        monkeypatch.setattr(mod, "STATIC_DIR", REPO_ROOT / "static")
        monkeypatch.setattr(mod, "TOPIC_INTROS_PATH", tmp_path / "tools" / "topic_intros.json")
        monkeypatch.setattr(mod, "COMMENTS_CONFIG_PATH", tmp_path / "tools" / "comments_config.json")
        monkeypatch.setattr(mod, "OG_CONFIG_PATH", tmp_path / "tools" / "og_config.json")
        monkeypatch.setattr(mod, "CITATION_GRAPH_PATH", tmp_path / "citation_graph.json")

        self._setup_article_with_translation(tmp_path, mod, status="published")

        idx = mod.build_index()
        mod.build_site(idx)

        es_path = tmp_path / "site" / "es" / "articles" / "test" / "index.html"
        html = es_path.read_text(encoding="utf-8")
        assert 'content="index, follow"' in html
        assert 'href="https://articles.firstaimovers.com/es/articles/test/"' in html

    def test_jsonld_inlanguage_is_dynamic(self, tmp_path, monkeypatch):
        mod = self._import_rebuild()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")

        monkeypatch.setattr(mod, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(mod, "TEMPLATE_DIR", REPO_ROOT / "templates")
        monkeypatch.setattr(mod, "STATIC_DIR", REPO_ROOT / "static")
        monkeypatch.setattr(mod, "TOPIC_INTROS_PATH", tmp_path / "tools" / "topic_intros.json")
        monkeypatch.setattr(mod, "COMMENTS_CONFIG_PATH", tmp_path / "tools" / "comments_config.json")
        monkeypatch.setattr(mod, "OG_CONFIG_PATH", tmp_path / "tools" / "og_config.json")
        monkeypatch.setattr(mod, "CITATION_GRAPH_PATH", tmp_path / "citation_graph.json")

        self._setup_article_with_translation(tmp_path, mod, status="published")

        idx = mod.build_index()
        mod.build_site(idx)

        en_path = tmp_path / "site" / "articles" / "test" / "index.html"
        es_path = tmp_path / "site" / "es" / "articles" / "test" / "index.html"
        assert '"en"' in en_path.read_text(encoding="utf-8")
        assert '"es"' in es_path.read_text(encoding="utf-8")

    def test_html_lang_is_dynamic(self, tmp_path, monkeypatch):
        mod = self._import_rebuild()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")

        monkeypatch.setattr(mod, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(mod, "TEMPLATE_DIR", REPO_ROOT / "templates")
        monkeypatch.setattr(mod, "STATIC_DIR", REPO_ROOT / "static")
        monkeypatch.setattr(mod, "TOPIC_INTROS_PATH", tmp_path / "tools" / "topic_intros.json")
        monkeypatch.setattr(mod, "COMMENTS_CONFIG_PATH", tmp_path / "tools" / "comments_config.json")
        monkeypatch.setattr(mod, "OG_CONFIG_PATH", tmp_path / "tools" / "og_config.json")
        monkeypatch.setattr(mod, "CITATION_GRAPH_PATH", tmp_path / "citation_graph.json")

        self._setup_article_with_translation(tmp_path, mod, status="published")

        idx = mod.build_index()
        mod.build_site(idx)

        en_path = tmp_path / "site" / "articles" / "test" / "index.html"
        es_path = tmp_path / "site" / "es" / "articles" / "test" / "index.html"
        assert '<html lang="en"' in en_path.read_text(encoding="utf-8")
        assert '<html lang="es"' in es_path.read_text(encoding="utf-8")

    def test_archive_notice_preserved(self, tmp_path, monkeypatch):
        mod = self._import_rebuild()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")

        monkeypatch.setattr(mod, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(mod, "TEMPLATE_DIR", REPO_ROOT / "templates")
        monkeypatch.setattr(mod, "STATIC_DIR", REPO_ROOT / "static")
        monkeypatch.setattr(mod, "TOPIC_INTROS_PATH", tmp_path / "tools" / "topic_intros.json")
        monkeypatch.setattr(mod, "COMMENTS_CONFIG_PATH", tmp_path / "tools" / "comments_config.json")
        monkeypatch.setattr(mod, "OG_CONFIG_PATH", tmp_path / "tools" / "og_config.json")
        monkeypatch.setattr(mod, "CITATION_GRAPH_PATH", tmp_path / "citation_graph.json")

        self._setup_article_with_translation(tmp_path, mod, status="published")

        idx = mod.build_index()
        mod.build_site(idx)

        es_path = tmp_path / "site" / "es" / "articles" / "test" / "index.html"
        html = es_path.read_text(encoding="utf-8")
        assert "read original at" in html
        assert "example.com" in html

    def test_orphan_translation_no_route(self, tmp_path, monkeypatch):
        mod = self._import_rebuild()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")

        monkeypatch.setattr(mod, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(mod, "TEMPLATE_DIR", REPO_ROOT / "templates")
        monkeypatch.setattr(mod, "STATIC_DIR", REPO_ROOT / "static")
        monkeypatch.setattr(mod, "TOPIC_INTROS_PATH", tmp_path / "tools" / "topic_intros.json")
        monkeypatch.setattr(mod, "COMMENTS_CONFIG_PATH", tmp_path / "tools" / "comments_config.json")
        monkeypatch.setattr(mod, "OG_CONFIG_PATH", tmp_path / "tools" / "og_config.json")
        monkeypatch.setattr(mod, "CITATION_GRAPH_PATH", tmp_path / "citation_graph.json")

        folder, _ = self._setup_article_with_translation(tmp_path, mod, status="published")
        # Remove translations.json but keep article.es.md
        (tmp_path / "articles" / folder / "translations.json").unlink()

        idx = mod.build_index()
        mod.build_site(idx)

        assert not (tmp_path / "site" / "es" / "articles" / "test" / "index.html").exists()

    def test_no_unrelated_articles_get_translated_routes(self, tmp_path, monkeypatch):
        mod = self._import_rebuild()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")

        monkeypatch.setattr(mod, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(mod, "TEMPLATE_DIR", REPO_ROOT / "templates")
        monkeypatch.setattr(mod, "STATIC_DIR", REPO_ROOT / "static")
        monkeypatch.setattr(mod, "TOPIC_INTROS_PATH", tmp_path / "tools" / "topic_intros.json")
        monkeypatch.setattr(mod, "COMMENTS_CONFIG_PATH", tmp_path / "tools" / "comments_config.json")
        monkeypatch.setattr(mod, "OG_CONFIG_PATH", tmp_path / "tools" / "og_config.json")
        monkeypatch.setattr(mod, "CITATION_GRAPH_PATH", tmp_path / "citation_graph.json")

        # Article with translation
        self._setup_article_with_translation(tmp_path, mod, status="published")
        # Article without translation
        folder2 = "2026-04-02-other"
        (tmp_path / "articles" / folder2).mkdir(parents=True)
        meta2 = {
            "folder": folder2,
            "slug": "other",
            "title": "Other Article",
            "published_date": "2026-04-02",
            "canonical_url": "https://example.com/other",
        }
        (tmp_path / "articles" / folder2 / "metadata.json").write_text(json.dumps(meta2), encoding="utf-8")
        (tmp_path / "articles" / folder2 / "article.md").write_text("# Other\n\nBody.\n", encoding="utf-8")

        index = {
            "articles": [
                {
                    "folder": "2026-04-01-test",
                    "slug": "test",
                    "title": "Test Article",
                    "published_date": "2026-04-01",
                    "canonical_url": "https://example.com/test",
                    "topics": ["AI Strategy"],
                },
                {
                    "folder": folder2,
                    "slug": "other",
                    "title": "Other Article",
                    "published_date": "2026-04-02",
                    "canonical_url": "https://example.com/other",
                },
            ]
        }
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        idx = mod.build_index()
        mod.build_site(idx)

        assert (tmp_path / "site" / "es" / "articles" / "test" / "index.html").exists()
        assert not (tmp_path / "site" / "es" / "articles" / "other" / "index.html").exists()

    def test_sitemap_excludes_translated_pages(self, tmp_path, monkeypatch):
        mod = self._import_rebuild()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")

        monkeypatch.setattr(mod, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(mod, "TEMPLATE_DIR", REPO_ROOT / "templates")
        monkeypatch.setattr(mod, "STATIC_DIR", REPO_ROOT / "static")
        monkeypatch.setattr(mod, "TOPIC_INTROS_PATH", tmp_path / "tools" / "topic_intros.json")
        monkeypatch.setattr(mod, "COMMENTS_CONFIG_PATH", tmp_path / "tools" / "comments_config.json")
        monkeypatch.setattr(mod, "OG_CONFIG_PATH", tmp_path / "tools" / "og_config.json")
        monkeypatch.setattr(mod, "CITATION_GRAPH_PATH", tmp_path / "citation_graph.json")

        self._setup_article_with_translation(tmp_path, mod, status="published")

        idx = mod.build_index()
        mod.build_sitemap(idx)

        sitemap = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
        assert "es/articles" not in sitemap
        assert "fr/articles" not in sitemap
