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
    await expect(page).toHaveScreenshot('home.png', {
      fullPage: false,
      maxDiffPixels: 35000,
      clip: { x: 0, y: 0, width: VIEWPORT.width, height: VIEWPORT.height },
    });
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
