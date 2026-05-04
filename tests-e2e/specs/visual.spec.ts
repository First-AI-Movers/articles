import { test, expect } from '@playwright/test';

/**
 * Visual regression baseline tests (E17c).
 *
 * These tests capture viewport screenshots of key pages to detect
 * unintended visual regressions after design changes.
 *
 * Prerequisites:
 *   python3 tools/rebuild_local.py   # ensure site/ is up to date
 *
 * Update snapshots after intentional visual changes:
 *   npx playwright test tests-e2e/specs/visual.spec.ts --update-snapshots
 */

const VIEWPORT = { width: 1280, height: 900 };

async function prepareStablePage(page, path: string) {
  // Force dark theme and reduced motion for deterministic rendering
  await page.addInitScript(() => {
    localStorage.setItem('theme', 'dark');
  });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.setViewportSize(VIEWPORT);
  await page.goto(path);
  // Wait for self-hosted fonts to finish loading before capturing
  await page.evaluate(() => document.fonts.ready);
  // Small extra wait for any layout settling
  await page.waitForTimeout(200);
}

test.describe('Visual regression baselines', () => {
  test('home page', async ({ page }) => {
    await prepareStablePage(page, '/');

    // The homepage renders dynamic, content-driven text in regions that
    // change every time an article is ingested:
    //   - .lede paragraph (article-count summary, in home.html.j2)
    //   - .stats grid (4-cell count-and-date block, in home.html.j2)
    //   - latest-articles list (newest article cards rotate)
    //   - footer-stats span (in base.html.j2 — included defensively in
    //     case the clip ever extends below the fold)
    //
    // Masking these regions lets the visual test cover layout,
    // typography, dark-mode chrome, and structural rendering, while
    // ignoring the count/date/recent-cards drift that issue #159
    // identified as the reason ingestion PRs always failed CI.
    //
    // The masked content is asserted deterministically below so we
    // don't lose coverage of the values themselves — we just stop
    // burning a full screenshot diff on them.
    const dynamicMasks = [
      page.getByTestId('archive-stats-summary'),
      page.getByTestId('archive-stats-grid'),
      page.getByTestId('latest-articles'),
      page.getByTestId('archive-footer-stats'),
    ];

    await expect(page).toHaveScreenshot('home.png', {
      fullPage: false,
      maxDiffPixels: 35000,
      clip: { x: 0, y: 0, width: VIEWPORT.width, height: VIEWPORT.height },
      mask: dynamicMasks,
    });

    // Deterministic content checks — the masked regions still need to
    // contain the expected shape so a missing/empty render doesn't slip
    // through as a "harmless mask diff".
    const summary = page.getByTestId('archive-stats-summary');
    await expect(summary).toContainText(/original articles/i);

    const statsGrid = page.getByTestId('archive-stats-grid');
    await expect(statsGrid).toContainText(/articles/i);
    await expect(statsGrid).toContainText(/canonical topics/i);
    await expect(statsGrid).toContainText(/first article/i);
    await expect(statsGrid).toContainText(/most recent/i);

    const latest = page.getByTestId('latest-articles');
    await expect(latest).toBeVisible();
    // At least one article card should render — the partial
    // (templates/partials/article_card.html.j2) uses <article class="card">.
    await expect(latest.locator('article.card').first()).toBeVisible();
  });

  test('topic page with intro', async ({ page }) => {
    await prepareStablePage(page, '/topics/ai-strategy/');
    await expect(page).toHaveScreenshot('topic-ai-strategy.png', {
      fullPage: false,
      maxDiffPixels: 35000,
      clip: { x: 0, y: 0, width: VIEWPORT.width, height: VIEWPORT.height },
    });
  });

  test('article page', async ({ page }) => {
    // Use a stable article slug (first alphabetically, hash-based)
    await prepareStablePage(page, '/articles/09a0404f9db0/');
    await expect(page).toHaveScreenshot('article.png', {
      fullPage: false,
      maxDiffPixels: 35000,
      clip: { x: 0, y: 0, width: VIEWPORT.width, height: VIEWPORT.height },
    });
  });

  test('about page', async ({ page }) => {
    await prepareStablePage(page, '/about/');
    await expect(page).toHaveScreenshot('about.png', {
      fullPage: false,
      maxDiffPixels: 35000,
      clip: { x: 0, y: 0, width: VIEWPORT.width, height: VIEWPORT.height },
    });
  });
});
