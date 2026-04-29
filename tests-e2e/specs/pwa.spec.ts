import { test, expect } from '@playwright/test';

test.describe('PWA installability', () => {
  test('manifest is linked and fetchable', async ({ page }) => {
    await page.goto('/');
    const manifestLink = page.locator('link[rel="manifest"]');
    await expect(manifestLink).toHaveAttribute('href', '/manifest.webmanifest');

    const response = await page.request.get('/manifest.webmanifest');
    expect(response.ok()).toBe(true);
    const data = await response.json();
    expect(data.name).toBeTruthy();
    expect(data.short_name).toBeTruthy();
    expect(data.display).toMatch(/standalone|fullscreen|minimal-ui/);
    expect(data.icons).toBeInstanceOf(Array);
    expect(data.icons.some((i: { sizes: string }) => i.sizes === '192x192')).toBe(true);
    expect(data.icons.some((i: { sizes: string }) => i.sizes === '512x512')).toBe(true);
  });

  test('service worker registration script exists', async ({ page }) => {
    await page.goto('/');
    const script = page.locator('script[src="/pwa.js"]');
    await expect(script).toHaveCount(1);
  });

  test('theme-color meta is present', async ({ page }) => {
    await page.goto('/');
    const meta = page.locator('meta[name="theme-color"]');
    await expect(meta).toHaveAttribute('content', '#111827');
  });

  test('offline page is accessible', async ({ page }) => {
    const response = await page.goto('/offline/');
    expect(response?.ok()).toBe(true);
    await expect(page.locator('h1')).toContainText(/offline/i);
  });

  test('icons are fetchable', async ({ page }) => {
    for (const size of ['192', '512']) {
      const response = await page.request.get(`/icons/icon-${size}.png`);
      expect(response.ok()).toBe(true);
      expect(response.headers()['content-type']).toBe('image/png');
    }
  });
});
