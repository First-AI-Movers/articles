import { test, expect } from '@playwright/test';

test.describe('Topics', () => {
  test('topics index loads and shows All Topics heading', async ({ page }) => {
    await page.goto('/topics/');
    await expect(page).toHaveTitle(/All Topics/);
    const h1 = page.getByRole('heading', { level: 1, name: 'All Topics' });
    await expect(h1).toBeVisible();
  });

  test('topics index has search input', async ({ page }) => {
    await page.goto('/topics/');
    const search = page.getByRole('searchbox', { name: /Search articles/i });
    await expect(search).toBeVisible();
  });

  test('topic list contains linked topics', async ({ page }) => {
    await page.goto('/topics/');
    const topicLinks = page.locator('.topic-list a');
    await expect(topicLinks.first()).toBeVisible();
    const count = await topicLinks.count();
    expect(count).toBeGreaterThan(0);
  });

  test('sample topic page has heading, article cards, and JSON-LD', async ({ page }) => {
    // ai-strategy is a stable canonical topic
    await page.goto('/topics/ai-strategy/');

    const h1 = page.getByRole('heading', { level: 1 });
    await expect(h1).toContainText('AI Strategy');

    // Breadcrumb
    const breadcrumb = page.getByRole('navigation', { name: 'Breadcrumb' });
    await expect(breadcrumb).toBeVisible();
    await expect(breadcrumb).toContainText('Home');
    await expect(breadcrumb).toContainText('Topics');

    // Article cards exist
    const articleCards = page.locator('article h3 a');
    await expect(articleCards.first()).toBeVisible();

    // Meta info
    await expect(page.locator('.meta')).toContainText(/articles/);

    // JSON-LD scripts
    const jsonLdScripts = page.locator('script[type="application/ld+json"]');
    const count = await jsonLdScripts.count();
    expect(count).toBeGreaterThanOrEqual(1);
    // Scripts are not "visible" in Playwright semantics; verify attached.
    await expect(jsonLdScripts.first()).toBeAttached();
  });

  test('topic page may have curated intro or key themes', async ({ page }) => {
    await page.goto('/topics/ai-strategy/');
    // Some topics have intros; if present, validate structure
    const intro = page.locator('.topic-intro');
    if (await intro.isVisible().catch(() => false)) {
      const keyThemes = intro.locator('.key-themes li');
      // Only assert if key themes are actually rendered
      if (await keyThemes.count() > 0) {
        await expect(keyThemes.first()).toBeVisible();
      }
    }
  });
});
