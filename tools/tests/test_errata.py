#!/usr/bin/env python3
"""Tests for errata validation and rendering."""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from _fixtures import *


class TestCheckErrata:
    def test_passes_when_no_errata_files(self, tmp_path, monkeypatch):
        import check_errata as ce
        monkeypatch.setattr(ce, "ARTICLES_DIR", tmp_path / "articles")
        (tmp_path / "articles").mkdir()
        report = ce.validate_all()
        assert report["files_checked"] == 0
        assert report["errors"] == 0
        assert report["entries"] == 0

    def test_valid_errata_file_passes(self, tmp_path, monkeypatch):
        import check_errata as ce
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("errata.md").write_text(
            "# Errata\n\n"
            "## 2026-04-29 — Source link updated\n\n"
            "Type: source-update\n"
            "Status: published\n"
            "Editor: Dr. Hernani Costa\n\n"
            "The original link no longer resolved.\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(ce, "ARTICLES_DIR", articles)
        report = ce.validate_all()
        assert report["files_checked"] == 1
        assert report["entries"] == 1
        assert report["errors"] == 0

    def test_errata_requires_h1(self, tmp_path, monkeypatch):
        import check_errata as ce
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("errata.md").write_text(
            "## 2026-04-29 — Something\n\n"
            "Type: correction\n"
            "Status: published\n"
            "Editor: A\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(ce, "ARTICLES_DIR", articles)
        report = ce.validate_all()
        assert report["errors"] > 0
        assert any("# Errata" in e for e in report["results"][0]["errors"])

    def test_errata_requires_iso_date_heading(self, tmp_path, monkeypatch):
        import check_errata as ce
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("errata.md").write_text(
            "# Errata\n\n"
            "## 29 April 2026 — Bad date\n\n"
            "Type: correction\n"
            "Status: published\n"
            "Editor: A\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(ce, "ARTICLES_DIR", articles)
        report = ce.validate_all()
        assert report["errors"] > 0
        assert any("YYYY-MM-DD" in e for e in report["results"][0]["errors"])

    def test_errata_rejects_unknown_type(self, tmp_path, monkeypatch):
        import check_errata as ce
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("errata.md").write_text(
            "# Errata\n\n"
            "## 2026-04-29 — Something\n\n"
            "Type: typo-fix\n"
            "Status: published\n"
            "Editor: A\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(ce, "ARTICLES_DIR", articles)
        report = ce.validate_all()
        assert report["errors"] > 0
        assert any("invalid type" in e for e in report["results"][0]["errors"])

    def test_errata_rejects_unknown_status(self, tmp_path, monkeypatch):
        import check_errata as ce
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("errata.md").write_text(
            "# Errata\n\n"
            "## 2026-04-29 — Something\n\n"
            "Type: correction\n"
            "Status: pending-review\n"
            "Editor: A\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(ce, "ARTICLES_DIR", articles)
        report = ce.validate_all()
        assert report["errors"] > 0
        assert any("invalid status" in e for e in report["results"][0]["errors"])

    def test_errata_requires_editor(self, tmp_path, monkeypatch):
        import check_errata as ce
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("errata.md").write_text(
            "# Errata\n\n"
            "## 2026-04-29 — Something\n\n"
            "Type: correction\n"
            "Status: published\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(ce, "ARTICLES_DIR", articles)
        report = ce.validate_all()
        assert report["errors"] > 0
        assert any("missing Editor" in e for e in report["results"][0]["errors"])

    def test_draft_errata_does_not_render(self, tmp_path, monkeypatch):
        import check_errata as ce
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("errata.md").write_text(
            "# Errata\n\n"
            "## 2026-04-29 — Draft note\n\n"
            "Type: editorial-note\n"
            "Status: draft\n"
            "Editor: Dr. Hernani Costa\n\n"
            "This is a draft and should not appear.\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(ce, "ARTICLES_DIR", articles)
        report = ce.validate_all()
        assert report["errors"] == 0
        # Draft entries should not be in the validated output
        entries = report["results"][0].get("entries", 0)
        assert entries == 1  # one entry total (draft)

    def test_json_output(self, tmp_path, monkeypatch):
        import check_errata as ce
        articles = tmp_path / "articles"
        articles.mkdir()
        folder = articles / "2026-04-01-test"
        folder.mkdir()
        folder.joinpath("errata.md").write_text(
            "# Errata\n\n"
            "## 2026-04-29 — Source link updated\n\n"
            "Type: source-update\n"
            "Status: published\n"
            "Editor: Dr. Hernani Costa\n\n"
            "The original link no longer resolved.\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(ce, "ARTICLES_DIR", articles)
        report = ce.validate_all()
        assert report["files_checked"] == 1
        assert report["entries"] == 1
        assert report["errors"] == 0
        assert report["results"][0]["folder"] == "2026-04-01-test"


class TestErrataRendering:
    def _mod(self):
        pytest.importorskip("jinja2")
        pytest.importorskip("markdown")
        import rebuild_local
        return rebuild_local

    def _synthetic_index(self, n=1):
        articles = []
        for i in range(n):
            day = 20 - i
            articles.append({
                "folder": f"2026-04-{day:02d}-article-{i}",
                "slug": f"article-{i}",
                "title": f"Test Article {i}",
                "published_date": f"2026-04-{day:02d}",
                "tags": ["AI Strategy"],
                "topics": ["AI Strategy", "European SME AI"],
                "funnel_stage": "middle",
                "canonical_url": f"https://radar.firstaimovers.com/article-{i}",
            })
        return {"articles": articles}

    def _run(self, monkeypatch, tmp_path, index, with_errata=False):
        m = self._mod()
        monkeypatch.setenv("INDEXNOW_API_KEY_ARTICLES_FAIM", "")
        out = tmp_path / "site"
        out.mkdir()
        articles = tmp_path / "articles"
        articles.mkdir()
        static = tmp_path / "static"
        static.mkdir()
        templates = tmp_path / "templates"
        templates.mkdir()
        real_root = Path(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", templates, dirs_exist_ok=True)
        shutil.copytree(real_root / "static", static, dirs_exist_ok=True)

        for art in index.get("articles", []):
            folder = articles / art["folder"]
            folder.mkdir()
            folder.joinpath("article.md").write_text(
                f'---\ntitle: "{art["title"]}"\npublished_date: "{art["published_date"]}"\ncanonical_url: "{art["canonical_url"]}"\n---\n\n# {art["title"]}\n\nBody text.\n',
                encoding="utf-8",
            )
            if with_errata:
                folder.joinpath("errata.md").write_text(
                    "# Errata\n\n"
                    "## 2026-04-29 — Source link updated\n\n"
                    "Type: source-update\n"
                    "Status: published\n"
                    "Editor: Dr. Hernani Costa\n\n"
                    "The original link no longer resolved.\n",
                    encoding="utf-8",
                )

        idx_path = tmp_path / "index.json"
        idx_path.write_text(json.dumps(index), encoding="utf-8")
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", articles)
        monkeypatch.setattr(m, "SITE_DIR", out)
        monkeypatch.setattr(m, "STATIC_DIR", static)
        monkeypatch.setattr(m, "TEMPLATE_DIR", templates)
        m.build_site(index)
        return out

    def test_published_errata_renders_on_article_page(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1), with_errata=True)
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert '<aside class="errata"' in page
        assert "Corrections and editorial notes" in page
        assert "Source link updated" in page
        assert "Source Update" in page or "source update" in page.lower()
        assert "Dr. Hernani Costa" in page

    def test_article_without_errata_has_no_errata_aside(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1), with_errata=False)
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert '<aside class="errata"' not in page
        assert "Corrections and editorial notes" not in page

    def test_draft_errata_not_rendered(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.setenv("INDEXNOW_API_KEY_ARTICLES_FAIM", "")
        out = tmp_path / "site"
        out.mkdir()
        articles = tmp_path / "articles"
        articles.mkdir()
        static = tmp_path / "static"
        static.mkdir()
        templates = tmp_path / "templates"
        templates.mkdir()
        real_root = Path(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", templates, dirs_exist_ok=True)
        shutil.copytree(real_root / "static", static, dirs_exist_ok=True)

        index = self._synthetic_index(1)
        art = index["articles"][0]
        folder = articles / art["folder"]
        folder.mkdir()
        folder.joinpath("article.md").write_text(
            f'---\ntitle: "{art["title"]}"\npublished_date: "{art["published_date"]}"\ncanonical_url: "{art["canonical_url"]}"\n---\n\n# {art["title"]}\n\nBody text.\n',
            encoding="utf-8",
        )
        folder.joinpath("errata.md").write_text(
            "# Errata\n\n"
            "## 2026-04-29 — Draft note\n\n"
            "Type: editorial-note\n"
            "Status: draft\n"
            "Editor: Dr. Hernani Costa\n\n"
            "This is a draft.\n",
            encoding="utf-8",
        )

        idx_path = tmp_path / "index.json"
        idx_path.write_text(json.dumps(index), encoding="utf-8")
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", articles)
        monkeypatch.setattr(m, "SITE_DIR", out)
        monkeypatch.setattr(m, "STATIC_DIR", static)
        monkeypatch.setattr(m, "TEMPLATE_DIR", templates)
        m.build_site(index)

        page = (out / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert '<aside class="errata"' not in page
        assert "Draft note" not in page


class TestErrataDocs:
    def test_errata_docs_exist(self):
        path = Path(__file__).resolve().parents[2] / "docs" / "ERRATA.md"
        assert path.exists(), "docs/ERRATA.md should exist"
        text = path.read_text(encoding="utf-8")
        assert "immutable" in text.lower()
        assert "correction" in text.lower()

    def test_contributing_mentions_errata_policy(self):
        path = Path(__file__).resolve().parents[2] / "CONTRIBUTING.md"
        text = path.read_text(encoding="utf-8")
        assert "errata" in text.lower()
        assert "ERRATA.md" in text
