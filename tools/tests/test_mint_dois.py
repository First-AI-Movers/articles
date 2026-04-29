#!/usr/bin/env python3
"""Tests for E34 per-article DOI infrastructure.

Covers:
- Schema validation for optional DOI field
- Index build behavior with/without DOI
- Article page rendering (cite block, JSON-LD)
- mint_dois.py dry-run, sandbox, and mocked write modes
- Production safety flag
- CSL JSON and JSON-LD validity
"""

import json
import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTICLE_SCHEMA = REPO_ROOT / "tools" / "article_schema.json"
MINT_DOIS = REPO_ROOT / "tools" / "mint_dois.py"


# =========================================================================
# Schema tests
# =========================================================================

class TestSchema:
    def test_schema_allows_optional_doi(self):
        schema = json.loads(ARTICLE_SCHEMA.read_text(encoding="utf-8"))
        assert "doi" in schema["properties"]
        assert schema["properties"]["doi"]["type"] == "string"

    def test_schema_rejects_invalid_doi(self):
        schema = json.loads(ARTICLE_SCHEMA.read_text(encoding="utf-8"))
        pattern = schema["properties"]["doi"]["pattern"]
        # Valid DOIs should match
        assert re.match(pattern, "10.5281/zenodo.1234567")
        # Invalid should not match
        assert not re.match(pattern, "not-a-doi")
        assert not re.match(pattern, "doi:10.5281/zenodo.1234567")


# =========================================================================
# Index tests
# =========================================================================

class TestIndex:
    def test_index_includes_doi_when_present(self, tmp_path, monkeypatch):
        import rebuild_local
        monkeypatch.setattr(rebuild_local, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(rebuild_local, "ARTICLES_DIR", tmp_path / "articles")
        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
            "doi": "10.5281/zenodo.1234567",
        }
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )
        index = rebuild_local.build_index()
        article = index["articles"][0]
        assert article.get("doi") == "10.5281/zenodo.1234567"

    def test_index_omits_doi_when_absent(self, tmp_path, monkeypatch):
        import rebuild_local
        monkeypatch.setattr(rebuild_local, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(rebuild_local, "ARTICLES_DIR", tmp_path / "articles")
        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
        }
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )
        index = rebuild_local.build_index()
        article = index["articles"][0]
        assert "doi" not in article


# =========================================================================
# Article page rendering tests
# =========================================================================

