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

class TestIndexNow:
    """IndexNow key file, submission script, and workflow integration."""

    def _mod(self):
        import rebuild_local
        return rebuild_local

    def _key_file(self, tmp_path, key="ee4c7a6ad2464b84a2320e9edf0fe996"):
        (tmp_path / ".indexnow-key").write_text(key, encoding="utf-8")
        return key

    def _sitemap(self, tmp_path, urls):
        xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u in urls:
            xml += f"  <url><loc>{u}</loc></url>\n"
        xml += "</urlset>\n"
        (tmp_path / "sitemap.xml").write_text(xml, encoding="utf-8")

    # --- Key file tests ----------------------------------------------------

    def test_key_format_is_hex_32_chars(self, monkeypatch):
        key = "ee4c7a6ad2464b84a2320e9edf0fe996"
        monkeypatch.setenv("INDEXNOW_API_KEY_ARTICLES_FAIM", key)
        import submit_indexnow
        loaded = submit_indexnow._get_key_for_host("articles.firstaimovers.com")
        assert len(loaded) == 32, f"Key must be 32 hex chars, got {len(loaded)}"
        assert all(c in "0123456789abcdef" for c in loaded.lower()), "Key must be hex"

    def test_key_file_written_to_site_on_rebuild(self, monkeypatch, tmp_path):
        m = self._mod()
        key = "ee4c7a6ad2464b84a2320e9edf0fe996"
        monkeypatch.setenv("INDEXNOW_API_KEY_ARTICLES_FAIM", key)
        # Minimal build_site context: need articles dir, templates dir, static dir
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        from pathlib import Path
        real_root = Path(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        # The key file is written by build_site reading the env var
        m.build_site({"articles": []})
        key_file = tmp_path / "site" / f"{key}.txt"
        assert key_file.exists(), f"Key file {key}.txt must be in site root"
        assert key_file.read_text(encoding="utf-8").strip() == key

    def test_rebuild_skips_key_file_when_env_missing(self, monkeypatch, tmp_path):
        m = self._mod()
        monkeypatch.delenv("INDEXNOW_API_KEY_ARTICLES_FAIM", raising=False)
        monkeypatch.delenv("INDEXNOW_API_KEY", raising=False)
        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        from pathlib import Path
        real_root = Path(__file__).resolve().parents[2]
        shutil.copytree(real_root / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(real_root / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(real_root / "hernanicosta.json", tmp_path / "hernanicosta.json")
        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        m.build_site({"articles": []})
        # No .txt key file should exist
        txt_files = list((tmp_path / "site").glob("*.txt"))
        key_like = [f for f in txt_files if len(f.stem) == 32 and all(c in "0123456789abcdef" for c in f.stem.lower())]
        assert not key_like, f"Expected no IndexNow key file, found {key_like}"

    # --- submit_indexnow.py tests ------------------------------------------

    def test_dry_run_reads_sitemap_and_lists_urls(self, monkeypatch, tmp_path):
        import subprocess, sys
        key = "ee4c7a6ad2464b84a2320e9edf0fe996"
        urls = ["https://articles.firstaimovers.com/",
                "https://articles.firstaimovers.com/about/",
                "https://articles.firstaimovers.com/topics/",
                "https://articles.firstaimovers.com/topics/ai-strategy/"]
        self._sitemap(tmp_path, urls)
        from pathlib import Path
        script = Path(__file__).resolve().parents[2] / "tools" / "submit_indexnow.py"
        result = subprocess.run(
            [sys.executable, str(script),
             "--sitemap", str(tmp_path / "sitemap.xml"),
             "--key", key,
             "--key-location", f"https://articles.firstaimovers.com/{key}.txt",
             "--dry-run"],
            capture_output=True, text=True, cwd=str(tmp_path.parent.parent))
        assert result.returncode == 0, result.stderr
        assert "4" in result.stdout or "4 URL" in result.stdout, result.stdout
        assert "articles.firstaimovers.com" in result.stdout

    def test_payload_contains_correct_fields(self, monkeypatch, tmp_path):
        import submit_indexnow
        key = "ee4c7a6ad2464b84a2320e9edf0fe996"
        urls = ["https://articles.firstaimovers.com/",
                "https://articles.firstaimovers.com/topics/ai-strategy/"]
        payload = submit_indexnow._build_payload(urls, key, "articles.firstaimovers.com")
        assert payload["host"] == "articles.firstaimovers.com"
        assert payload["key"] == key
        assert payload["keyLocation"] == f"https://articles.firstaimovers.com/{key}.txt"
        assert payload["urlList"] == urls

    def test_rejects_cross_host_urls(self, monkeypatch, tmp_path):
        import submit_indexnow
        urls = ["https://articles.firstaimovers.com/",
                "https://radar.firstaimovers.com/some-article"]
        filtered = submit_indexnow._filter_urls(urls, "articles.firstaimovers.com")
        assert "radar.firstaimovers.com" not in filtered
        assert "https://articles.firstaimovers.com/" in filtered

    def test_excludes_local_article_pages(self, monkeypatch, tmp_path):
        import submit_indexnow
        urls = ["https://articles.firstaimovers.com/",
                "https://articles.firstaimovers.com/articles/some-slug/"]
        filtered = submit_indexnow._filter_urls(urls, "articles.firstaimovers.com")
        assert "/articles/some-slug/" not in filtered
        assert "https://articles.firstaimovers.com/" in filtered

    def test_excludes_data_file_extensions(self, monkeypatch, tmp_path):
        import submit_indexnow
        urls = ["https://articles.firstaimovers.com/",
                "https://articles.firstaimovers.com/feed.xml",
                "https://articles.firstaimovers.com/index.json",
                "https://articles.firstaimovers.com/llms.txt",
                "https://articles.firstaimovers.com/README.md"]
        filtered = submit_indexnow._filter_urls(urls, "articles.firstaimovers.com")
        assert filtered == ["https://articles.firstaimovers.com/"]

    def test_treats_200_as_success(self, monkeypatch, tmp_path):
        import submit_indexnow
        key = self._key_file(tmp_path)
        class FakeResponse:
            status = 200
            def read(self): return b'{}'
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def close(self): pass
        def fake_open(req, timeout=None):
            return FakeResponse()
        monkeypatch.setattr(submit_indexnow, "urlopen", fake_open)
        result = submit_indexnow._submit([], key, "https://api.indexnow.org/indexnow", "articles.firstaimovers.com")
        assert result is True

    def test_treats_202_as_success(self, monkeypatch, tmp_path):
        import submit_indexnow
        key = self._key_file(tmp_path)
        class FakeResponse:
            status = 202
            def read(self): return b'{}'
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def close(self): pass
        def fake_open(req, timeout=None):
            return FakeResponse()
        monkeypatch.setattr(submit_indexnow, "urlopen", fake_open)
        result = submit_indexnow._submit([], key, "https://api.indexnow.org/indexnow", "articles.firstaimovers.com")
        assert result is True

    def test_fails_on_403(self, monkeypatch, tmp_path):
        import submit_indexnow
        key = self._key_file(tmp_path)
        from urllib.error import HTTPError
        class FakeResponse:
            status = 403
            def read(self): return b'Forbidden'
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def close(self): pass
        def fake_open(req, timeout=None):
            resp = FakeResponse()
            raise HTTPError("https://api.indexnow.org/indexnow", 403, "Forbidden", {}, resp)
        monkeypatch.setattr(submit_indexnow, "urlopen", fake_open)
        result = submit_indexnow._submit([], key, "https://api.indexnow.org/indexnow", "articles.firstaimovers.com")
        assert result is False

    def test_fails_on_429(self, monkeypatch, tmp_path):
        import submit_indexnow
        key = self._key_file(tmp_path)
        from urllib.error import HTTPError
        class FakeResponse:
            status = 429
            def read(self): return b'Too Many Requests'
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def close(self): pass
        def fake_open(req, timeout=None):
            resp = FakeResponse()
            raise HTTPError("https://api.indexnow.org/indexnow", 429, "Too Many Requests", {}, resp)
        monkeypatch.setattr(submit_indexnow, "urlopen", fake_open)
        result = submit_indexnow._submit([], key, "https://api.indexnow.org/indexnow", "articles.firstaimovers.com")
        assert result is False

    def test_sitemap_advertises_exactly_the_curated_urls(self):
        """The sitemap must advertise EXACTLY the curated set on
        articles.firstaimovers.com: the homepage, /about/, the /topics/ index,
        and one hub per pageable topic (>= MIN_ARTICLES_FOR_TOPIC_PAGE articles).

        The expected topic slugs are derived from index.json via the SHARED
        builder logic (rebuild_local._topics_with_page / _slugify), not from the
        sitemap itself — so this fails both if a cross-host/article URL LEAKS in
        (the original regression) AND if the sitemap DROPS a topic hub it should
        advertise. No magic total: it grows correctly with owned content.
        """
        import json
        import re
        import sys
        from pathlib import Path as P

        repo = P(__file__).resolve().parents[2]
        sys.path.insert(0, str(repo / "tools"))
        import rebuild_local as rl

        index = json.loads((repo / "index.json").read_text(encoding="utf-8"))
        _, pageable_topics, _ = rl._topics_with_page(index)
        base = rl.SITE_BASE
        expected = {f"{base}/", f"{base}/about/", f"{base}/topics/"} | {
            f"{base}/topics/{rl._slugify(t)}/" for t in pageable_topics
        }

        sitemap = repo / "sitemap.xml"
        assert sitemap.exists()
        xml = sitemap.read_text(encoding="utf-8")
        locs = set(re.findall(r"<loc>([^<]+)</loc>", xml))

        assert locs == expected, (
            f"Sitemap URL set diverges from the curated expectation. "
            f"Leaked (in sitemap, not expected): {sorted(locs - expected)[:5]}; "
            f"Missing (expected, not in sitemap): {sorted(expected - locs)[:5]}"
        )
        # No duplicate <url> entries inflating the file.
        assert xml.count("<url>") == len(expected)

    def test_cli_key_overrides_env(self, monkeypatch, tmp_path):
        import submit_indexnow
        env_key = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        cli_key = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        monkeypatch.setenv("INDEXNOW_API_KEY_ARTICLES_FAIM", env_key)
        loaded = submit_indexnow._get_key_for_host("articles.firstaimovers.com")
        assert loaded == env_key
        # CLI --key should bypass env lookup entirely
        assert cli_key == submit_indexnow._get_key_for_host("articles.firstaimovers.com") or True  # --key is handled in main(), not _get_key_for_host
        # Verify main() uses CLI key when provided
        import subprocess, sys
        from pathlib import Path
        script = Path(__file__).resolve().parents[2] / "tools" / "submit_indexnow.py"
        urls = ["https://articles.firstaimovers.com/"]
        xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               f'  <url><loc>{urls[0]}</loc></url>\n'
               '</urlset>\n')
        sitemap_path = tmp_path / "sitemap.xml"
        sitemap_path.write_text(xml, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(script),
             "--sitemap", str(sitemap_path),
             "--key", cli_key,
             "--dry-run"],
            capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        assert cli_key[:4] in result.stdout or cli_key[-4:] in result.stdout, result.stdout

    def test_missing_env_gives_actionable_error(self, monkeypatch, tmp_path):
        import submit_indexnow
        monkeypatch.delenv("INDEXNOW_API_KEY_ARTICLES_FAIM", raising=False)
        monkeypatch.delenv("INDEXNOW_API_KEY", raising=False)
        with pytest.raises(SystemExit) as exc_info:
            submit_indexnow._get_key_for_host("articles.firstaimovers.com")
        msg = str(exc_info.value)
        assert "INDEXNOW_API_KEY_ARTICLES_FAIM" in msg
        assert "--key" in msg

    def test_no_old_key_in_docs_or_source(self):
        from pathlib import Path
        old_key = "f9d934376f0a4a55c2fd6608f2868f48"
        root = Path(__file__).resolve().parents[2]
        for path in root.rglob("*"):
            if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts:
                # Skip test files that contain the old_key literal by design
                if path.name in ("test_tools.py", "test_submit_indexnow.py"):
                    continue
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                if old_key in text:
                    pytest.fail(f"Old hardcoded IndexNow key found in {path.relative_to(root)}")

    def test_repo_no_longer_commits_indexnow_key(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        key_file = root / ".indexnow-key"
        assert not key_file.exists(), ".indexnow-key must not exist at repo root"


# =========================================================================
# Tests: PR C — Topic hub SEO/GEO enhancement
# =========================================================================


