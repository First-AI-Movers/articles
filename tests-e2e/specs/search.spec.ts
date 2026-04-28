import { test, expect } from '@playwright/test';

test.describe('Search', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for search index to load
    const search = page.getByRole('searchbox', { name: /Search articles/i });
    await search.fill('');
    // Small delay to allow index.json fetch to start
    await page.waitForTimeout(300);
  });

  test('search for "governance" returns results', async ({ page }) => {
    const search = page.getByRole('searchbox', { name: /Search articles/i });
    await search.fill('governance');

    const results = page.locator('#search-results .search-result');
    await expect(results.first()).toBeVisible({ timeout: 5000 });
    const count = await results.count();
    expect(count).toBeGreaterThan(0);
  });

  test('nonsense query shows empty state', async ({ page }) => {
    const search = page.getByRole('searchbox', { name: /Search articles/i });
    await search.fill('xyznonsense12345');

    const empty = page.locator('#search-results .search-empty');
    await expect(empty).toBeVisible({ timeout: 5000 });
    await expect(empty).toContainText(/No articles found/i);
  });

  test('search works on topics index page', async ({ page }) => {
    await page.goto('/topics/');
    const search = page.getByRole('searchbox', { name: /Search articles/i });
    await search.fill('strategy');

    const results = page.locator('#search-results .search-result');
    await expect(results.first()).toBeVisible({ timeout: 5000 });
    const count = await results.count();
    expect(count).toBeGreaterThan(0);
  });
});
