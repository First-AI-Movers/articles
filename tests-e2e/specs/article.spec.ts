import { test, expect } from '@playwright/test';

test.describe('Article page', () => {
  test('dynamically discovered article has correct archive semantics', async ({ page }) => {
    // Navigate to a stable topic page and click the first article card.
    // This avoids hardcoding a slug that could change.
    await page.goto('/topics/ai-strategy/');
    const firstArticleLink = page.locator('article h3 a').first();
    await expect(firstArticleLink).toBeVisible();

    // Capture the article title before navigating
    const articleTitle = await firstArticleLink.textContent() || '';
    await firstArticleLink.click();

    // Wait for navigation to article page
    await page.waitForURL(/\/articles\//);

    // robots: noindex, follow
    const robots = page.locator('meta[name="robots"]');
    await expect(robots).toHaveAttribute('content', /noindex/);
    await expect(robots).toHaveAttribute('content', /follow/);

    // Canonical points away from archive (not articles.firstaimovers.com)
    const canonical = page.locator('link[rel="canonical"]');
    const canonicalHref = await canonical.getAttribute('href');
    expect(canonicalHref).toBeTruthy();
    expect(canonicalHref).not.toMatch(/articles\.firstaimovers\.com/);

    // Breadcrumb
    const breadcrumb = page.getByRole('navigation', { name: 'Breadcrumb' });
    await expect(breadcrumb).toBeVisible();
    await expect(breadcrumb).toContainText('Home');

    // Article heading matches link text
    const h1 = page.getByRole('heading', { level: 1 });
    await expect(h1).toContainText(articleTitle.trim());

    // Reading time chip
    const meta = page.locator('.article-header .meta');
    await expect(meta).toContainText(/min read/);

    // Related articles section
    const related = page.locator('.related-articles');
    await expect(related).toBeVisible();

    // Explore-all topic link
    const exploreLink = page.locator('.explore-topic a');
    await expect(exploreLink).toBeVisible();
    await expect(exploreLink).toContainText(/Explore all/);
  });

  test('article with TOC has working TOC links', async ({ page }) => {
    // Navigate to a topic known to have articles with TOC
    await page.goto('/topics/ai-strategy/');
    const firstArticleLink = page.locator('article h3 a').first();
    await firstArticleLink.click();
    await page.waitForURL(/\/articles\//);

    const toc = page.locator('nav.toc');
    if (await toc.isVisible().catch(() => false)) {
      const tocLinks = toc.locator('a');
      await expect(tocLinks.first()).toBeVisible();

      // Verify at least one TOC link targets an in-page anchor
      const href = await tocLinks.first().getAttribute('href');
      expect(href).toMatch(/^#/);
    } else {
      // If no TOC, the test is still valid — just note it
      test.info().annotations.push({ type: 'info', description: 'Article has no TOC (fewer than 2 headings)' });
    }
  });
});
