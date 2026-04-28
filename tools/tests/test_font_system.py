"""Tests for the self-hosted font system (E17b)."""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
STATIC_CSS = REPO_ROOT / "static" / "style.css"
STATIC_FONTS = REPO_ROOT / "static" / "fonts"
SITE_FONTS = REPO_ROOT / "site" / "fonts"
DOCS_DESIGN = REPO_ROOT / "docs" / "DESIGN.md"


class TestFontAssets:
    """Font files are present, licensed, and copied by the build."""

    def test_inter_font_files_exist(self):
        inter = STATIC_FONTS / "inter"
        assert (inter / "Inter-Regular.woff2").exists()
        assert (inter / "Inter-SemiBold.woff2").exists()
        assert (inter / "Inter-Bold.woff2").exists()
        assert (inter / "LICENSE.txt").exists()

    def test_jetbrains_mono_font_files_exist(self):
        jbm = STATIC_FONTS / "jetbrains-mono"
        assert (jbm / "JetBrainsMono-Regular.woff2").exists()
        assert (jbm / "JetBrainsMono-SemiBold.woff2").exists()
        assert (jbm / "JetBrainsMono-Bold.woff2").exists()
        assert (jbm / "LICENSE.txt").exists()

    def test_fonts_copied_to_site_by_rebuild(self):
        # site/fonts may be absent before rebuild; verify after a rebuild has run
        if not SITE_FONTS.exists():
            pytest.skip("site/fonts absent; run rebuild_local.py first")
        assert (SITE_FONTS / "inter" / "Inter-Regular.woff2").exists()
        assert (SITE_FONTS / "jetbrains-mono" / "JetBrainsMono-Regular.woff2").exists()


class TestFontCss:
    """CSS contains correct @font-face declarations and no external font calls."""

    @pytest.fixture(scope="class")
    def css(self):
        return STATIC_CSS.read_text(encoding="utf-8")

    def test_font_face_blocks_present(self, css):
        assert "@font-face" in css
        assert 'font-family: "Inter"' in css
        assert 'font-family: "JetBrains Mono"' in css

    def test_font_display_swap_used(self, css):
        assert css.count("font-display: swap") >= 2

    def test_font_urls_are_local(self, css):
        for line in css.splitlines():
            if "url(" in line and "format(\"woff2\")" in line:
                assert "/fonts/" in line, f"Font URL must be local: {line}"
                assert "http" not in line, f"Font URL must not be external: {line}"

    def test_no_google_fonts_in_css(self, css):
        assert "fonts.googleapis.com" not in css
        assert "fonts.gstatic.com" not in css

    def test_no_cdn_font_references_in_css(self, css):
        assert "cdn.jsdelivr" not in css
        assert "unpkg.com" not in css

    def test_font_tokens_use_self_hosted_first(self, css):
        assert '--font-body: "Inter"' in css
        assert '--font-ui: "Inter"' in css
        assert '--font-mono: "JetBrains Mono"' in css


class TestNoExternalFontReferences:
    """No external font calls in templates, docs, or package files."""

    def test_no_google_fonts_in_templates(self):
        for tmpl in (REPO_ROOT / "templates").rglob("*.html.j2"):
            text = tmpl.read_text(encoding="utf-8")
            assert "fonts.googleapis.com" not in text, f"Found in {tmpl}"
            assert "fonts.gstatic.com" not in text, f"Found in {tmpl}"

    def test_no_google_fonts_in_docs(self):
        for md in (REPO_ROOT / "docs").rglob("*.md"):
            text = md.read_text(encoding="utf-8")
            assert "fonts.googleapis.com" not in text, f"Found in {md}"
            assert "fonts.gstatic.com" not in text, f"Found in {md}"

    def test_no_font_cdn_in_package_files(self):
        pkg = REPO_ROOT / "package.json"
        lock = REPO_ROOT / "package-lock.json"
        for p in (pkg, lock):
            if p.exists():
                text = p.read_text(encoding="utf-8")
                assert "fonts.googleapis.com" not in text
                assert "fonts.gstatic.com" not in text


class TestDesignDocs:
    """Design documentation exists and covers typography."""

    def test_design_md_exists(self):
        assert DOCS_DESIGN.exists()

    def test_design_md_covers_font_policy(self):
        text = DOCS_DESIGN.read_text(encoding="utf-8")
        assert "font" in text.lower()
        assert "self-host" in text.lower() or "self host" in text.lower()
        assert "Inter" in text
        assert "JetBrains Mono" in text


class TestRebuildCopiesFonts:
    """Rebuild script copies font files into site output."""

    def test_rebuild_creates_site_fonts(self, monkeypatch, tmp_path):
        # Import rebuild module and run a minimal build
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        import rebuild_local as m

        (tmp_path / "articles").mkdir(exist_ok=True)
        (tmp_path / "templates").mkdir(exist_ok=True)
        (tmp_path / "static").mkdir(exist_ok=True)
        import shutil
        shutil.copytree(REPO_ROOT / "templates", tmp_path / "templates", dirs_exist_ok=True)
        shutil.copytree(REPO_ROOT / "static", tmp_path / "static", dirs_exist_ok=True)
        shutil.copy(REPO_ROOT / "hernanicosta.json", tmp_path / "hernanicosta.json")

        monkeypatch.setattr(m, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(m, "TEMPLATE_DIR", tmp_path / "templates")
        monkeypatch.setattr(m, "STATIC_DIR", tmp_path / "static")
        monkeypatch.setattr(m, "SITE_DIR", tmp_path / "site")

        index = {"articles": [], "topics": {}, "topics_with_page": []}
        m.build_site(index)

        site_fonts = tmp_path / "site" / "fonts"
        assert (site_fonts / "inter" / "Inter-Regular.woff2").exists()
        assert (site_fonts / "jetbrains-mono" / "JetBrainsMono-Regular.woff2").exists()
        assert (site_fonts / "inter" / "LICENSE.txt").exists()
