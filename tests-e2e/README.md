# Playwright E2E Tests

Browser-level end-to-end coverage for the First AI Movers Article Archive static site.

## Scope

These tests prove the **generated site** works in a real browser:
- Navigation, theme toggle, search
- Topic hubs, article pages, feeds, sitemap
- Accessibility landmarks and semantic markup

They do **not** replace the Python unit/integration suite (`tools/tests/`). E2E validates rendered output; Python validates generation logic.

## Install

```bash
cd articles/
npm install
npx playwright install chromium
```

## Build prerequisite

The E2E suite runs against the built `site/` directory:

```bash
python3 tools/rebuild_local.py
```

## Run locally

```bash
npm run test:e2e
npm run test:e2e:report   # open HTML report
```

Playwright starts a local Python static server on `127.0.0.1:4173` automatically.

## CI

`.github/workflows/e2e.yml` runs these on every PR and push to `main`.
It builds `site/`, installs Playwright Chromium, runs the suite, and uploads
traces + HTML reports on failure.

## How to add a new E2E test

1. Create `tests-e2e/specs/<feature>.spec.ts`
2. Import `{ test, expect } from '@playwright/test'`
3. Prefer semantic selectors:
   - `page.getByRole('heading', { name: '...' })`
   - `page.getByRole('navigation', { name: 'Primary' })`
   - `page.getByLabel('...')`
   - `page.getByText('...')`
4. Avoid brittle CSS selectors unless no semantic alternative exists.
5. Do not depend on external network or live production URLs.
6. Run `npm run test:e2e` to verify.

## Selector guidance

| Element | Preferred selector |
|---|---|
| Skip link | `page.getByRole('link', { name: 'Skip to content' })` |
| Primary nav | `page.getByRole('navigation', { name: 'Primary' })` |
| Breadcrumb | `page.getByRole('navigation', { name: 'Breadcrumb' })` |
| Search | `page.getByRole('searchbox', { name: /Search articles/i })` |
| Theme toggle | `page.locator('#theme-toggle')` |
| Main landmark | `page.getByRole('main')` |
| Article cards | `page.locator('article h3 a')` |

## What belongs in E2E vs Python tests

| Concern | Layer |
|---|---|
| Sitemap has 80 URLs | Python (generation logic) + E2E (HTTP response) |
| Feed JSON schema | Python (generation logic) + E2E (parseable response) |
| `noindex` on article pages | Python (template output) + E2E (meta tag in browser) |
| Theme toggle persistence | E2E (browser localStorage) |
| Skip link visibility on focus | E2E (keyboard interaction) |
| Search result rendering | E2E (DOM updates) |
| Tag normalization rules | Python only |
| Schema validation | Python only |

## Axe accessibility testing

Axe-core via `axe-playwright` is documented as a follow-up in ROADMAP.md.
The current suite covers semantic a11y checks (landmarks, labels, focus,
heading order). Automated axe scanning will be added once the Playwright
foundation is proven stable.
