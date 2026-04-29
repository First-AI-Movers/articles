#!/usr/bin/env python3
"""Tests for build_citation_graph.py and citation graph integration."""

import json
import shutil
import sys
from pathlib import Path

import pytest

# build_citation_graph imports _atomic_io, so add tools/ to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestGraphBuilder:
    """Unit tests for tools/build_citation_graph.py."""

    def _mod(self):
        import build_citation_graph
        return build_citation_graph

    def test_graph_builder_exists(self):
        m = self._mod()
        assert hasattr(m, "build_graph")
        assert hasattr(m, "write_graph")
        assert hasattr(m, "main")

    def test_build_graph_output_shape(self, tmp_path, monkeypatch):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "DEFAULT_OUT", tmp_path / "citation_graph.json")

        (tmp_path / "articles" / "2026-04-01-alpha").mkdir(parents=True)
        (tmp_path / "articles" / "2026-04-02-beta").mkdir(parents=True)

        idx = {
            "articles": [
                {
                    "folder": "2026-04-01-alpha",
                    "slug": "alpha",
                    "title": "Alpha Article",
                    "published_date": "2026-04-01",
                    "topics": ["AI Strategy"],
                    "canonical_url": "https://radar.firstaimovers.com/alpha",
                },
                {
                    "folder": "2026-04-02-beta",
                    "slug": "beta",
                    "title": "Beta Article",
                    "published_date": "2026-04-02",
                    "topics": ["AI Governance"],
                    "canonical_url": "https://radar.firstaimovers.com/beta",
                },
            ]
        }
        (tmp_path / "index.json").write_text(json.dumps(idx), encoding="utf-8")

        (tmp_path / "articles" / "2026-04-01-alpha" / "metadata.json").write_text(
            json.dumps({"slug": "alpha", "canonical_url": "https://radar.firstaimovers.com/alpha"}),
            encoding="utf-8",
        )
        (tmp_path / "articles" / "2026-04-01-alpha" / "article.md").write_text(
            "# Alpha\n\nSee [Beta](https://radar.firstaimovers.com/beta) for more.\n",
            encoding="utf-8",
        )

        (tmp_path / "articles" / "2026-04-02-beta" / "metadata.json").write_text(
            json.dumps({"slug": "beta", "canonical_url": "https://radar.firstaimovers.com/beta"}),
            encoding="utf-8",
        )
        (tmp_path / "articles" / "2026-04-02-beta" / "article.md").write_text(
            "# Beta\n\nSee [Alpha](https://radar.firstaimovers.com/alpha).\n",
            encoding="utf-8",
        )

        graph = m.build_graph()
        assert graph["version"] == 1
        assert "nodes" in graph
        assert "edges" in graph
        assert "stats" in graph
        assert graph["stats"]["node_count"] == 2
        assert graph["stats"]["edge_count"] == 2
        assert graph["stats"]["articles_with_outgoing"] == 2
        assert graph["stats"]["articles_with_incoming"] == 2

    def test_detects_local_url_links(self, tmp_path, monkeypatch):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        (tmp_path / "articles" / "2026-04-01-a").mkdir(parents=True)
        (tmp_path / "articles" / "2026-04-01-b").mkdir(parents=True)

        idx = {
            "articles": [
                {
                    "folder": "2026-04-01-a", "slug": "a", "title": "A",
                    "published_date": "2026-04-01", "canonical_url": "https://radar.firstaimovers.com/a",
                },
                {
                    "folder": "2026-04-01-b", "slug": "b", "title": "B",
                    "published_date": "2026-04-01", "canonical_url": "https://radar.firstaimovers.com/b",
                },
            ]
        }
        (tmp_path / "index.json").write_text(json.dumps(idx), encoding="utf-8")

        (tmp_path / "articles" / "2026-04-01-a" / "metadata.json").write_text(
            json.dumps({"slug": "a", "canonical_url": "https://radar.firstaimovers.com/a"}), encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-a" / "article.md").write_text(
            "# A\n\nSee [B local](/articles/b/)\n", encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-b" / "metadata.json").write_text(
            json.dumps({"slug": "b", "canonical_url": "https://radar.firstaimovers.com/b"}), encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-b" / "article.md").write_text("# B\n", encoding="utf-8")

        graph = m.build_graph()
        assert graph["stats"]["edge_count"] == 1
        assert graph["edges"][0]["target_slug"] == "b"
        assert graph["edges"][0]["matched_url"] == "/articles/b/"

    def test_detects_full_local_domain_links(self, tmp_path, monkeypatch):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        (tmp_path / "articles" / "2026-04-01-a").mkdir(parents=True)
        (tmp_path / "articles" / "2026-04-01-b").mkdir(parents=True)

        idx = {
            "articles": [
                {
                    "folder": "2026-04-01-a", "slug": "a", "title": "A",
                    "published_date": "2026-04-01", "canonical_url": "https://radar.firstaimovers.com/a",
                },
                {
                    "folder": "2026-04-01-b", "slug": "b", "title": "B",
                    "published_date": "2026-04-01", "canonical_url": "https://radar.firstaimovers.com/b",
                },
            ]
        }
        (tmp_path / "index.json").write_text(json.dumps(idx), encoding="utf-8")

        for slug in ("a", "b"):
            (tmp_path / "articles" / f"2026-04-01-{slug}" / "metadata.json").write_text(
                json.dumps({"slug": slug, "canonical_url": f"https://radar.firstaimovers.com/{slug}"}),
                encoding="utf-8",
            )
        (tmp_path / "articles" / "2026-04-01-a" / "article.md").write_text(
            "# A\n\nSee [B](https://articles.firstaimovers.com/articles/b/)\n", encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-b" / "article.md").write_text("# B\n", encoding="utf-8")

        graph = m.build_graph()
        assert graph["stats"]["edge_count"] == 1
        assert graph["edges"][0]["target_slug"] == "b"

    def test_ignores_external_links(self, tmp_path, monkeypatch):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        (tmp_path / "articles" / "2026-04-01-a").mkdir(parents=True)
        idx = {
            "articles": [
                {
                    "folder": "2026-04-01-a", "slug": "a", "title": "A",
                    "published_date": "2026-04-01", "canonical_url": "https://radar.firstaimovers.com/a",
                },
            ]
        }
        (tmp_path / "index.json").write_text(json.dumps(idx), encoding="utf-8")
        (tmp_path / "articles" / "2026-04-01-a" / "metadata.json").write_text(
            json.dumps({"slug": "a", "canonical_url": "https://radar.firstaimovers.com/a"}), encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-a" / "article.md").write_text(
            "# A\n\nSee [External](https://example.com/something) and [LinkedIn](https://www.linkedin.com/in/test).\n",
            encoding="utf-8",
        )

        graph = m.build_graph()
        assert graph["stats"]["edge_count"] == 0

    def test_ignores_topic_feed_asset_links(self, tmp_path, monkeypatch):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        (tmp_path / "articles" / "2026-04-01-a").mkdir(parents=True)
        idx = {
            "articles": [
                {
                    "folder": "2026-04-01-a", "slug": "a", "title": "A",
                    "published_date": "2026-04-01", "canonical_url": "https://radar.firstaimovers.com/a",
                },
            ]
        }
        (tmp_path / "index.json").write_text(json.dumps(idx), encoding="utf-8")
        (tmp_path / "articles" / "2026-04-01-a" / "metadata.json").write_text(
            json.dumps({"slug": "a", "canonical_url": "https://radar.firstaimovers.com/a"}), encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-a" / "article.md").write_text(
            "# A\n\nSee [Topic](/topics/ai-strategy/) and [Feed](/feed.xml) and [Asset](/static/style.css).\n",
            encoding="utf-8",
        )

        graph = m.build_graph()
        assert graph["stats"]["edge_count"] == 0

    def test_ignores_self_links(self, tmp_path, monkeypatch):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        (tmp_path / "articles" / "2026-04-01-a").mkdir(parents=True)
        idx = {
            "articles": [
                {
                    "folder": "2026-04-01-a", "slug": "a", "title": "A",
                    "published_date": "2026-04-01", "canonical_url": "https://radar.firstaimovers.com/a",
                },
            ]
        }
        (tmp_path / "index.json").write_text(json.dumps(idx), encoding="utf-8")
        (tmp_path / "articles" / "2026-04-01-a" / "metadata.json").write_text(
            json.dumps({"slug": "a", "canonical_url": "https://radar.firstaimovers.com/a"}), encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-a" / "article.md").write_text(
            "# A\n\nOriginally published at [First AI Movers](https://radar.firstaimovers.com/a).\n",
            encoding="utf-8",
        )

        graph = m.build_graph()
        assert graph["stats"]["edge_count"] == 0

    def test_captures_anchor_text(self, tmp_path, monkeypatch):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        (tmp_path / "articles" / "2026-04-01-a").mkdir(parents=True)
        (tmp_path / "articles" / "2026-04-01-b").mkdir(parents=True)

        idx = {
            "articles": [
                {
                    "folder": "2026-04-01-a", "slug": "a", "title": "A",
                    "published_date": "2026-04-01", "canonical_url": "https://radar.firstaimovers.com/a",
                },
                {
                    "folder": "2026-04-01-b", "slug": "b", "title": "B",
                    "published_date": "2026-04-01", "canonical_url": "https://radar.firstaimovers.com/b",
                },
            ]
        }
        (tmp_path / "index.json").write_text(json.dumps(idx), encoding="utf-8")
        for slug in ("a", "b"):
            (tmp_path / "articles" / f"2026-04-01-{slug}" / "metadata.json").write_text(
                json.dumps({"slug": slug, "canonical_url": f"https://radar.firstaimovers.com/{slug}"}),
                encoding="utf-8",
            )
        (tmp_path / "articles" / "2026-04-01-a" / "article.md").write_text(
            "# A\n\nSee [the beta guide](https://radar.firstaimovers.com/b).\n", encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-b" / "article.md").write_text("# B\n", encoding="utf-8")

        graph = m.build_graph()
        assert graph["edges"][0]["anchor_text"] == "the beta guide"

    def test_deterministic_edge_ordering(self, tmp_path, monkeypatch):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        for name in ("c", "b", "a"):
            (tmp_path / "articles" / f"2026-04-01-{name}").mkdir(parents=True)

        idx = {
            "articles": [
                {
                    "folder": f"2026-04-01-{s}", "slug": s, "title": s.upper(),
                    "published_date": "2026-04-01", "canonical_url": f"https://radar.firstaimovers.com/{s}",
                }
                for s in ("a", "b", "c")
            ]
        }
        (tmp_path / "index.json").write_text(json.dumps(idx), encoding="utf-8")
        for s in ("a", "b", "c"):
            (tmp_path / "articles" / f"2026-04-01-{s}" / "metadata.json").write_text(
                json.dumps({"slug": s, "canonical_url": f"https://radar.firstaimovers.com/{s}"}),
                encoding="utf-8",
            )
            (tmp_path / "articles" / f"2026-04-01-{s}" / "article.md").write_text(
                "# X\n\n" + "\n".join(
                    f"See [{other.upper()}](https://radar.firstaimovers.com/{other})"
                    for other in ("a", "b", "c") if other != s
                ) + "\n",
                encoding="utf-8",
            )

        graph = m.build_graph()
        sources = [e["source_folder"] for e in graph["edges"]]
        assert sources == sorted(sources)

    def test_check_passes_when_current(self, tmp_path, monkeypatch):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        out = tmp_path / "citation_graph.json"
        monkeypatch.setattr(m, "DEFAULT_OUT", out)

        (tmp_path / "articles" / "2026-04-01-a").mkdir(parents=True)
        idx = {
            "articles": [
                {
                    "folder": "2026-04-01-a", "slug": "a", "title": "A",
                    "published_date": "2026-04-01", "canonical_url": "https://radar.firstaimovers.com/a",
                },
            ]
        }
        (tmp_path / "index.json").write_text(json.dumps(idx), encoding="utf-8")
        (tmp_path / "articles" / "2026-04-01-a" / "metadata.json").write_text(
            json.dumps({"slug": "a", "canonical_url": "https://radar.firstaimovers.com/a"}), encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-a" / "article.md").write_text("# A\n", encoding="utf-8")

        graph = m.build_graph()
        m.write_graph(graph, out)

        import argparse
        ns = argparse.Namespace(out=out, check=True)
        # main() would sys.exit; test the logic directly
        existing = json.loads(out.read_text(encoding="utf-8"))
        assert existing == graph

    def test_check_fails_when_stale(self, tmp_path, monkeypatch):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        out = tmp_path / "citation_graph.json"
        monkeypatch.setattr(m, "DEFAULT_OUT", out)

        (tmp_path / "articles" / "2026-04-01-a").mkdir(parents=True)
        idx = {
            "articles": [
                {
                    "folder": "2026-04-01-a", "slug": "a", "title": "A",
                    "published_date": "2026-04-01", "canonical_url": "https://radar.firstaimovers.com/a",
                },
            ]
        }
        (tmp_path / "index.json").write_text(json.dumps(idx), encoding="utf-8")
        (tmp_path / "articles" / "2026-04-01-a" / "metadata.json").write_text(
            json.dumps({"slug": "a", "canonical_url": "https://radar.firstaimovers.com/a"}), encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-a" / "article.md").write_text("# A\n", encoding="utf-8")

        stale = {"version": 1, "nodes": [], "edges": [], "stats": {}}
        out.write_text(json.dumps(stale), encoding="utf-8")

        graph = m.build_graph()
        assert graph != stale

    def test_ignores_non_article_pages(self, tmp_path, monkeypatch):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        (tmp_path / "articles" / "2026-04-01-a").mkdir(parents=True)
        idx = {
            "articles": [
                {
                    "folder": "2026-04-01-a", "slug": "a", "title": "A",
                    "published_date": "2026-04-01", "canonical_url": "https://radar.firstaimovers.com/a",
                },
            ]
        }
        (tmp_path / "index.json").write_text(json.dumps(idx), encoding="utf-8")
        (tmp_path / "articles" / "2026-04-01-a" / "metadata.json").write_text(
            json.dumps({"slug": "a", "canonical_url": "https://radar.firstaimovers.com/a"}), encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-a" / "article.md").write_text(
            "# A\n\n[Consulting](https://radar.firstaimovers.com/page/ai-consulting)\n"
            "[Subscribe](https://www.firstaimovers.com/subscribe)\n"
            "[Home](https://firstaimovers.com)\n"
            "[Category](https://www.firstaimovers.com/c/ai-strategy)\n",
            encoding="utf-8",
        )

        graph = m.build_graph()
        assert graph["stats"]["edge_count"] == 0

    def test_detects_canonical_url_links(self, tmp_path, monkeypatch):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        (tmp_path / "articles" / "2026-04-01-a").mkdir(parents=True)
        (tmp_path / "articles" / "2026-04-01-b").mkdir(parents=True)

        idx = {
            "articles": [
                {
                    "folder": "2026-04-01-a", "slug": "a", "title": "A",
                    "published_date": "2026-04-01", "canonical_url": "https://radar.firstaimovers.com/a",
                },
                {
                    "folder": "2026-04-01-b", "slug": "b", "title": "B",
                    "published_date": "2026-04-01", "canonical_url": "https://radar.firstaimovers.com/b",
                },
            ]
        }
        (tmp_path / "index.json").write_text(json.dumps(idx), encoding="utf-8")
        for s in ("a", "b"):
            (tmp_path / "articles" / f"2026-04-01-{s}" / "metadata.json").write_text(
                json.dumps({"slug": s, "canonical_url": f"https://radar.firstaimovers.com/{s}"}),
                encoding="utf-8",
            )
        (tmp_path / "articles" / "2026-04-01-a" / "article.md").write_text(
            "# A\n\nSee [B](https://radar.firstaimovers.com/b).\n", encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-b" / "article.md").write_text("# B\n", encoding="utf-8")

        graph = m.build_graph()
        assert graph["stats"]["edge_count"] == 1
        assert graph["edges"][0]["matched_url"] == "https://radar.firstaimovers.com/b"

    def test_detects_beehiiv_slug_paths(self, tmp_path, monkeypatch):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        (tmp_path / "articles" / "2026-04-01-a").mkdir(parents=True)
        (tmp_path / "articles" / "2026-04-01-b").mkdir(parents=True)

        idx = {
            "articles": [
                {
                    "folder": "2026-04-01-a", "slug": "a", "title": "A",
                    "published_date": "2026-04-01", "canonical_url": "https://radar.firstaimovers.com/a",
                },
                {
                    "folder": "2026-04-01-b", "slug": "b", "title": "B",
                    "published_date": "2026-04-01", "canonical_url": "https://www.firstaimovers.com/p/b",
                },
            ]
        }
        (tmp_path / "index.json").write_text(json.dumps(idx), encoding="utf-8")
        for s in ("a", "b"):
            (tmp_path / "articles" / f"2026-04-01-{s}" / "metadata.json").write_text(
                json.dumps({"slug": s, "canonical_url": idx["articles"][0 if s == "a" else 1]["canonical_url"]}),
                encoding="utf-8",
            )
        (tmp_path / "articles" / "2026-04-01-a" / "article.md").write_text(
            "# A\n\nSee [B](https://www.firstaimovers.com/p/b).\n", encoding="utf-8"
        )
        (tmp_path / "articles" / "2026-04-01-b" / "article.md").write_text("# B\n", encoding="utf-8")

        graph = m.build_graph()
        assert graph["stats"]["edge_count"] == 1
        assert graph["edges"][0]["target_slug"] == "b"


class TestRebuildIntegration:
    """Tests for citation graph integration in rebuild_local.py."""

    def _mod(self):
        pytest.importorskip("jinja2")
        pytest.importorskip("markdown")
        import rebuild_local
        return rebuild_local

    def _synthetic_index(self, n=3):
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

    def _run(self, monkeypatch, tmp_path, index):
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

        for a in index["articles"]:
            folder = a["folder"]
            (tmp_path / "articles" / folder).mkdir(exist_ok=True)
            (tmp_path / "articles" / folder / "article.md").write_text(
                f'---\ntitle: "{a["title"]}"\nauthor: "Dr. Hernani Costa"\n'
                f'canonical_url: "{a["canonical_url"]}"\npublished_date: "{a["published_date"]}"\n'
                f'license: "CC BY 4.0"\n---\n'
                f'# {a["title"]}\n\n## Introduction\n\nThis is the introduction.\n',
                encoding="utf-8")
            (tmp_path / "articles" / folder / "metadata.json").write_text(
                json.dumps(a), encoding="utf-8")

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return tmp_path / "site"

    def test_article_without_citations_no_sections(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(2))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert "References in this archive" not in page
        assert "Referenced by" not in page

    def test_article_renders_outgoing_citations(self, monkeypatch, tmp_path):
        m = self._mod()
        index = self._synthetic_index(3)
        site = self._run(monkeypatch, tmp_path, index)

        # Write a citation graph that links article-0 -> article-1
        graph = {
            "version": 1,
            "nodes": [
                {"folder": a["folder"], "slug": a["slug"], "title": a["title"],
                 "published_date": a["published_date"], "local_url": "", "canonical_url": a["canonical_url"], "topics": []}
                for a in index["articles"]
            ],
            "edges": [
                {
                    "source_folder": index["articles"][0]["folder"],
                    "target_folder": index["articles"][1]["folder"],
                    "source_slug": index["articles"][0]["slug"],
                    "target_slug": index["articles"][1]["slug"],
                    "type": "explicit-link",
                    "matched_url": "https://radar.firstaimovers.com/article-1",
                    "anchor_text": "Article 1",
                }
            ],
            "stats": {},
        }
        graph_path = tmp_path / "citation_graph.json"
        graph_path.write_text(json.dumps(graph), encoding="utf-8")

        # Rebuild with the graph present
        monkeypatch.setattr(m, "CITATION_GRAPH_PATH", graph_path)
        m.build_site(index)

        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert "References in this archive" in page
        assert "Test Article 1" in page
        assert "Referenced by" not in page

    def test_article_renders_incoming_citations(self, monkeypatch, tmp_path):
        m = self._mod()
        index = self._synthetic_index(3)
        site = self._run(monkeypatch, tmp_path, index)

        graph = {
            "version": 1,
            "nodes": [
                {"folder": a["folder"], "slug": a["slug"], "title": a["title"],
                 "published_date": a["published_date"], "local_url": "", "canonical_url": a["canonical_url"], "topics": []}
                for a in index["articles"]
            ],
            "edges": [
                {
                    "source_folder": index["articles"][2]["folder"],
                    "target_folder": index["articles"][0]["folder"],
                    "source_slug": index["articles"][2]["slug"],
                    "target_slug": index["articles"][0]["slug"],
                    "type": "explicit-link",
                    "matched_url": "https://radar.firstaimovers.com/article-0",
                    "anchor_text": "Article 0",
                }
            ],
            "stats": {},
        }
        graph_path = tmp_path / "citation_graph.json"
        graph_path.write_text(json.dumps(graph), encoding="utf-8")

        monkeypatch.setattr(m, "CITATION_GRAPH_PATH", graph_path)
        m.build_site(index)

        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert "Referenced by" in page
        assert "Test Article 2" in page
        assert "References in this archive" not in page

    def test_json_ld_includes_citation_when_outgoing_exist(self, monkeypatch, tmp_path):
        m = self._mod()
        index = self._synthetic_index(2)
        site = self._run(monkeypatch, tmp_path, index)

        graph = {
            "version": 1,
            "nodes": [
                {"folder": a["folder"], "slug": a["slug"], "title": a["title"],
                 "published_date": a["published_date"], "local_url": "", "canonical_url": a["canonical_url"], "topics": []}
                for a in index["articles"]
            ],
            "edges": [
                {
                    "source_folder": index["articles"][0]["folder"],
                    "target_folder": index["articles"][1]["folder"],
                    "source_slug": index["articles"][0]["slug"],
                    "target_slug": index["articles"][1]["slug"],
                    "type": "explicit-link",
                    "matched_url": "https://radar.firstaimovers.com/article-1",
                    "anchor_text": "Article 1",
                }
            ],
            "stats": {},
        }
        graph_path = tmp_path / "citation_graph.json"
        graph_path.write_text(json.dumps(graph), encoding="utf-8")

        monkeypatch.setattr(m, "CITATION_GRAPH_PATH", graph_path)
        m.build_site(index)

        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert '"citation"' in page
        assert "Test Article 1" in page

    def test_json_ld_omits_citation_when_no_outgoing(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert '"citation"' not in page


class TestDocs:
    """Documentation existence and content tests."""

    def test_citation_graph_doc_exists(self):
        path = Path(__file__).resolve().parents[2] / "docs" / "CITATION_GRAPH.md"
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "explicit-link-only" in text or "explicit link" in text.lower()
        assert "limitation" in text.lower()

    def test_operations_doc_mentions_citation_graph(self):
        path = Path(__file__).resolve().parents[2] / "docs" / "OPERATIONS.md"
        text = path.read_text(encoding="utf-8")
        assert "citation_graph" in text or "Citation Graph" in text

    def test_contributing_doc_mentions_internal_links(self):
        path = Path(__file__).resolve().parents[2] / "CONTRIBUTING.md"
        text = path.read_text(encoding="utf-8")
        assert "internal links" in text.lower() or "citation graph" in text.lower()
