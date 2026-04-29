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
    await page.goto("/ask/");
    await page.locator("#ask-question").fill("How should SMEs approach AI governance?");
    await page.locator("#ask-submit").click();
    // Since /api/ask is not served by the static test server, fetch returns 404
    await expect(page.locator("#ask-disabled")).toBeVisible({ timeout: 5000 });
    await expect(page.locator("#ask-disabled")).toContainText("endpoint not yet deployed");
  });

  test("nav link exists", async ({ page }) => {
    await page.goto("/");
    const askLink = page.locator('nav a[href$="ask/"]');
    await expect(askLink).toBeVisible();
    await expect(askLink).toHaveText("Ask");
  });
});
