#!/usr/bin/env python3
"""Generate PWA icons from deterministic SVG source.

Usage:
    python3 tools/build_pwa_icons.py

Outputs:
    static/icons/icon-192.png
    static/icons/icon-512.png

The source is an inline SVG so the build is fully deterministic and
requires no external image assets.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "static" / "icons"
SIZES = [192, 512]

# Brand colors from static/style.css
BG_COLOR = "#111827"
ACCENT_COLOR = "#b5450f"

SVG_TEMPLATE = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" fill="{bg}"/>
  <circle cx="256" cy="256" r="160" fill="{accent}"/>
</svg>'''


def _svg_to_png(svg_bytes: bytes, size: int) -> bytes:
    try:
        import cairosvg
    except ImportError:
        # Fallback: use Pillow to render a simple geometric icon
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (size, size), BG_COLOR)
        draw = ImageDraw.Draw(img)
        # Draw a centered circle
        padding = size // 8
        draw.ellipse(
            [padding, padding, size - padding, size - padding],
            fill=ACCENT_COLOR,
        )
        import io
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    return cairosvg.svg2png(bytestring=svg_bytes, output_width=size, output_height=size)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    svg = SVG_TEMPLATE.format(bg=BG_COLOR, accent=ACCENT_COLOR).encode("utf-8")

    for size in SIZES:
        out_path = OUT_DIR / f"icon-{size}.png"
        png_data = _svg_to_png(svg, size)
        out_path.write_bytes(png_data)
        print(f"[pwa-icons] Wrote {out_path} ({size}x{size})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
