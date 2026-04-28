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

class TestBuildFeed:
    """Atom feed builder. rebuild_local imports cleanly (no env guards)."""

    ATOM_NS = "{http://www.w3.org/2005/Atom}"

    def _mod(self):
        import rebuild_local
        return rebuild_local

    # --- Pure helpers ------------------------------------------------------

    def test_truncate_below_limit_returns_unchanged(self):
        m = self._mod()
        assert m._truncate("short sentence", 100) == "short sentence"

    def test_truncate_cuts_on_word_boundary_with_ellipsis(self):
        m = self._mod()
        result = m._truncate("one two three four five six seven eight", 20)
        assert result.endswith("…")
        assert " " not in result[-3:-1]  # didn't cut mid-word

    def test_clean_canonical_rejects_non_http(self):
        m = self._mod()
        assert m._clean_canonical("ftp://example.com") is None
        assert m._clean_canonical("not a url") is None
        assert m._clean_canonical("") is None
        assert m._clean_canonical(None) is None

    def test_clean_canonical_handles_newline_in_value(self):
        """The 2026-01-21 LinkedIn batch has newlines inside canonical_url."""
        m = self._mod()
        result = m._clean_canonical("\nhttps://www.linkedin.com/pulse/foo\n")
        assert result is not None
        url, host = result
        assert url == "https://www.linkedin.com/pulse/foo"
        assert host == "www.linkedin.com"

    def test_feed_link_uses_canonical_when_first_party(self):
        m = self._mod()
        link = m._feed_link_for({
            "canonical_url": "https://radar.firstaimovers.com/foo",
            "folder": "2026-04-20-foo",
        })
        assert link == "https://radar.firstaimovers.com/foo"

    def test_feed_link_falls_back_to_mirror_for_third_party(self):
        m = self._mod()
        link = m._feed_link_for({
            "canonical_url": "https://www.linkedin.com/pulse/foo",
            "folder": "2026-04-20-foo",
        })
        assert link == "https://articles.firstaimovers.com/articles/2026-04-20-foo/article.md"

    def test_looks_like_prose_rejects_short_blocks(self):
        m = self._mod()
        assert m._looks_like_prose("# Heading") is False
        assert m._looks_like_prose("Short") is False
        assert m._looks_like_prose("_Italicized subtitle_") is False

    def test_looks_like_prose_accepts_real_paragraph(self):
        m = self._mod()
        block = ("This is a genuine paragraph of prose with enough length to "
                 "pass the 80-character filter and look like real article content.")
        assert m._looks_like_prose(block) is True

    def test_tldr_blockquote_regex_matches_standard_format(self):
        m = self._mod()
        text = "# Title\n\n> **TL;DR:** Summary of the article here.\n\nBody content."
        match = m.TLDR_BLOCKQUOTE_RE.search(text)
        assert match is not None
        assert "Summary of the article here" in match.group(1)

    # --- End-to-end build_feed --------------------------------------------

    def _synthetic_index(self, n=3):
        return {
            "articles": [
                {
                    "folder": f"2026-04-{20-i:02d}-entry-{i}",
                    "title": f"Entry {i}",
                    "published_date": f"2026-04-{20-i:02d}",
                    "tags": [f"tag{j}" for j in range(7)],
                    "funnel_stage": "middle",
                    "canonical_url": f"https://radar.firstaimovers.com/entry-{i}",
                }
                for i in range(n)
            ],
        }

    def _run_build_feed(self, monkeypatch, tmp_path, index, **overrides):
        """Run build_feed with ARTICLES_DIR and REPO_ROOT redirected to tmp_path."""
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        for k, v in overrides.items():
            monkeypatch.setattr(m, k, v)
        m.build_feed(index)
        return (tmp_path / "feed.xml").read_text(encoding="utf-8")

    def test_feed_parses_as_atom(self, monkeypatch, tmp_path):
        out = self._run_build_feed(monkeypatch, tmp_path, self._synthetic_index(3))
        root = fromstring(out)
        assert root.tag == f"{self.ATOM_NS}feed"

    def test_feed_respects_max_entries_cap(self, monkeypatch, tmp_path):
        out = self._run_build_feed(
            monkeypatch, tmp_path, self._synthetic_index(10), FEED_MAX_ENTRIES=4)
        root = fromstring(out)
        assert len(root.findall(f"{self.ATOM_NS}entry")) == 4

    def test_feed_updated_matches_most_recent_entry_not_today(self, monkeypatch, tmp_path):
        out = self._run_build_feed(monkeypatch, tmp_path, self._synthetic_index(3))
        root = fromstring(out)
        assert root.find(f"{self.ATOM_NS}updated").text == "2026-04-20T00:00:00Z"

    def test_feed_entry_ids_are_stable_tag_uris(self, monkeypatch, tmp_path):
        out = self._run_build_feed(monkeypatch, tmp_path, self._synthetic_index(2))
        root = fromstring(out)
        for entry in root.findall(f"{self.ATOM_NS}entry"):
            entry_id = entry.find(f"{self.ATOM_NS}id").text
            assert entry_id.startswith("tag:articles.firstaimovers.com,2026-04-")

    def test_feed_categories_capped_per_entry(self, monkeypatch, tmp_path):
        out = self._run_build_feed(monkeypatch, tmp_path, self._synthetic_index(2))
        root = fromstring(out)
        for entry in root.findall(f"{self.ATOM_NS}entry"):
            cats = entry.findall(f"{self.ATOM_NS}category")
            assert len(cats) <= 5

    def test_feed_is_byte_stable_across_runs(self, monkeypatch, tmp_path):
        a = self._run_build_feed(monkeypatch, tmp_path, self._synthetic_index(3))
        b = self._run_build_feed(monkeypatch, tmp_path, self._synthetic_index(3))
        assert a == b

    def test_feed_summary_uses_tldr_blockquote_when_present(self, monkeypatch, tmp_path):
        idx = self._synthetic_index(1)
        out = self._run_build_feed(monkeypatch, tmp_path, idx)
        # No article.md exists → fallback should be title-based
        root = fromstring(out)
        summary = root.find(f"{self.ATOM_NS}entry/{self.ATOM_NS}summary").text
        assert "Entry 0" in summary and "Dr. Hernani Costa" in summary

        # Now add an article.md with a TL;DR and rebuild
        art_dir = tmp_path / "articles" / idx["articles"][0]["folder"]
        art_dir.mkdir()
        (art_dir / "article.md").write_text(
            "---\ntitle: x\n---\n# Hello\n\n> **TL;DR:** The short summary.\n\nBody.")
        out2 = self._run_build_feed(monkeypatch, tmp_path, idx)
        summary2 = fromstring(out2).find(f"{self.ATOM_NS}entry/{self.ATOM_NS}summary").text
        assert summary2 == "The short summary."


