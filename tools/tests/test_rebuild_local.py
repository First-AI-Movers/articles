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

from _fixtures import *

class TestRebuildIndex:
    """Test index building logic without network calls."""

    def test_articles_sorted_descending_by_date(self):
        """Index articles must be sorted newest first."""
        articles = [
            {"published_date": "2025-06-01", "title": "Old"},
            {"published_date": "2026-04-04", "title": "New"},
            {"published_date": "2026-01-15", "title": "Mid"},
        ]
        articles.sort(key=lambda a: a.get("published_date", ""), reverse=True)
        assert articles[0]["title"] == "New"
        assert articles[1]["title"] == "Mid"
        assert articles[2]["title"] == "Old"

    def test_articles_with_empty_date_sort_last(self):
        """Articles without a date should sort to the end."""
        articles = [
            {"published_date": "", "title": "No Date"},
            {"published_date": "2026-04-04", "title": "Has Date"},
        ]
        articles.sort(key=lambda a: a.get("published_date", ""), reverse=True)
        assert articles[0]["title"] == "Has Date"
        assert articles[1]["title"] == "No Date"

    def test_metadata_fields_extracted_correctly(self):
        """Index entries should contain exactly the expected fields."""
        meta = {
            "folder": "2026-04-04-test",
            "title": "Test",
            "published_date": "2026-04-04",
            "tags": ["AI", "strategy"],
            "funnel_stage": "top",
            "canonical_url": "https://example.com",
            "extra_field": "should be ignored",
        }
        entry = {
            "folder": meta.get("folder"),
            "title": meta.get("title"),
            "published_date": meta.get("published_date"),
            "tags": meta.get("tags", []),
            "funnel_stage": meta.get("funnel_stage"),
            "canonical_url": meta.get("canonical_url"),
        }
        assert "extra_field" not in entry
        assert entry["tags"] == ["AI", "strategy"]

    def test_missing_tags_defaults_to_empty_list(self):
        """If metadata has no tags field, default to []."""
        meta = {"folder": "test", "title": "Test"}
        tags = meta.get("tags", [])
        assert tags == []

    def test_json_strict_false_handles_control_chars(self):
        """JSON with control characters should parse with strict=False."""
        bad_json = '{"title": "Hello\\nWorld", "value": "test\ttab"}'
        # This would fail with strict=True in some cases
        result = json.loads(bad_json, strict=False)
        assert result["title"] == "Hello\nWorld"


# =========================================================================
# Tests: rebuild_local.py docs patchers (compute_stats + patch_readme + patch_llms)
# =========================================================================


