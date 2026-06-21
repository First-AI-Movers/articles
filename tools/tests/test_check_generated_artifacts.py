#!/usr/bin/env python3
"""Tests for check_generated_artifacts.py."""

import sys
from pathlib import Path

import pytest

from check_generated_artifacts import check_artifacts, ARTIFACTS


class TestCheckGeneratedArtifacts:
    """Drift detection behaviour."""

    def _fake_rebuild_script(self, tmp_path: Path, python_code: str) -> list[str]:
        """Write a fake rebuild_local.py and return the subprocess cmd."""
        (tmp_path / "tools").mkdir(parents=True, exist_ok=True)
        rebuild = tmp_path / "tools" / "rebuild_local.py"
        rebuild.write_text(f"#!/usr/bin/env python3\n{python_code}\n", encoding="utf-8")
        return [sys.executable, str(rebuild)]

    def _write_artifacts(self, repo_root: Path):
        """Create committed artifact files (mkdir parent dirs for nested paths)."""
        for name in ARTIFACTS:
            path = repo_root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"content of {name}\n", encoding="utf-8")

    def test_no_drift_exits_zero(self, tmp_path):
        """When rebuild produces identical artifacts, check passes."""
        cmd = self._fake_rebuild_script(tmp_path, "print('noop')")
        self._write_artifacts(tmp_path)

        code, messages = check_artifacts(tmp_path, rebuild_cmd=cmd)
        assert code == 0
        assert messages == []

    def test_drift_exits_nonzero(self, tmp_path):
        """When rebuild changes an artifact, check fails."""
        cmd = self._fake_rebuild_script(
            tmp_path,
            "import pathlib; pathlib.Path('index.json').write_text('stale\\n')",
        )
        self._write_artifacts(tmp_path)

        code, messages = check_artifacts(tmp_path, rebuild_cmd=cmd)
        assert code == 1
        assert any("index.json" in m for m in messages)

    def test_report_lists_changed_artifact(self, tmp_path):
        """The failure message names the specific artifact that drifted."""
        cmd = self._fake_rebuild_script(
            tmp_path,
            "import pathlib; pathlib.Path('sitemap.xml').write_text('<new/>\\n')",
        )
        self._write_artifacts(tmp_path)

        code, messages = check_artifacts(tmp_path, rebuild_cmd=cmd)
        assert code == 1
        assert any("sitemap.xml" in m for m in messages)

    def test_does_not_modify_working_tree_after_check(self, tmp_path):
        """After the check, committed artifacts are restored to their originals."""
        cmd = self._fake_rebuild_script(
            tmp_path,
            "import pathlib; pathlib.Path('README.md').write_text('mutated\\n')",
        )
        self._write_artifacts(tmp_path)
        original = (tmp_path / "README.md").read_text(encoding="utf-8")

        check_artifacts(tmp_path, rebuild_cmd=cmd)

        assert (tmp_path / "README.md").read_text(encoding="utf-8") == original

    def test_site_dir_is_ignored(self, tmp_path):
        """Changes inside gitignored site/ do not count as drift."""
        cmd = self._fake_rebuild_script(
            tmp_path,
            "import pathlib; pathlib.Path('site').mkdir(exist_ok=True); pathlib.Path('site/index.html').write_text('new')",
        )
        self._write_artifacts(tmp_path)

        code, messages = check_artifacts(tmp_path, rebuild_cmd=cmd)
        assert code == 0
        assert messages == []

    def test_missing_artifact_reported(self, tmp_path):
        """If a committed artifact is missing, it is reported as drift."""
        cmd = self._fake_rebuild_script(tmp_path, "print('noop')")
        self._write_artifacts(tmp_path)
        (tmp_path / "feed.json").unlink()

        code, messages = check_artifacts(tmp_path, rebuild_cmd=cmd)
        assert code == 1
        assert any("feed.json" in m and "missing" in m for m in messages)

    def test_new_artifact_reported(self, tmp_path):
        """If an artifact is created but was not previously committed, it is reported."""
        cmd = self._fake_rebuild_script(
            tmp_path,
            "import pathlib; pathlib.Path('llms.txt').write_text('new corpus')",
        )
        # Write all artifacts EXCEPT llms.txt (mkdir parents for nested paths)
        for name in ARTIFACTS:
            if name != "llms.txt":
                path = tmp_path / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"content of {name}\n", encoding="utf-8")

        code, messages = check_artifacts(tmp_path, rebuild_cmd=cmd)
        assert code == 1
        assert any("llms.txt" in m and "new" in m for m in messages)

    def test_rebuild_failure_returns_nonzero(self, tmp_path):
        """If rebuild_local.py crashes, the check fails without modifying the tree."""
        cmd = self._fake_rebuild_script(tmp_path, "raise RuntimeError('boom')")
        self._write_artifacts(tmp_path)
        original = {name: (tmp_path / name).read_bytes() for name in ARTIFACTS}

        code, messages = check_artifacts(tmp_path, rebuild_cmd=cmd)
        assert code == 1
        assert any("boom" in m for m in messages)
        for name in ARTIFACTS:
            assert (tmp_path / name).read_bytes() == original[name]

    def test_multiple_drifts_all_reported(self, tmp_path):
        """Every drifted artifact is listed, not just the first."""
        cmd = self._fake_rebuild_script(
            tmp_path,
            "import pathlib; "
            "pathlib.Path('index.json').write_text('a'); "
            "pathlib.Path('feed.xml').write_text('b');",
        )
        self._write_artifacts(tmp_path)

        code, messages = check_artifacts(tmp_path, rebuild_cmd=cmd)
        assert code == 1
        assert len(messages) == 2
        assert any("index.json" in m for m in messages)
        assert any("feed.xml" in m for m in messages)