class TestArticlePageRendering:
    """Test per-article page rendering with/without DOI."""

    def _mod(self):
        pytest.importorskip("jinja2")
        pytest.importorskip("markdown")
        import rebuild_local
        return rebuild_local

    def _run(self, monkeypatch, tmp_path, article_meta):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        from pathlib import Path as P
        real_root = P(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")

        folder = article_meta.get("folder", "2026-04-01-test")
        (tmp_path / "articles" / folder).mkdir(exist_ok=True)
        (tmp_path / "articles" / folder / "article.md").write_text(
            '---\ntitle: "Test"\n---\n# Test\n\nBody.\n', encoding="utf-8"
        )
        (tmp_path / "articles" / folder / "metadata.json").write_text(
            json.dumps(article_meta), encoding="utf-8"
        )

        index = {"articles": [article_meta]}
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return tmp_path / "site"

    def _jsonld_from_page(self, page_html):
        match = re.search(r'<script type="application/ld\+json">(.*?)</script>', page_html, re.DOTALL)
        assert match is not None, "No JSON-LD found in page"
        return json.loads(match.group(1))

    def test_article_page_renders_cite_block_when_doi_exists(self, monkeypatch, tmp_path):
        article = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test Article",
            "published_date": "2026-04-01",
            "tags": ["AI Strategy"],
            "topics": ["AI Strategy"],
            "funnel_stage": "middle",
            "canonical_url": "https://radar.firstaimovers.com/test",
            "doi": "10.5281/zenodo.1234567",
        }
        site = self._run(monkeypatch, tmp_path, article)
        page = (site / "articles" / "test" / "index.html").read_text(encoding="utf-8")
        assert 'class="cite-block"' in page
        assert "Cite this article" in page
        assert "10.5281/zenodo.1234567" in page
        assert "APA" in page
        assert "BibTeX" in page
        assert "CSL JSON" in page

    def test_article_page_hides_cite_block_when_doi_absent(self, monkeypatch, tmp_path):
        article = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test Article",
            "published_date": "2026-04-01",
            "tags": ["AI Strategy"],
            "topics": ["AI Strategy"],
            "funnel_stage": "middle",
            "canonical_url": "https://radar.firstaimovers.com/test",
        }
        site = self._run(monkeypatch, tmp_path, article)
        page = (site / "articles" / "test" / "index.html").read_text(encoding="utf-8")
        assert 'class="cite-block"' not in page
        assert "Cite this article" not in page

    def test_article_page_jsonld_includes_identifier_when_doi_exists(self, monkeypatch, tmp_path):
        article = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test Article",
            "published_date": "2026-04-01",
            "tags": ["AI Strategy"],
            "topics": ["AI Strategy"],
            "funnel_stage": "middle",
            "canonical_url": "https://radar.firstaimovers.com/test",
            "doi": "10.5281/zenodo.1234567",
        }
        site = self._run(monkeypatch, tmp_path, article)
        page = (site / "articles" / "test" / "index.html").read_text(encoding="utf-8")
        data = self._jsonld_from_page(page)
        assert data["identifier"]["@type"] == "PropertyValue"
        assert data["identifier"]["propertyID"] == "DOI"
        assert data["identifier"]["value"] == "10.5281/zenodo.1234567"
        assert data["sameAs"] == "https://doi.org/10.5281/zenodo.1234567"

    def test_article_page_jsonld_omits_doi_fields_when_absent(self, monkeypatch, tmp_path):
        article = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test Article",
            "published_date": "2026-04-01",
            "tags": ["AI Strategy"],
            "topics": ["AI Strategy"],
            "funnel_stage": "middle",
            "canonical_url": "https://radar.firstaimovers.com/test",
        }
        site = self._run(monkeypatch, tmp_path, article)
        page = (site / "articles" / "test" / "index.html").read_text(encoding="utf-8")
        data = self._jsonld_from_page(page)
        assert "identifier" not in data
        assert "sameAs" not in data

    def test_article_jsonld_valid_with_doi_only(self, monkeypatch, tmp_path):
        article = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test Article",
            "published_date": "2026-04-01",
            "tags": [],
            "topics": [],
            "funnel_stage": "middle",
            "canonical_url": "https://radar.firstaimovers.com/test",
            "doi": "10.5281/zenodo.1234567",
        }
        site = self._run(monkeypatch, tmp_path, article)
        page = (site / "articles" / "test" / "index.html").read_text(encoding="utf-8")
        data = self._jsonld_from_page(page)
        assert data["@type"] == "Article"
        assert data["identifier"]["value"] == "10.5281/zenodo.1234567"

    def test_article_jsonld_valid_with_doi_and_series(self, monkeypatch, tmp_path):
        article = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test Article",
            "published_date": "2026-04-01",
            "tags": [],
            "topics": ["AI Strategy"],
            "funnel_stage": "middle",
            "canonical_url": "https://radar.firstaimovers.com/test",
            "doi": "10.5281/zenodo.1234567",
            "series": "test-series",
            "series_order": 1,
        }
        # Create series registry
        registry = {"series": {"test-series": {"title": "Test Series", "description": "Desc"}}}
        (tmp_path / "tools").mkdir(exist_ok=True)
        (tmp_path / "tools" / "series_registry.json").write_text(json.dumps(registry), encoding="utf-8")
        site = self._run(monkeypatch, tmp_path, article)
        page = (site / "articles" / "test" / "index.html").read_text(encoding="utf-8")
        data = self._jsonld_from_page(page)
        assert data["identifier"]["value"] == "10.5281/zenodo.1234567"
        assert data["isPartOf"]["name"] == "Test Series"

    def test_article_jsonld_valid_without_doi(self, monkeypatch, tmp_path):
        article = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test Article",
            "published_date": "2026-04-01",
            "tags": [],
            "topics": [],
            "funnel_stage": "middle",
            "canonical_url": "https://radar.firstaimovers.com/test",
        }
        site = self._run(monkeypatch, tmp_path, article)
        page = (site / "articles" / "test" / "index.html").read_text(encoding="utf-8")
        data = self._jsonld_from_page(page)
        assert data["@type"] == "Article"
        assert "identifier" not in data
        assert "sameAs" not in data

    def test_csl_json_parses_as_valid_json(self, monkeypatch, tmp_path):
        import rebuild_local
        csl = rebuild_local._build_csl_json("Test Title", "2026-04-01", "10.5281/zenodo.1234567")
        data = json.loads(csl)
        assert data["type"] == "article"
        assert data["DOI"] == "10.5281/zenodo.1234567"

    def test_bibtex_contains_required_fields(self, monkeypatch, tmp_path):
        import rebuild_local
        bib = rebuild_local._build_bibtex("Test Title", "test-slug", "2026-04-01", "10.5281/zenodo.1234567")
        assert "@article{costa_test_slug" in bib
        assert "Test Title" in bib
        assert "2026" in bib
        assert "10.5281/zenodo.1234567" in bib


