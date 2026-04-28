import { test, expect } from '@playwright/test';

test.describe('Accessibility semantics', () => {
  test('main landmark exists on home', async ({ page }) => {
    await page.goto('/');
    const main = page.getByRole('main');
    await expect(main).toBeVisible();
    await expect(main).toHaveAttribute('id', 'main-content');
  });

  test('skip link becomes visible on keyboard focus', async ({ page }) => {
    await page.goto('/');
    const skipLink = page.locator('.skip-link');

    // Initially hidden (visually) but in the DOM
    await expect(skipLink).toBeAttached();

    // Tab to it
    await page.keyboard.press('Tab');
    await expect(skipLink).toBeFocused();
    await expect(skipLink).toBeVisible();
  });

  test('theme toggle has aria-pressed', async ({ page }) => {
    await page.goto('/');
    const toggle = page.locator('#theme-toggle');
    await expect(toggle).toHaveAttribute('aria-pressed', /.*/);
  });

  test('breadcrumb on topic page uses aria-label=Breadcrumb', async ({ page }) => {
    await page.goto('/topics/ai-strategy/');
    const breadcrumb = page.locator('nav[aria-label="Breadcrumb"]');
    await expect(breadcrumb).toBeVisible();
  });

  test('breadcrumb on article page uses aria-label=Breadcrumb', async ({ page }) => {
    await page.goto('/topics/ai-strategy/');
    await page.locator('article h3 a').first().click();
    await page.waitForURL(/\/articles\//);

    const breadcrumb = page.locator('nav[aria-label="Breadcrumb"]');
    await expect(breadcrumb).toBeVisible();
  });

  test('no horizontal overflow at mobile width', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = await page.evaluate(() => window.innerWidth);
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 1); // allow 1px rounding
  });

  test('article page headings are in logical order', async ({ page }) => {
    await page.goto('/topics/ai-strategy/');
    await page.locator('article h3 a').first().click();
    await page.waitForURL(/\/articles\//);

    const h1 = page.locator('h1');
    await expect(h1).toHaveCount(1);

    // If TOC exists, it has an h2; article body may have h2s.
    // We just verify there are no h1s inside article body beyond the main one.
    const extraH1 = page.locator('.article-body h1');
    await expect(extraH1).toHaveCount(0);
  });
});