from check_generated_artifacts import _normalize_generation_dates as _n  # noqa: E402


class TestNormalizeGenerationDates:
    """Generation-date stamps are normalized; content dates are NOT.

    Locks ARTICLES-GENERATED-ARTIFACT-DRIFT-REFRESH-A: a build-date-only diff must
    not register as drift, but a real content-date change must still fail.
    """

    def test_index_last_updated_is_normalized(self):
        a = b'{\n  "last_updated": "2026-06-06",\n  "n": 1\n}'
        b = b'{\n  "last_updated": "2026-06-21",\n  "n": 1\n}'
        assert _n("index.json", a) == _n("index.json", b)

    def test_readme_datemodified_is_normalized(self):
        a = b'"dateModified": "2026-06-06"'
        b = b'"dateModified": "2026-06-21"'
        assert _n("README.md", a) == _n("README.md", b)

    def test_llms_generated_footer_is_normalized(self):
        a = b"# llms\n\n- Generated: 2026-06-06\n\nbody\n"
        b = b"# llms\n\n- Generated: 2026-06-21\n\nbody\n"
        for fname in ("llms.txt", "llms-index.txt", "llms-full.txt", "llms-recent.txt"):
            assert _n(fname, a) == _n(fname, b), fname

    def test_sitemap_static_page_lastmod_is_normalized(self):
        tmpl = (b"<url>\n  <loc>https://articles.firstaimovers.com/</loc>\n"
                b"  <lastmod>%s</lastmod>\n  <changefreq>weekly</changefreq>\n</url>")
        assert _n("sitemap.xml", tmpl % b"2026-06-06") == _n("sitemap.xml", tmpl % b"2026-06-21")

    # --- content dates MUST NOT be normalized (real freshness changes still fail) ---

    def test_sitemap_topic_hub_lastmod_is_NOT_normalized(self):
        # a topic hub page's <lastmod> is the newest-article (content) date.
        tmpl = (b"<url>\n  <loc>https://articles.firstaimovers.com/topics/ai-agents/</loc>\n"
                b"  <lastmod>%s</lastmod>\n</url>")
        assert _n("sitemap.xml", tmpl % b"2026-04-24") != _n("sitemap.xml", tmpl % b"2026-06-21")

    def test_index_article_published_date_is_NOT_normalized(self):
        a = b'{"articles": [{"published_date": "2026-06-06"}]}'
        b = b'{"articles": [{"published_date": "2026-06-21"}]}'
        assert _n("index.json", a) != _n("index.json", b)
