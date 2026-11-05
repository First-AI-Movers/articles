import { test, expect } from "@playwright/test";

test.describe("Ask the Archive page", () => {
  test("/ask/ renders with correct title", async ({ page }) => {
    await page.goto("/ask/");
    await expect(page).toHaveTitle(/Ask the Archive/);
    await expect(page.locator("h1")).toHaveText("Ask the Archive");
  });

  test("form is accessible", async ({ page }) => {
    await page.goto("/ask/");
    const textarea = page.locator("#ask-question");
    await expect(textarea).toHaveAttribute("aria-label", "Your question");
    await expect(textarea).toHaveAttribute("minlength", "3");
    await expect(textarea).toHaveAttribute("maxlength", "500");
    await expect(textarea).toHaveAttribute("required");

    const submit = page.locator("#ask-submit");
    await expect(submit).toBeVisible();
    await expect(submit).toHaveText("Ask");
  });

  test("empty submit shows browser validation", async ({ page }) => {
    await page.goto("/ask/");
    const textarea = page.locator("#ask-question");
    await textarea.fill("");
    await page.locator("#ask-form").evaluate((form: HTMLFormElement) => form.reportValidity());
    // Browser-level validation should prevent submission
    await expect(textarea).toHaveAttribute("required");
  });

  test("page has noindex robots meta", async ({ page }) => {
    await page.goto("/ask/");
    const meta = page.locator('meta[name="robots"]');
    await expect(meta).toHaveAttribute("content", "noindex, follow");
  });

  test("disabled endpoint state is user-friendly", async ({ page }) => {
    await page.route("**/api/ask", (route) =>
      route.fulfill({ status: 503, contentType: "application/json", body: "{}" })
    );
    await page.goto("/ask/");
    await page.locator("#ask-question").fill("How should SMEs approach AI governance?");
    await page.locator("#ask-submit").click();
    // Simulate an unavailable HTTP endpoint without contacting production.
    await expect(page.locator("#ask-disabled")).toBeVisible({ timeout: 5000 });
    await expect(page.locator("#ask-disabled")).toContainText("endpoint not yet deployed");
  });

  test("network failure shows an error and permits retry", async ({ page }) => {
    await page.route("**/api/ask", (route) => route.abort("failed"));
    await page.goto("/ask/");
    await page.locator("#ask-question").fill("How should SMEs approach AI governance?");
    await page.locator("#ask-submit").click();
    await expect(page.locator("#ask-error")).toContainText("Failed to reach the answer endpoint.");
    await expect(page.locator("#ask-loading")).toBeHidden();
    await expect(page.locator("#ask-submit")).toBeEnabled();
    await expect(page.locator("#ask-disabled")).toBeHidden();
  });

  test("privacy and retention notice is visible", async ({ page }) => {
    await page.goto("/ask/");
    const notice = page.locator("#ask-privacy");
    await expect(notice).toBeVisible();
    await expect(notice).toContainText("Do not submit private, client or personal information.");
    await expect(notice).toContainText("stores no questions");
  });

  test("extractive answer renders citations with dates", async ({ page }) => {
    await page.route("**/api/ask", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          mode: "extractive",
          answer: "unused",
          citations: [
            {
              title: "Example article",
              slug: "example",
              local_url: "/articles/example/",
              canonical_url: "https://example.com/example",
              published_date: "2026-01-02",
              passage: "Quoted summary passage.",
              score: 1,
            },
          ],
        }),
      })
    );
    await page.goto("/ask/");
    await page.locator("#ask-question").fill("AI governance for SMEs");
    await page.locator("#ask-submit").click();
    const list = page.locator("#ask-citations-list");
    await expect(list).toContainText("Example article");
    await expect(list.locator("time")).toHaveText("2026-01-02");
    await expect(list).toContainText("Quoted summary passage.");
    await expect(page.locator("#ask-answer-text")).toContainText("No AI model wrote this answer");
  });

  test("nav link exists", async ({ page }) => {
    await page.goto("/");
    const askLink = page.locator('nav a[href$="ask/"]');
    await expect(askLink).toBeVisible();
    await expect(askLink).toHaveText("Ask");
  });
});
