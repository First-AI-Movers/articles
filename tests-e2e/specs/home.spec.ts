import { test, expect } from '@playwright/test';

test.describe('Home page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('loads with correct title and heading', async ({ page }) => {
    await expect(page).toHaveTitle(/First AI Movers/);
    const h1 = page.getByRole('heading', { level: 1 });
    await expect(h1).toContainText('First AI Movers');
  });

  test('defaults to dark mode', async ({ page }) => {
    const html = page.locator('html');
    await expect(html).toHaveAttribute('data-theme', 'dark');
  });

  test('theme toggle switches to light and persists after reload', async ({ page }) => {
    const toggle = page.locator('#theme-toggle');
    await expect(toggle).toBeVisible();

    // Click to switch to light
    await toggle.click();
    const html = page.locator('html');
    await expect(html).toHaveAttribute('data-theme', 'light');

    // Reload and verify persistence via localStorage
    await page.reload();
    await expect(html).toHaveAttribute('data-theme', 'light');

    // Toggle back to dark for cleanliness
    await toggle.click();
    await expect(html).toHaveAttribute('data-theme', 'dark');
  });

  test('skip link exists and targets main content', async ({ page }) => {
    const skipLink = page.getByRole('link', { name: 'Skip to content' });
    await expect(skipLink).toHaveAttribute('href', '#main-content');
  });

  test('primary navigation has accessible label', async ({ page }) => {
    const nav = page.getByRole('navigation', { name: 'Primary' });
    await expect(nav).toBeVisible();
    await expect(nav.getByRole('link', { name: 'Home' })).toBeVisible();
    await expect(nav.getByRole('link', { name: 'Topics' })).toBeVisible();
    await expect(nav.getByRole('link', { name: 'About' })).toBeVisible();
  });

  test('search box exists with accessible label', async ({ page }) => {
    const search = page.getByRole('searchbox', { name: /Search articles/i });
    await expect(search).toBeVisible();
  });

  test('stats section shows article count', async ({ page }) => {
    const stats = page.locator('.stats');
    await expect(stats).toBeVisible();
    await expect(stats).toContainText(/articles/);
  });

  test('latest articles section is present', async ({ page }) => {
    const latestHeading = page.getByRole('heading', { name: 'Latest articles' });
    await expect(latestHeading).toBeVisible();
    const cards = page.locator('article');
    await expect(cards.first()).toBeVisible();
  });
});