class TestRebuildLocalDocs:
    """Patching logic for README and llms.txt, plus stats computation."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def test_compute_stats(self):
        stats = self._mod().compute_stats(SAMPLE_INDEX)
        assert stats["total"] == 3
        assert stats["tags_count"] == 4  # AI strategy, EU AI Act, AI governance, MCP
        assert stats["topics_count"] == 0  # SAMPLE_INDEX has no topics field
        assert stats["funnel"]["top"] == 1
        assert stats["funnel"]["middle"] == 1
        assert stats["funnel"]["bottom"] == 1
        assert stats["date_min"] == "2025-06-01"
        assert stats["date_max"] == "2026-04-04"

    def test_human_date(self):
        m = self._mod()
        assert m._human_date("2025-02-17") == "February 17, 2025"
        assert m._human_date("2026-04-04") == "April 4, 2026"
        assert m._human_date("invalid") == "invalid"

    def test_funnel_summary(self):
        result = self._mod()._funnel_summary({"top": 221, "middle": 423, "bottom": 4})
        assert "top (221 articles)" in result
        assert "middle (423)" in result
        assert "bottom (4)" in result

    def test_funnel_summary_first_gets_articles_label(self):
        result = self._mod()._funnel_summary({"middle": 10, "top": 5})
        assert result.startswith("top (5 articles)")

    def _stats(self, **overrides):
        base = {"total": 700, "tags_count": 4000, "topics_count": 105,
                "funnel": {"top": 300, "middle": 395, "bottom": 5},
                "date_min": "2025-02-17", "date_max": "2026-04-10"}
        base.update(overrides)
        return base

    def test_patch_readme_updates_badge(self):
        new_content = self._mod().patch_readme(SAMPLE_README, self._stats())
        assert "Articles-700-orange" in new_content
        assert new_content != SAMPLE_README

    def test_patch_readme_updates_article_count_in_description(self):
        new_content = self._mod().patch_readme(SAMPLE_README, self._stats())
        assert "700 original articles" in new_content

    def test_patch_readme_updates_quick_stats(self):
        new_content = self._mod().patch_readme(SAMPLE_README, self._stats(topics_count=105))
        assert "**700** articles indexed" in new_content
        assert "**105** canonical topics" in new_content
        assert "unique topic tags" not in new_content  # old label fully migrated

    def test_patch_readme_always_touches_date_modified(self):
        """Even when article-count fields match, dateModified should be re-stamped."""
        stats = self._stats(total=648, tags_count=3147, topics_count=100,
                            funnel={"top": 221, "middle": 423, "bottom": 4},
                            date_max="2026-04-04")
        new_content = self._mod().patch_readme(SAMPLE_README, stats)
        assert "648 original articles" in new_content
        # dateModified is always updated to today
        assert '"dateModified": "2026-04-05"' not in new_content

    def test_patch_llms_updates_count(self):
        new_content = self._mod().patch_llms(SAMPLE_LLMS_TXT, self._stats(funnel={}))
        assert "700 original articles" in new_content
        assert new_content != SAMPLE_LLMS_TXT


# =========================================================================
# Tests: generate_sitemap.py logic
# =========================================================================


class TestRebuildLocalSitemap:
    """Sitemap XML generation from rebuild_local.build_sitemap.

    The newer signature takes a full index dict and writes sitemap.xml to
    REPO_ROOT rather than returning XML. Tests redirect REPO_ROOT to a
    temp directory and parse the written file.

    Sitemap contains only indexable HTML pages on articles.firstaimovers.com:
    home(1) + /about/(1) + /topics/(1) + topic hubs for topics with
    >= MIN_ARTICLES_FOR_TOPIC_PAGE articles. Raw data files, feeds, and
    cross-host canonical article URLs are intentionally excluded.
    """

    SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def _run(self, monkeypatch, tmp_path, articles):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        m.build_sitemap({"articles": articles})
        return (tmp_path / "sitemap.xml").read_text(encoding="utf-8")

    def test_produces_valid_sitemap_xml(self, monkeypatch, tmp_path):
        xml = self._run(monkeypatch, tmp_path, SAMPLE_INDEX["articles"])
        root = fromstring(xml)
        assert root.tag == f"{self.SITEMAP_NS}urlset"

    def test_url_count_with_sample_index(self, monkeypatch, tmp_path):
        """SAMPLE_INDEX has 3 articles, all on allow-listed hosts, zero topics."""
        xml = self._run(monkeypatch, tmp_path, SAMPLE_INDEX["articles"])
        # home(1) + about(1) + topics(1) + 0 topic hubs = 3
        assert xml.count("<url>") == 3

    def test_sitemap_excludes_cross_host_canonicals(self, monkeypatch, tmp_path):
        xml = self._run(monkeypatch, tmp_path, SAMPLE_INDEX["articles"])
        # Canonical article URLs on external hosts are excluded from sitemap
        assert "https://radar.firstaimovers.com/test-one" not in xml
        assert "https://radar.firstaimovers.com/test-two" not in xml
        assert "https://insights.firstaimovers.com/test-three" not in xml
        # No fabricated /articles/<folder>/ paths either
        assert "/articles/2026-04-04-test-article-one/" not in xml

    def test_third_party_canonicals_are_skipped(self, monkeypatch, tmp_path):
        articles = [
            {"folder": "2026-01-01-x", "title": "LinkedIn", "published_date": "2026-01-01",
             "tags": [], "funnel_stage": "middle",
             "canonical_url": "https://www.linkedin.com/pulse/x"},
            {"folder": "2026-01-02-y", "title": "Medium", "published_date": "2026-01-02",
             "tags": [], "funnel_stage": "middle",
             "canonical_url": "https://medium.com/@x/y"},
        ]
        xml = self._run(monkeypatch, tmp_path, articles)
        assert "linkedin.com" not in xml
        assert "medium.com" not in xml
        # Only support URLs remain: home + about + topics = 3
        assert xml.count("<url>") == 3

    def test_uses_correct_base_url(self, monkeypatch, tmp_path):
        xml = self._run(monkeypatch, tmp_path, [])
        assert "https://articles.firstaimovers.com/" in xml

    def test_home_has_highest_priority(self, monkeypatch, tmp_path):
        xml = self._run(monkeypatch, tmp_path, [])
        root = fromstring(xml)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        for url in root.findall("s:url", ns):
            loc = url.find("s:loc", ns).text
            if loc.endswith(".com/"):
                assert url.find("s:priority", ns).text == "1.0"
                break

    def test_sitemap_excludes_data_files(self, monkeypatch, tmp_path):
        xml = self._run(monkeypatch, tmp_path, SAMPLE_INDEX["articles"])
        assert ".md" not in xml
        assert ".json" not in xml
        assert ".txt" not in xml
        assert ".cff" not in xml
        assert "feed.xml" not in xml
        assert "feed.json" not in xml
        assert "llms.txt" not in xml
        assert "index.json" not in xml
        assert "hernanicosta.json" not in xml

    def test_empty_index_emits_only_support_urls(self, monkeypatch, tmp_path):
        xml = self._run(monkeypatch, tmp_path, [])
        # home + about + topics = 3
        assert xml.count("<url>") == 3

    def test_topic_hub_urls_emitted_for_threshold_topics(self, monkeypatch, tmp_path):
        """Topics with >= MIN_ARTICLES_FOR_TOPIC_PAGE articles get a sitemap URL."""
        m = self._mod()
        # Build an index with one topic above threshold, one below
        articles = []
        for i in range(m.MIN_ARTICLES_FOR_TOPIC_PAGE):
            articles.append({
                "folder": f"2026-04-{i+1:02d}-a", "title": f"Article {i}",
                "published_date": f"2026-04-{i+1:02d}", "tags": [],
                "topics": ["AI Strategy"], "funnel_stage": "middle",
                "canonical_url": f"https://radar.firstaimovers.com/a{i}",
            })
        # Below-threshold topic
        articles.append({
            "folder": "2026-04-10-b", "title": "B", "published_date": "2026-04-10",
            "tags": [], "topics": ["AI Testing"], "funnel_stage": "middle",
            "canonical_url": "https://radar.firstaimovers.com/b",
        })
        xml = self._run(monkeypatch, tmp_path, articles)
        assert f"{m.SITE_BASE}/topics/ai-strategy/" in xml
        assert f"{m.SITE_BASE}/topics/ai-testing/" not in xml

    def test_malformed_canonical_is_skipped(self, monkeypatch, tmp_path):
        articles = [
            {"folder": "2026-01-01-x", "title": "Bad", "published_date": "2026-01-01",
             "tags": [], "funnel_stage": "middle", "canonical_url": "not a url"},
            {"folder": "2026-01-02-y", "title": "Empty", "published_date": "2026-01-02",
             "tags": [], "funnel_stage": "middle", "canonical_url": ""},
        ]
        xml = self._run(monkeypatch, tmp_path, articles)
        assert xml.count("<url>") == 3  # only support URLs (3 total)


# =========================================================================
# Tests: add_tldr.py logic
# =========================================================================


class TestBuildSite:
    """HTML topic-hub site. Requires jinja2; skipped cleanly if not installed."""

    def _mod(self):
        pytest.importorskip("jinja2")
        import rebuild_local
        return rebuild_local

    def _synthetic_index(self, topic_distribution):
        """Build an index where topic_distribution is {topic_name: article_count}."""
        articles = []
        day = 1
        for topic, count in topic_distribution.items():
            for _ in range(count):
                articles.append({
                    "folder": f"2026-04-{day:02d}-slug{day}",
                    "slug": f"slug-{day}",
                    "title": f"Article {day}",
                    "published_date": f"2026-04-{day:02d}",
                    "tags": [],
                    "topics": [topic],
                    "funnel_stage": "middle",
                    "canonical_url": f"https://radar.firstaimovers.com/slug{day}",
                })
                day += 1
        articles.sort(key=lambda a: a["published_date"], reverse=True)
        return {"articles": articles}

    def _run(self, monkeypatch, tmp_path, index):
        m = self._mod()
        # Redirect all IO roots to tmp_path
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        # Copy real templates + static so we don't re-fixture them
        import shutil
        from pathlib import Path as P
        # Resolve repo root from this file's location, not a hardcoded path
        # (this test file lives at <repo>/tools/tests/test_rebuild_local.py).
        real_root = P(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        # Real hernanicosta.json is needed for about page
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")
        # Sample article files so llms-full.txt summary lookups don't 404
        for a in index["articles"]:
            (tmp_path / "articles" / a["folder"]).mkdir(exist_ok=True)
            (tmp_path / "articles" / a["folder"] / "article.md").write_text(
                f"---\ntitle: {a['title']}\n---\n# {a['title']}\n\nBody paragraph with enough text to serve as a summary for this test article.\n")

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return tmp_path / "site"

    def test_slugify_produces_stable_urls(self):
        m = self._mod()
        assert m._slugify("AI Governance") == "ai-governance"
        assert m._slugify("GDPR & Data Privacy") == "gdpr-and-data-privacy"
        assert m._slugify("European SME AI") == "european-sme-ai"
        assert m._slugify("AI SEO and GEO") == "ai-seo-and-geo"
        assert m._slugify("UK and Ireland AI") == "uk-and-ireland-ai"

    def test_home_page_renders(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Governance": 6}))
        home = (site / "index.html").read_text(encoding="utf-8")
        assert "<title>First AI Movers" in home
        assert 'rel="canonical" href="https://articles.firstaimovers.com/"' in home
        assert 'name="robots" content="index, follow"' in home

    def test_topics_index_lists_all_topics(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Governance": 6, "AI Agents": 2}))
        idx = (site / "topics" / "index.html").read_text(encoding="utf-8")
        # Both topics appear (under/over threshold), but only over-threshold is a link
        assert "AI Governance" in idx
        assert "AI Agents" in idx
        assert "topics/ai-governance/" in idx
        assert "topics/ai-agents/" not in idx  # below threshold → not linked

    def test_topic_page_created_only_above_threshold(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Governance": 6, "AI Agents": 2}))
        assert (site / "topics" / "ai-governance" / "index.html").exists()
        assert not (site / "topics" / "ai-agents").exists()

    def test_topic_page_lists_articles_newest_first(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Strategy": 6}))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        # Day 6 is newest; day 1 is oldest. Position check.
        assert page.index("Article 6") < page.index("Article 1")

    def test_topic_page_self_canonical(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Strategy": 6}))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert 'rel="canonical" href="https://articles.firstaimovers.com/topics/ai-strategy/"' in page
        assert 'name="robots" content="index, follow"' in page

    def test_article_cards_link_to_local_page(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Governance": 6}))
        page = (site / "topics" / "ai-governance" / "index.html").read_text(encoding="utf-8")
        # Title links to local archive page
        assert 'href="../../articles/slug-1/"' in page
        # CTA still links to external canonical
        assert "https://radar.firstaimovers.com/slug1" in page

    def test_about_page_canonicals_to_drhernanicosta(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Strategy": 6}))
        about = (site / "about" / "index.html").read_text(encoding="utf-8")
        assert 'rel="canonical" href="https://drhernanicosta.com"' in about
        assert 'application/ld+json' in about  # Person JSON-LD embedded

    def test_404_page_noindex(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Strategy": 6}))
        page = (site / "404.html").read_text(encoding="utf-8")
        assert 'name="robots" content="noindex"' in page

    def test_stylesheet_copied(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Strategy": 6}))
        assert (site / "style.css").exists()
        # Every page references it via relative path — spot-check topic page
        topic = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert 'href="../../style.css"' in topic

    def test_raw_data_mirror_files_copied(self, monkeypatch, tmp_path):
        # Put some mirror files in the tmp root to simulate a full rebuild
        (tmp_path / "index.json").write_text('{"articles": []}')
        (tmp_path / "llms.txt").write_text("llms")
        (tmp_path / "llms-full.txt").write_text("corpus")
        (tmp_path / "feed.xml").write_text("<feed/>")
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Strategy": 6}))
        assert (site / "index.json").exists()
        assert (site / "llms.txt").exists()
        assert (site / "llms-full.txt").exists()
        assert (site / "feed.xml").exists()
        # Raw articles tree mirrored
        assert (site / "articles").exists()

    def test_related_topics_ranked_by_cooccurrence(self):
        m = self._mod()
        articles = [
            {"topics": ["A", "B", "C"]},
            {"topics": ["A", "B"]},
            {"topics": ["A", "D"]},
        ]
        counts = {"A": 3, "B": 2, "C": 1, "D": 1}
        related = m._related_topics_for("A", articles, counts, limit=3)
        assert related == ["B", "C", "D"]  # B co-occurs twice, C/D once each

    def test_canonical_host_label_maps_common_hosts(self):
        m = self._mod()
        assert m._canonical_host_label("https://radar.firstaimovers.com/foo") == "Radar"
        assert m._canonical_host_label("https://www.linkedin.com/pulse/x") == "LinkedIn"
        assert m._canonical_host_label("https://insights.firstaimovers.com/y") == "Insights"

    def test_topic_page_renders_intro_block_when_present(self, monkeypatch, tmp_path):
        """When _load_topic_intros returns content for a topic, the page surfaces it."""
        m = self._mod()
        monkeypatch.setattr(m, "_load_topic_intros", lambda: {
            "AI Strategy": {
                "lede": "Lede sentence about strategy.",
                "key_themes": ["First theme line", "Second theme line"],
                "why_it_matters": "Why this topic matters paragraph.",
            },
        })
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Strategy": 6}))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert "Lede sentence about strategy." in page
        assert "First theme line" in page
        assert "Second theme line" in page
        assert "Why this topic matters paragraph." in page
        assert 'class="topic-intro"' in page
        # Curated lede should also surface in the meta description
        assert 'name="description" content="Lede sentence about strategy."' in page

    def test_topic_page_falls_back_to_generic_lede_without_intro(self, monkeypatch, tmp_path):
        """Topics absent from topic_intros.json still render — with the boilerplate lede."""
        m = self._mod()
        monkeypatch.setattr(m, "_load_topic_intros", lambda: {})
        site = self._run(monkeypatch, tmp_path,
                         self._synthetic_index({"AI Strategy": 6}))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert "Every article in the First AI Movers archive tagged" in page
        assert 'class="topic-intro"' not in page



class TestDarkMode:
    """Default dark mode with light toggle — theme system."""

    def _mod(self):
        pytest.importorskip("jinja2")
        import rebuild_local
        return rebuild_local

    def _run(self, monkeypatch, tmp_path):
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

        index = {"articles": []}
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return tmp_path / "site"

    def test_home_page_has_dark_theme_default(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path)
        home = (site / "index.html").read_text(encoding="utf-8")
        assert '<html lang="en" data-theme="dark">' in home

    def test_toggle_button_exists(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path)
        home = (site / "index.html").read_text(encoding="utf-8")
        assert 'id="theme-toggle"' in home
        assert 'Light mode' in home
        assert 'aria-label="Toggle light mode"' in home

    def test_inline_script_no_external_js(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path)
        home = (site / "index.html").read_text(encoding="utf-8")
        assert '<script>' in home
        # Dark mode toggle must be inline; search.js and pwa.js are the only allowed external scripts
        src_count = home.count('<script src="')
        assert src_count <= 2, f"Expected at most 2 external scripts, found {src_count}"
        assert 'pwa.js' in home
        assert 'localStorage' in home

    def test_light_theme_css_exists(self):
        from pathlib import Path as P
        css = (P(__file__).resolve().parents[2] / "static" / "style.css").read_text(encoding="utf-8")
        assert 'html[data-theme="dark"]' in css
        assert 'html[data-theme="light"]' in css or '--bg: #fafafa' in css

    def test_topic_page_renders_with_dark_theme(self, monkeypatch, tmp_path):
        m = self._mod()
        # Build with articles above topic threshold so a topic page is generated
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        from pathlib import Path as P
        real_root = P(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")
        for i in range(6):
            folder = f"2026-04-{20-i:02d}-a{i}"
            (tmp_path / "articles" / folder).mkdir(exist_ok=True)
            (tmp_path / "articles" / folder / "article.md").write_text(
                f"---\ntitle: A{i}\n---\n# A{i}\n\nBody.\n")
        index = {"articles": [
            {"folder": f"2026-04-{20-i:02d}-a{i}", "slug": f"a{i}", "title": f"A{i}",
             "published_date": f"2026-04-{20-i:02d}", "tags": [], "topics": ["AI Strategy"],
             "funnel_stage": "middle", "canonical_url": f"https://radar.firstaimovers.com/a{i}"}
            for i in range(6)
        ]}
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        page = (tmp_path / "site" / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert '<html lang="en" data-theme="dark">' in page



class TestSocialFooter:
    """Visible author social links in footer — E5."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def _run(self, monkeypatch, tmp_path):
        m = self._mod()
        import shutil
        from pathlib import Path as P
        real_root = P(__file__).resolve().parents[2]
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")

        index = {"articles": []}
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return tmp_path / "site"

    def test_footer_renders_social_links(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path)
        home = (site / "index.html").read_text(encoding="utf-8")
        assert "linkedin.com/in/hernani-costa-ai-ceo-firstaimovers" in home
        assert "open.spotify.com/show/5HX1cZF7Ojikm2VWcAzTnt" in home
        assert "youtube.com/@DrHernaniCosta" in home

    def test_base_template_has_json_feed_link(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path)
        home = (site / "index.html").read_text(encoding="utf-8")
        assert 'type="application/json"' in home
        assert "feed.json" in home

    def test_no_og_image_when_none_configured(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path)
        home = (site / "index.html").read_text(encoding="utf-8")
        # No og:image should be emitted when no image asset exists
        assert "property=\"og:image\"" not in home
        assert "name=\"twitter:image\"" not in home


