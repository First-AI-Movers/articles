# Design System

This document describes the visual design, typography, and asset policies for the First AI Movers article archive.

## Typography

### Goals

- Publication-grade readability for long-form content.
- Consistent, neutral sans-serif for UI and headings.
- Clear monospace for code and metadata.
- No external runtime font dependencies (privacy, performance, reproducibility).

### Font stack

| Token | Primary | Fallbacks |
|---|---|---|
| `--font-body` | Inter | ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif |
| `--font-ui` | Inter | ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif |
| `--font-mono` | JetBrains Mono | ui-monospace, "SF Mono", Menlo, Monaco, Consolas, monospace |

Georgia remains available as a fallback via the system font stack if Inter fails to load.

### Self-hosting policy

All font assets are vendored under `static/fonts/` and copied into `site/fonts/` during build. No Google Fonts, no CDN calls, no third-party font services at runtime.

### Font source and license

| Font | Source | License | Weights vendored |
|---|---|---|---|
| Inter | `@fontsource/inter` v5.2.8 | SIL Open Font License 1.1 | 400, 600, 700 |
| JetBrains Mono | `@fontsource/jetbrains-mono` v5.2.8 | SIL Open Font License 1.1 | 400, 600, 700 |

License texts are included as `static/fonts/*/LICENSE.txt`.

### Asset paths

```text
static/fonts/
  inter/
    LICENSE.txt
    Inter-Regular.woff2
    Inter-SemiBold.woff2
    Inter-Bold.woff2
  jetbrains-mono/
    LICENSE.txt
    JetBrainsMono-Regular.woff2
    JetBrainsMono-SemiBold.woff2
    JetBrainsMono-Bold.woff2
```

### Updating fonts

1. Verify the new version is from an official source (fontsource npm packages or upstream GitHub releases).
2. Replace `.woff2` files; keep `LICENSE.txt` in sync.
3. Run `python3 tools/rebuild_local.py --dry-run` and verify fonts copy to `site/fonts/`.
4. Run `python3 -m pytest tools/tests/test_font_system.py -v`.
5. Run `npm run test:e2e`.
6. Commit font assets, CSS, tests, and docs together.

## Visual regression

Four Playwright screenshot baselines guard against unintended visual changes:

| Baseline | Page | Selector |
|---|---|---|
| `home.png` | `/` | Viewport (1280×900) |
| `topic-ai-strategy.png` | `/topics/ai-strategy/` | Viewport |
| `article.png` | `/articles/09a0404f9db0/` | Viewport |
| `about.png` | `/about/` | Viewport |

All baselines are captured with:
- Dark theme forced
- `prefers-reduced-motion: reduce`
- Fonts fully loaded (`document.fonts.ready`)
- `maxDiffPixels: 35000` tolerance for cross-platform font rendering differences

Update after intentional design changes:

```bash
npx playwright test tests-e2e/specs/visual.spec.ts --update-snapshots
```

## Performance & audit

Lighthouse CI is **deferred**. The project already has Playwright E2E coverage and deterministic screenshot baselines. Lighthouse can be run manually for release checks and added to CI later once the design layer is fully stable.

## What E17b does **not** include

- Full visual redesign beyond font integration.
- Pico.css or any other third-party CSS framework.
- Runtime CDN dependencies of any kind.

## Theme

Light and dark modes are driven by CSS custom properties in `static/style.css`. The default is dark. A theme toggle stores preference in `localStorage` and prevents flash-of-unstyled-content with an inline script in `base.html.j2`.

## Colour tokens

| Token | Light | Dark |
|---|---|---|
| `--text` | `#1a1a1a` | `#e0e0e0` |
| `--muted` | `#5a5a5a` | `#aaa` |
| `--bg` | `#fafafa` | `#121212` |
| `--card-bg` | `#fff` | `#1a1a1a` |
| `--accent` | `#b5450f` | `#e67e45` |
| `--link` | `#0a58ca` | `#6cb4f5` |

The accent colour meets WCAG AA contrast (≥4.5:1) in both modes.