# =========================================================================
# Tests: rebuild_local.py llms-full.txt builder
# =========================================================================


class TestJsonFeed:
    """JSON Feed 1.1 generation from rebuild_local.build_json_feed."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def _run(self, monkeypatch, tmp_path, articles_on_disk):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        index = {"articles": []}
        for spec in articles_on_disk:
            folder = spec["folder"]
            (tmp_path / "articles" / folder).mkdir(exist_ok=True)
            body = f"---\ntitle: {spec['title']}\n---\n# {spec['title']}\n\n"
            if spec.get("tldr"):
                body += f"> **TL;DR:** {spec['tldr']}\n\n"
            body += "Body paragraph with enough text to serve as a summary for this test article.\n"
            (tmp_path / "articles" / folder / "article.md").write_text(body)
            index["articles"].append({
                "folder": folder,
                "title": spec["title"],
                "published_date": spec["published_date"],
                "tags": spec.get("tags", []),
                "topics": spec.get("topics", []),
                "funnel_stage": "middle",
                "canonical_url": spec.get("canonical_url", f"https://radar.firstaimovers.com/{folder}"),
            })
        index["articles"].sort(key=lambda a: a["published_date"], reverse=True)
        m.build_json_feed(index)
        return json.loads((tmp_path / "feed.json").read_text(encoding="utf-8"))

    def test_json_feed_has_required_top_level_keys(self, monkeypatch, tmp_path):
        feed = self._run(monkeypatch, tmp_path, [
            {"folder": "2026-04-20-a", "title": "A", "published_date": "2026-04-20"},
        ])
        assert feed["version"] == "https://jsonfeed.org/version/1.1"
        assert "title" in feed
        assert "items" in feed
        assert "language" in feed
        assert "authors" in feed

    def test_json_feed_item_count_matches_atom_cap(self, monkeypatch, tmp_path):
        articles = [
            {"folder": f"2026-04-{d:02d}-a", "title": f"A{d}", "published_date": f"2026-04-{d:02d}"}
            for d in range(1, 60)
        ]
        feed = self._run(monkeypatch, tmp_path, articles)
        assert len(feed["items"]) <= 50

    def test_json_feed_items_use_canonical_urls(self, monkeypatch, tmp_path):
        feed = self._run(monkeypatch, tmp_path, [
            {"folder": "2026-04-20-a", "title": "A", "published_date": "2026-04-20",
             "canonical_url": "https://insights.firstaimovers.com/article-a"},
        ])
        assert feed["items"][0]["url"] == "https://insights.firstaimovers.com/article-a"

    def test_json_feed_items_have_dates_and_tags(self, monkeypatch, tmp_path):
        feed = self._run(monkeypatch, tmp_path, [
            {"folder": "2026-04-20-a", "title": "A", "published_date": "2026-04-20",
             "topics": ["AI Strategy", "EU AI Act"]},
        ])
        item = feed["items"][0]
        assert "date_published" in item
        assert item["tags"] == ["AI Strategy", "EU AI Act"]

    def test_json_feed_no_generated_summaries(self, monkeypatch, tmp_path):
        """Items without TL;DR get the same title-based fallback as Atom feed — never AI-generated."""
        feed = self._run(monkeypatch, tmp_path, [
            {"folder": "2026-04-20-a", "title": "A", "published_date": "2026-04-20"},
        ])
        item = feed["items"][0]
        # Fallback is title-based, same as Atom feed; not an invented summary
        assert "A — by Dr. Hernani Costa" in item.get("content_text", "")

    def test_json_feed_uses_tldr_as_content_text(self, monkeypatch, tmp_path):
        feed = self._run(monkeypatch, tmp_path, [
            {"folder": "2026-04-20-a", "title": "A", "published_date": "2026-04-20",
             "tldr": "This is the actual TL;DR."},
        ])
        item = feed["items"][0]
        assert item.get("content_text") == "This is the actual TL;DR."

    def test_feed_json_is_mirrored_to_site(self, monkeypatch, tmp_path):
        import shutil
        from pathlib import Path as P
        m = self._mod()
        real_root = P(__file__).resolve().parents[2]
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")
        (tmp_path / "feed.json").write_text('{"version":"1.1"}')
        (tmp_path / "index.json").write_text('{"articles":[]}')

        index = {"articles": []}
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site(index)
        assert (tmp_path / "site" / "feed.json").exists()

    def test_feed_urls_not_in_sitemap(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        m.build_sitemap({"articles": []})
        xml = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
        # Feed URLs are excluded from sitemap — they belong on their own host
        assert "feed.xml" not in xml
        assert "feed.json" not in xml



class TestFeedByteStability:
    """Prove Atom and JSON Feed outputs are deterministic for fixed input."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def _synthetic_index(self, n=3):
        return {
            "articles": [
                {
                    "folder": f"2026-04-{20-i:02d}-entry-{i}",
                    "title": f"Entry {i}",
                    "published_date": f"2026-04-{20-i:02d}",
                    "tags": [f"tag{j}" for j in range(7)],
                    "topics": [f"topic{j}" for j in range(3)],
                    "funnel_stage": "middle",
                    "canonical_url": f"https://radar.firstaimovers.com/entry-{i}",
                }
                for i in range(n)
            ],
        }

    def test_atom_feed_is_identical_across_two_builds(self, monkeypatch, tmp_path):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        for a in self._synthetic_index(3)["articles"]:
            d = tmp_path / "articles" / a["folder"]
            d.mkdir(exist_ok=True)
            (d / "article.md").write_text(f"---\ntitle: {a['title']}\n---\n# {a['title']}\n\nBody.\n")
        idx = self._synthetic_index(3)
        m.build_feed(idx)
        first = (tmp_path / "feed.xml").read_text(encoding="utf-8")
        m.build_feed(idx)
        second = (tmp_path / "feed.xml").read_text(encoding="utf-8")
        assert first == second

    def test_json_feed_is_identical_across_two_builds(self, monkeypatch, tmp_path):
        m = self._mod()
        (tmp_path / "articles").mkdir(exist_ok=True)
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        for a in self._synthetic_index(3)["articles"]:
            d = tmp_path / "articles" / a["folder"]
            d.mkdir(exist_ok=True)
            (d / "article.md").write_text(f"---\ntitle: {a['title']}\n---\n# {a['title']}\n\nBody.\n")
        idx = self._synthetic_index(3)
        m.build_json_feed(idx)
        first = (tmp_path / "feed.json").read_text(encoding="utf-8")
        m.build_json_feed(idx)
        second = (tmp_path / "feed.json").read_text(encoding="utf-8")
        assert first == second


# =========================================================================
# Tests: E8 hardening — llms-full.txt byte-stability
# =========================================================================