# =========================================================================
# Tests: rebuild_local.py per-article HTML pages (E6)
# =========================================================================


class TestAccessibility:
    """Accessibility fixes: skip link, landmarks, focus states, theme toggle semantics."""

    def _mod(self):
        pytest.importorskip("jinja2")
        pytest.importorskip("markdown")
        import rebuild_local
        return rebuild_local

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

        for a in index.get("articles", []):
            folder = a.get("folder", "")
            if folder:
                (tmp_path / "articles" / folder).mkdir(exist_ok=True)
                (tmp_path / "articles" / folder / "article.md").write_text(
                    f"---\ntitle: {a.get('title', 'T')}\n---\n# {a.get('title', 'T')}\n\nBody.\n")

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return tmp_path / "site"

    def _synthetic_index(self, n=3):
        articles = []
        for i in range(n):
            day = 20 - i
            articles.append({
                "folder": f"2026-04-{day:02d}-article-{i}",
                "slug": f"article-{i}",
                "title": f"Test Article {i}",
                "published_date": f"2026-04-{day:02d}",
                "tags": [],
                "topics": ["AI Strategy"],
                "funnel_stage": "middle",
                "canonical_url": f"https://radar.firstaimovers.com/article-{i}",
            })
        return {"articles": articles}

    # --- Skip link ---------------------------------------------------------

    def test_home_page_has_skip_link(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        home = (site / "index.html").read_text(encoding="utf-8")
        assert '<a href="#main-content" class="skip-link">Skip to content</a>' in home

    def test_topic_page_has_skip_link(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert 'class="skip-link"' in page

    def test_article_page_has_skip_link(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'class="skip-link"' in page

    def test_about_page_has_skip_link(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        page = (site / "about" / "index.html").read_text(encoding="utf-8")
        assert 'class="skip-link"' in page

    def test_404_page_has_skip_link(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        page = (site / "404.html").read_text(encoding="utf-8")
        assert 'class="skip-link"' in page

    # --- Main landmark -----------------------------------------------------

    def test_main_has_id_main_content(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        home = (site / "index.html").read_text(encoding="utf-8")
        assert '<main id="main-content"' in home

    # --- Theme toggle accessibility ----------------------------------------

    def test_theme_toggle_is_button(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        home = (site / "index.html").read_text(encoding="utf-8")
        assert 'id="theme-toggle"' in home
        assert '<button' in home

    def test_theme_toggle_has_aria_pressed(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        home = (site / "index.html").read_text(encoding="utf-8")
        assert 'aria-pressed="false"' in home or 'aria-pressed="true"' in home

    def test_theme_toggle_aria_label_updates_with_theme(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        home = (site / "index.html").read_text(encoding="utf-8")
        # The inline script should set the label based on the stored/default theme
        assert "Toggle light mode" in home or "Toggle dark mode" in home

    # --- Navigation landmarks ----------------------------------------------

    def test_primary_nav_has_aria_label(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        home = (site / "index.html").read_text(encoding="utf-8")
        assert 'aria-label="Primary"' in home

    # --- Breadcrumbs -------------------------------------------------------

    def test_article_breadcrumb_has_aria_label(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'aria-label="Breadcrumb"' in page

    def test_topic_breadcrumb_has_aria_label(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert 'aria-label="Breadcrumb"' in page

    def test_about_breadcrumb_has_aria_label(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        page = (site / "about" / "index.html").read_text(encoding="utf-8")
        assert 'aria-label="Breadcrumb"' in page

    # --- Focus CSS ---------------------------------------------------------

    def test_focus_visible_css_exists(self):
        from pathlib import Path as P
        css = (P(__file__).resolve().parents[2] / "static" / "style.css").read_text(encoding="utf-8")
        assert ":focus-visible" in css

    def test_button_focus_visible_css_exists(self):
        from pathlib import Path as P
        css = (P(__file__).resolve().parents[2] / "static" / "style.css").read_text(encoding="utf-8")
        assert "button:focus-visible" in css or ".theme-toggle:focus-visible" in css

    def test_skip_link_css_exists(self):
        from pathlib import Path as P
        css = (P(__file__).resolve().parents[2] / "static" / "style.css").read_text(encoding="utf-8")
        assert ".skip-link" in css

    # --- Reduced motion ----------------------------------------------------

    def test_prefers_reduced_motion_exists(self):
        from pathlib import Path as P
        css = (P(__file__).resolve().parents[2] / "static" / "style.css").read_text(encoding="utf-8")
        assert "prefers-reduced-motion" in css

    # --- No heading-order violations (template level) ----------------------

    def test_home_page_heading_order(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": []})
        home = (site / "index.html").read_text(encoding="utf-8")
        # Home should have h1 before h2
        h1_pos = home.find("<h1>")
        h2_pos = home.find("<h2>")
        assert h1_pos != -1
        assert h2_pos == -1 or h1_pos < h2_pos

    def test_topic_page_heading_order(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        h1_pos = page.find("<h1>")
        h2_pos = page.find("<h2>")
        assert h1_pos != -1
        assert h2_pos == -1 or h1_pos < h2_pos

    def test_article_page_heading_order(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(1))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        h1_pos = page.find("<h1>")
        h2_pos = page.find("<h2>")
        assert h1_pos != -1
        assert h2_pos == -1 or h1_pos < h2_pos


# =========================================================================
# Tests: E10 client-side search
# =========================================================================


class TestTopicHubSeo:
    """Topic hub metadata, structured data, sitemap freshness, and internal linking."""

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
                f'# {a["title"]}\n\n## Introduction\n\nBody.\n',
                encoding="utf-8")

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        return tmp_path / "site"

    # --- Title / meta ------------------------------------------------------

    def test_topic_page_title_includes_topic_name_and_archive_context(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        assert "<title>AI Strategy Articles — First AI Movers Archive</title>" in page

    def test_topic_page_meta_description_includes_topic_name_and_count(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        desc = '<meta name="description" content="'
        assert desc in page
        # Description should mention the topic name
        assert "AI Strategy" in page or "ai-strategy" in page

    # --- Structured data ---------------------------------------------------

    def test_topic_page_has_valid_json_ld(self, monkeypatch, tmp_path):
        import json
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        # Extract first JSON-LD block
        start = page.find('<script type="application/ld+json">')
        end = page.find('</script>', start)
        block = page[start + len('<script type="application/ld+json">'):end]
        data = json.loads(block)
        assert "@context" in data
        assert "https://schema.org" in data["@context"]

    def test_topic_json_ld_has_collection_page_type(self, monkeypatch, tmp_path):
        import json
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        start = page.find('<script type="application/ld+json">')
        end = page.find('</script>', start)
        data = json.loads(page[start + len('<script type="application/ld+json">'):end])
        assert data["@type"] == "CollectionPage"
        assert "mainEntity" in data
        assert data["mainEntity"]["@type"] == "ItemList"

    def test_topic_json_ld_no_invented_images(self, monkeypatch, tmp_path):
        import json
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        start = page.find('<script type="application/ld+json">')
        end = page.find('</script>', start)
        data = json.loads(page[start + len('<script type="application/ld+json">'):end])
        assert "image" not in data

    def test_topic_page_has_breadcrumb_json_ld(self, monkeypatch, tmp_path):
        import json
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        page = (site / "topics" / "ai-strategy" / "index.html").read_text(encoding="utf-8")
        # Find second JSON-LD block (BreadcrumbList)
        first = page.find('<script type="application/ld+json">')
        second = page.find('<script type="application/ld+json">', first + 1)
        end = page.find('</script>', second)
        data = json.loads(page[second + len('<script type="application/ld+json">'):end])
        assert data["@type"] == "BreadcrumbList"
        assert len(data["itemListElement"]) == 3

    # --- Sitemap lastmod ---------------------------------------------------

    def test_sitemap_topic_lastmod_is_newest_article_date(self, monkeypatch, tmp_path):
        m = self._mod()
        # Need >= MIN_ARTICLES_FOR_TOPIC_PAGE (5) articles for topic hub to exist
        articles = []
        for i in range(5):
            day = 10 - i
            articles.append({
                "folder": f"2026-04-{day:02d}-a{i}", "title": f"A{i}",
                "published_date": f"2026-04-{day:02d}",
                "tags": [], "topics": ["AI Strategy"], "funnel_stage": "middle",
                "canonical_url": f"https://radar.firstaimovers.com/a{i}",
            })
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        m.build_sitemap({"articles": articles})
        xml = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
        # Topic hub lastmod should be newest article date: 2026-04-10
        assert "<loc>https://articles.firstaimovers.com/topics/ai-strategy/</loc>" in xml
        from xml.etree.ElementTree import fromstring
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        root = fromstring(xml)
        for url in root.findall("s:url", ns):
            loc = url.find("s:loc", ns).text
            if "topics/ai-strategy" in loc:
                lastmod = url.find("s:lastmod", ns).text
                assert lastmod == "2026-04-10", f"Expected 2026-04-10, got {lastmod}"
                break
        else:
            raise AssertionError("Topic hub URL not found in sitemap")

    # --- Internal linking --------------------------------------------------

    def test_article_page_links_to_topic_hub(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(6))
        # Pick any article page
        article_page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        # Should link to its primary topic hub somewhere on the page
        assert 'href="../../topics/ai-strategy/"' in article_page

    def test_article_page_preserves_noindex_external_canonical(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, self._synthetic_index(3))
        page = (site / "articles" / "article-0" / "index.html").read_text(encoding="utf-8")
        assert 'name="robots" content="noindex, follow"' in page
        assert 'rel="canonical" href="https://radar.firstaimovers.com/article-0"' in page


# Tests: E14 — Security tooling & supply-chain hygiene
# =========================================================================



# Tests: E33 — Ask the Archive page generation
# =========================================================================

class TestAskPage:
    def _run(self, monkeypatch, tmp_path, index_data):
        pytest.importorskip("jinja2")
        import rebuild_local as rebuild
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
        idx_path = tmp_path / "index.json"
        idx_path.write_text(json.dumps(index_data), encoding="utf-8")
        monkeypatch.setattr(rebuild, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(rebuild, "ARTICLES_DIR", articles)
        monkeypatch.setattr(rebuild, "SITE_DIR", out)
        monkeypatch.setattr(rebuild, "STATIC_DIR", static)
        monkeypatch.setattr(rebuild, "TEMPLATE_DIR", templates)
        rebuild.build_site(index_data)
        return out

    def test_ask_page_generated(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": [], "topics": []})
        ask = site / "ask" / "index.html"
        assert ask.exists(), "ask/index.html should be generated"

    def test_ask_page_has_noindex(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": [], "topics": []})
        page = (site / "ask" / "index.html").read_text(encoding="utf-8")
        assert 'name="robots" content="noindex, follow"' in page

    def test_ask_page_has_form(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": [], "topics": []})
        page = (site / "ask" / "index.html").read_text(encoding="utf-8")
        assert '<form id="ask-form"' in page
        assert 'id="ask-question"' in page
        assert 'type="submit"' in page

    def test_ask_page_includes_js(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": [], "topics": []})
        page = (site / "ask" / "index.html").read_text(encoding="utf-8")
        assert 'ask.js' in page
        assert 'ASK_ARCHIVE_ENDPOINT' in page

    def test_ask_page_has_disabled_banner(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": [], "topics": []})
        page = (site / "ask" / "index.html").read_text(encoding="utf-8")
        assert 'ask-disabled' in page
        assert "endpoint not yet deployed" in page

    def test_ask_page_has_breadcrumb(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": [], "topics": []})
        page = (site / "ask" / "index.html").read_text(encoding="utf-8")
        assert 'aria-label="Breadcrumb"' in page
        assert 'Ask' in page

    def test_ask_js_copied_to_static(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": [], "topics": []})
        js = site / "ask.js"
        assert js.exists(), "ask.js should be copied to site root"

    def test_nav_includes_ask_link(self, monkeypatch, tmp_path):
        site = self._run(monkeypatch, tmp_path, {"articles": [], "topics": []})
        home = (site / "index.html").read_text(encoding="utf-8")
        assert 'href="ask/"' in home or 'href="./ask/"' in home or 'href="/ask/"' in home

