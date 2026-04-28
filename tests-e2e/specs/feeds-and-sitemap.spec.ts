import { test, expect } from '@playwright/test';

test.describe('Feeds and sitemap', () => {
  test('/feed.json returns valid JSON Feed 1.1', async ({ request }) => {
    const response = await request.get('/feed.json');
    expect(response.status()).toBe(200);
    expect(response.headers()['content-type']).toContain('application/json');

    const body = await response.json();
    expect(body.version).toBe('https://jsonfeed.org/version/1.1');
    expect(body.title).toContain('First AI Movers');
    expect(Array.isArray(body.items)).toBe(true);
    expect(body.items.length).toBeGreaterThan(0);
  });

  test('/sitemap.xml returns XML with ~80 urls', async ({ request }) => {
    const response = await request.get('/sitemap.xml');
    expect(response.status()).toBe(200);
    expect(response.headers()['content-type']).toContain('xml');

    const body = await response.text();
    // Count <url> entries
    const urlMatches = body.match(/<url>/g) || [];
    expect(urlMatches.length).toBeGreaterThanOrEqual(75);
    expect(urlMatches.length).toBeLessThanOrEqual(85);
  });

  test('/sitemap.xml does not include local /articles/ pages', async ({ request }) => {
    const response = await request.get('/sitemap.xml');
    const body = await response.text();
    expect(body).not.toContain('/articles/');
  });

  test('/robots.txt loads and references sitemap', async ({ request }) => {
    const response = await request.get('/robots.txt');
    expect(response.status()).toBe(200);

    const body = await response.text();
    expect(body).toContain('Sitemap:');
    expect(body).toContain('sitemap.xml');
  });

  test('/feed.xml returns valid Atom feed', async ({ request }) => {
    const response = await request.get('/feed.xml');
    expect(response.status()).toBe(200);
    expect(response.headers()['content-type']).toContain('xml');

    const body = await response.text();
    expect(body).toContain('<feed');
    expect(body).toContain('<title>');
  });

  test('/llms.txt exists', async ({ request }) => {
    const response = await request.get('/llms.txt');
    expect(response.status()).toBe(200);
  });

  test('/llms-full.txt exists', async ({ request }) => {
    const response = await request.get('/llms-full.txt');
    expect(response.status()).toBe(200);
  });
});
