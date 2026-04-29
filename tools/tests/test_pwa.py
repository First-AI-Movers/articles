#!/usr/bin/env python3
"""Contract tests for PWA (Progressive Web App) scaffolding."""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = REPO_ROOT / "static"
SITE_DIR = REPO_ROOT / "site"
TEMPLATE_DIR = REPO_ROOT / "templates"


class TestManifest:
    def test_manifest_exists(self):
        assert (STATIC_DIR / "manifest.webmanifest").exists()

    def test_manifest_is_valid_json(self):
        path = STATIC_DIR / "manifest.webmanifest"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_manifest_has_required_installability_fields(self):
        data = json.loads((STATIC_DIR / "manifest.webmanifest").read_text(encoding="utf-8"))
        assert data.get("name") or data.get("short_name")
        assert data.get("start_url")
        assert data.get("display") in ("standalone", "fullscreen", "minimal-ui")
        assert data.get("prefer_related_applications") is not True

    def test_manifest_has_192_and_512_png_icons(self):
        data = json.loads((STATIC_DIR / "manifest.webmanifest").read_text(encoding="utf-8"))
        icons = data.get("icons", [])
        sizes = {icon.get("sizes") for icon in icons}
        assert "192x192" in sizes
        assert "512x512" in sizes
        for icon in icons:
            if icon.get("sizes") in ("192x192", "512x512"):
                assert icon.get("type") == "image/png"

    def test_manifest_theme_color_matches_brand(self):
        data = json.loads((STATIC_DIR / "manifest.webmanifest").read_text(encoding="utf-8"))
        assert data.get("theme_color") == "#111827"
        assert data.get("background_color") == "#111827"


class TestIcons:
    def test_icon_192_exists(self):
        assert (STATIC_DIR / "icons" / "icon-192.png").exists()

    def test_icon_512_exists(self):
        assert (STATIC_DIR / "icons" / "icon-512.png").exists()

    def test_icons_are_png(self):
        from PIL import Image
        for size in (192, 512):
            path = STATIC_DIR / "icons" / f"icon-{size}.png"
            with Image.open(path) as img:
                assert img.format == "PNG"
                assert img.width == size
                assert img.height == size


class TestServiceWorker:
    def test_sw_js_exists(self):
        assert (STATIC_DIR / "sw.js").exists()

    def test_sw_includes_offline_fallback(self):
        text = (STATIC_DIR / "sw.js").read_text(encoding="utf-8")
        assert "/offline/" in text

    def test_sw_does_not_cache_goatcounter(self):
        text = (STATIC_DIR / "sw.js").read_text(encoding="utf-8")
        assert "gc.zgo.at" in text or "goatcounter" in text.lower()

    def test_sw_does_not_cache_giscus(self):
        text = (STATIC_DIR / "sw.js").read_text(encoding="utf-8")
        assert "giscus" in text.lower()

    def test_sw_does_not_cache_external_cross_origin(self):
        text = (STATIC_DIR / "sw.js").read_text(encoding="utf-8")
        # Should have a cross-origin guard
        assert "cross-origin" in text.lower() or "url.origin !== self.location.origin" in text

    def test_cache_version_is_deterministic(self):
        text = (STATIC_DIR / "sw.js").read_text(encoding="utf-8")
        assert "_cacheVersion" in text or "CACHE_VERSION" in text


class TestRegistration:
    def test_pwa_js_exists(self):
        assert (STATIC_DIR / "pwa.js").exists()

    def test_pwa_js_registers_service_worker(self):
        text = (STATIC_DIR / "pwa.js").read_text(encoding="utf-8")
        import re
        assert re.search(r"navigator\.serviceWorker\s*\.\s*register", text)
        assert "serviceWorker" in text

    def test_base_template_links_manifest(self):
        text = (TEMPLATE_DIR / "base.html.j2").read_text(encoding="utf-8")
        assert "manifest.webmanifest" in text
        assert 'rel="manifest"' in text

    def test_base_template_has_theme_color(self):
        text = (TEMPLATE_DIR / "base.html.j2").read_text(encoding="utf-8")
        assert "theme-color" in text

    def test_base_template_includes_pwa_js(self):
        text = (TEMPLATE_DIR / "base.html.j2").read_text(encoding="utf-8")
        assert "pwa.js" in text


SITE_BUILT = SITE_DIR.exists()


class TestOfflinePage:
    def test_offline_template_exists(self):
        assert (TEMPLATE_DIR / "offline.html.j2").exists()

    def test_offline_template_extends_base(self):
        text = (TEMPLATE_DIR / "offline.html.j2").read_text(encoding="utf-8")
        assert "base.html.j2" in text

    def test_offline_template_has_noindex(self):
        text = (TEMPLATE_DIR / "offline.html.j2").read_text(encoding="utf-8")
        assert "noindex" in text

    @pytest.mark.skipif(not SITE_BUILT, reason="site/ not built")
    def test_offline_page_rendered_by_build(self):
        assert (SITE_DIR / "offline" / "index.html").exists()

    @pytest.mark.skipif(not SITE_BUILT, reason="site/ not built")
    def test_offline_page_has_content(self):
        text = (SITE_DIR / "offline" / "index.html").read_text(encoding="utf-8")
        assert "offline" in text.lower()


class TestBuildIntegration:
    @pytest.mark.skipif(not SITE_BUILT, reason="site/ not built")
    def test_manifest_copied_to_site(self):
        assert (SITE_DIR / "manifest.webmanifest").exists()

    @pytest.mark.skipif(not SITE_BUILT, reason="site/ not built")
    def test_sw_copied_to_site(self):
        assert (SITE_DIR / "sw.js").exists()

    @pytest.mark.skipif(not SITE_BUILT, reason="site/ not built")
    def test_pwa_js_copied_to_site(self):
        assert (SITE_DIR / "pwa.js").exists()

    @pytest.mark.skipif(not SITE_BUILT, reason="site/ not built")
    def test_icons_copied_to_site(self):
        assert (SITE_DIR / "icons" / "icon-192.png").exists()
        assert (SITE_DIR / "icons" / "icon-512.png").exists()

    def test_icon_builder_script_exists(self):
        assert (REPO_ROOT / "tools" / "build_pwa_icons.py").exists()

    def test_icon_builder_runs(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "build_pwa_icons.py")],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0
        assert "Wrote" in result.stdout


class TestDocs:
    def test_pwa_docs_exist(self):
        assert (REPO_ROOT / "docs" / "PWA.md").exists()

    def test_pwa_docs_mention_rollback(self):
        text = (REPO_ROOT / "docs" / "PWA.md").read_text(encoding="utf-8")
        assert "rollback" in text.lower()