# =========================================================================
# mint_dois.py tool tests
# =========================================================================

class TestMintDoisTool:
    def _import_module(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("mint_dois", MINT_DOIS)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["mint_dois"] = mod
        spec.loader.exec_module(mod)
        return mod

    def test_mint_tool_dry_run_does_not_modify_metadata(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
        }
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-test" / "article.md").write_text(
            "# Test\n\nBody.\n", encoding="utf-8"
        )
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        result = mod.main(["--dry-run", "--slug", "test"])
        assert result == 0
        # metadata.json should be unchanged
        after = json.loads((tmp_path / "articles" / "2026-04-01-test" / "metadata.json").read_text(encoding="utf-8"))
        assert "doi" not in after

    def test_mint_tool_requires_token_in_write_mode(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")
        monkeypatch.delenv("ZENODO_API_TOKEN", raising=False)
        monkeypatch.delenv("ZENODO_SANDBOX_API_TOKEN", raising=False)

        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
        }
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-test" / "article.md").write_text(
            "# Test\n\nBody.\n", encoding="utf-8"
        )
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        with pytest.raises(SystemExit) as excinfo:
            mod.main(["--write", "--slug", "test"])
        assert excinfo.value.code == 1

    def test_sandbox_endpoint_selected_with_sandbox_flag(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")
        monkeypatch.setenv("ZENODO_SANDBOX_API_TOKEN", "fake-token")

        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
        }
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-test" / "article.md").write_text(
            "# Test\n\nBody.\n", encoding="utf-8"
        )
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        calls = []
        def fake_api_call(method, url, token, **kwargs):
            calls.append(url)
            return 200, {"id": 1, "links": {"bucket": "https://sandbox.zenodo.org/api/files/123"}, "metadata": {"prereserve_doi": {"doi": "10.5072/zenodo.1"}}}, {}

        monkeypatch.setattr(mod, "_api_call", fake_api_call)
        import requests
        monkeypatch.setattr(requests, "put", lambda *args, **kwargs: type("R", (), {"status_code": 201, "text": "ok"})())

        result = mod.main(["--sandbox", "--write", "--no-publish", "--slug", "test"])
        assert result == 0
        assert any("sandbox.zenodo.org" in u for u in calls)

    def test_production_endpoint_selected_without_sandbox(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")
        monkeypatch.setenv("ZENODO_API_TOKEN", "fake-token")

        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
        }
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-test" / "article.md").write_text(
            "# Test\n\nBody.\n", encoding="utf-8"
        )
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        calls = []
        def fake_api_call(method, url, token, **kwargs):
            calls.append(url)
            return 200, {"id": 1, "links": {"bucket": "https://zenodo.org/api/files/123"}, "metadata": {"prereserve_doi": {"doi": "10.5281/zenodo.1"}}}, {}

        monkeypatch.setattr(mod, "_api_call", fake_api_call)
        import requests
        monkeypatch.setattr(requests, "put", lambda *args, **kwargs: type("R", (), {"status_code": 201, "text": "ok"})())

        result = mod.main([
            "--write",
            "--yes-i-understand-production-dois-are-permanent",
            "--no-publish",
            "--slug", "test",
        ])
        assert result == 0
        assert any("zenodo.org/api" in u and "sandbox" not in u for u in calls)

    def test_production_write_blocked_without_explicit_flag(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")
        monkeypatch.setenv("ZENODO_API_TOKEN", "fake-token")

        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
        }
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-test" / "article.md").write_text(
            "# Test\n\nBody.\n", encoding="utf-8"
        )
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        with pytest.raises(SystemExit) as excinfo:
            mod.main(["--write", "--slug", "test"])
        assert excinfo.value.code == 1

    def test_payload_includes_publication_type_article(self):
        mod = self._import_module()
        article = {
            "title": "Test",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
            "local_path": "/articles/test/",
            "summary": "Summary",
            "tldr": None,
            "topics": ["AI Strategy"],
            "tags": [],
        }
        payload = mod._build_zenodo_payload(article)
        assert payload["metadata"]["upload_type"] == "publication"
        assert payload["metadata"]["publication_type"] == "article"

    def test_payload_includes_related_identifiers(self):
        mod = self._import_module()
        article = {
            "title": "Test",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
            "local_path": "/articles/test/",
            "summary": "Summary",
            "tldr": None,
            "topics": ["AI Strategy"],
            "tags": [],
        }
        payload = mod._build_zenodo_payload(article)
        rels = payload["metadata"]["related_identifiers"]
        assert any(r["relation"] == "isIdenticalTo" and r["identifier"] == "https://example.com" for r in rels)
        assert any(r["relation"] == "isArchivedBy" and "articles.firstaimovers.com" in r["identifier"] for r in rels)

    def test_successful_mocked_publish_writes_doi_atomically(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")
        monkeypatch.setenv("ZENODO_SANDBOX_API_TOKEN", "fake-token")

        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
        }
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-test" / "article.md").write_text(
            "# Test\n\nBody.\n", encoding="utf-8"
        )
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        def fake_api_call(method, url, token, **kwargs):
            if "actions/publish" in url:
                return 202, {"id": 1, "doi": "10.5072/zenodo.999", "metadata": {"doi": "10.5072/zenodo.999"}}, {}
            return 200, {"id": 1, "links": {"bucket": "https://sandbox.zenodo.org/api/files/123"}, "metadata": {"prereserve_doi": {"doi": "10.5072/zenodo.1"}}}, {}

        monkeypatch.setattr(mod, "_api_call", fake_api_call)
        import requests
        monkeypatch.setattr(requests, "put", lambda *args, **kwargs: type("R", (), {"status_code": 201, "text": "ok"})())

        result = mod.main(["--sandbox", "--write", "--slug", "test"])
        assert result == 0
        after = json.loads((tmp_path / "articles" / "2026-04-01-test" / "metadata.json").read_text(encoding="utf-8"))
        assert after.get("doi") == "10.5072/zenodo.999"

    def test_failed_mocked_publish_does_not_write_doi(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")
        monkeypatch.setenv("ZENODO_SANDBOX_API_TOKEN", "fake-token")

        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
        }
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-test" / "article.md").write_text(
            "# Test\n\nBody.\n", encoding="utf-8"
        )
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        def fake_api_call(method, url, token, **kwargs):
            if "actions/publish" in url:
                return 500, {"message": "Internal Server Error"}, {}
            return 200, {"id": 1, "links": {"bucket": "https://sandbox.zenodo.org/api/files/123"}, "metadata": {"prereserve_doi": {"doi": "10.5072/zenodo.1"}}}, {}

        monkeypatch.setattr(mod, "_api_call", fake_api_call)
        import requests
        monkeypatch.setattr(requests, "put", lambda *args, **kwargs: type("R", (), {"status_code": 201, "text": "ok"})())

        result = mod.main(["--sandbox", "--write", "--slug", "test"])
        assert result == 1
        after = json.loads((tmp_path / "articles" / "2026-04-01-test" / "metadata.json").read_text(encoding="utf-8"))
        assert "doi" not in after

    def test_no_publish_does_not_write_doi_to_metadata(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")
        monkeypatch.setenv("ZENODO_SANDBOX_API_TOKEN", "fake-token")

        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
        }
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-test" / "article.md").write_text(
            "# Test\n\nBody.\n", encoding="utf-8"
        )
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        def fake_api_call(method, url, token, **kwargs):
            return 200, {"id": 1, "links": {"bucket": "https://sandbox.zenodo.org/api/files/123"}, "metadata": {"prereserve_doi": {"doi": "10.5072/zenodo.1"}}}, {}

        monkeypatch.setattr(mod, "_api_call", fake_api_call)
        import requests
        monkeypatch.setattr(requests, "put", lambda *args, **kwargs: type("R", (), {"status_code": 201, "text": "ok"})())

        result = mod.main(["--sandbox", "--write", "--no-publish", "--slug", "test"])
        assert result == 0
        after = json.loads((tmp_path / "articles" / "2026-04-01-test" / "metadata.json").read_text(encoding="utf-8"))
        assert "doi" not in after

    def test_mocked_bucket_upload_uses_links_bucket(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")
        monkeypatch.setenv("ZENODO_SANDBOX_API_TOKEN", "fake-token")

        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        meta = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Test",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
        }
        (tmp_path / "articles" / "2026-04-01-test" / "metadata.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-test" / "article.md").write_text(
            "# Test\n\nBody.\n", encoding="utf-8"
        )
        index = {"articles": [meta]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        bucket_urls = []
        def fake_api_call(method, url, token, **kwargs):
            return 200, {"id": 1, "links": {"bucket": "https://sandbox.zenodo.org/api/files/abc123"}, "metadata": {"prereserve_doi": {"doi": "10.5072/zenodo.1"}}}, {}

        monkeypatch.setattr(mod, "_api_call", fake_api_call)
        import requests
        original_put = requests.put
        def capture_put(url, *args, **kwargs):
            bucket_urls.append(url)
            return type("R", (), {"status_code": 201, "text": "ok"})()
        monkeypatch.setattr(requests, "put", capture_put)

        result = mod.main(["--sandbox", "--write", "--no-publish", "--slug", "test"])
        assert result == 0
        assert any("sandbox.zenodo.org/api/files/abc123" in u for u in bucket_urls)

    def test_no_existing_article_metadata_modified(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(mod, "INDEX_PATH", tmp_path / "index.json")

        # Article A: no DOI, should stay untouched
        (tmp_path / "articles" / "2026-04-01-a").mkdir(parents=True)
        meta_a = {"folder": "2026-04-01-a", "slug": "a", "title": "A", "published_date": "2026-04-01", "canonical_url": "https://example.com/a"}
        (tmp_path / "articles" / "2026-04-01-a" / "metadata.json").write_text(json.dumps(meta_a), encoding="utf-8")
        (tmp_path / "articles" / "2026-04-01-a" / "article.md").write_text("# A\n", encoding="utf-8")

        # Article B: already has DOI, should stay untouched
        (tmp_path / "articles" / "2026-04-01-b").mkdir(parents=True)
        meta_b = {"folder": "2026-04-01-b", "slug": "b", "title": "B", "published_date": "2026-04-01", "canonical_url": "https://example.com/b", "doi": "10.5281/zenodo.999"}
        (tmp_path / "articles" / "2026-04-01-b" / "metadata.json").write_text(json.dumps(meta_b), encoding="utf-8")
        (tmp_path / "articles" / "2026-04-01-b" / "article.md").write_text("# B\n", encoding="utf-8")

        index = {"articles": [meta_a, meta_b]}
        (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

        result = mod.main(["--dry-run", "--slug", "a"])
        assert result == 0
        after_a = json.loads((tmp_path / "articles" / "2026-04-01-a" / "metadata.json").read_text(encoding="utf-8"))
        after_b = json.loads((tmp_path / "articles" / "2026-04-01-b" / "metadata.json").read_text(encoding="utf-8"))
        assert "doi" not in after_a
        assert after_b.get("doi") == "10.5281/zenodo.999"

    def test_snapshot_includes_header_and_original_body(self, tmp_path, monkeypatch):
        mod = self._import_module()
        monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
        (tmp_path / "articles" / "2026-04-01-test").mkdir(parents=True)
        (tmp_path / "articles" / "2026-04-01-test" / "article.md").write_text(
            "# Original Title\n\nOriginal body.\n", encoding="utf-8"
        )
        article = {
            "folder": "2026-04-01-test",
            "slug": "test",
            "title": "Original Title",
            "published_date": "2026-04-01",
            "canonical_url": "https://example.com",
            "local_path": "/articles/test/",
            "author": "Dr. Hernani Costa",
            "license": "CC BY 4.0",
        }
        snapshot = mod._article_snapshot_content(article)
        assert "# Original Title" in snapshot
        assert "Original body." in snapshot
        assert "**Canonical URL:** https://example.com" in snapshot
        assert "**Local archive URL:** https://articles.firstaimovers.com/articles/test/" in snapshot
