import { test, expect } from "@playwright/test";

/** Answer the six scored questions with one option value each. */
async function answer(page, values: Record<string, string>) {
  for (const [name, value] of Object.entries(values)) {
    await page.locator(`input[name="${name}"][value="${value}"]`).check();
  }
}

const ALL_CLEAR = {
  q1: "useful",
  q2: "measured",
  q3: "none_dominates",
  q4: "clean",
  q5: "owned",
  q6: "reference",
};

test.describe("Seven-question workflow assessment", () => {
  test("/assess/ renders with heading and link to the source article", async ({ page }) => {
    await page.goto("/assess/");
    await expect(page).toHaveTitle(/Workflow Automation Assessment/);
    await expect(page.locator("h1")).toHaveText("Workflow Automation Assessment");
    await expect(
      page.locator('a[href*="before-you-automate-a-workflow-7-questions"]')
    ).toBeVisible();
  });

  test("all seven questions are present", async ({ page }) => {
    await page.goto("/assess/");
    await expect(page.locator("fieldset.assess-q")).toHaveCount(7);
  });

  test("a fully clear workflow yields BUILD", async ({ page }) => {
    await page.goto("/assess/");
    await answer(page, ALL_CLEAR);
    await page.locator("#assess-submit").click();
    await expect(page.locator("#assess-verdict")).toHaveText("BUILD");
    await expect(page.locator("#assess-reasons li")).not.toHaveCount(0);
  });

  test("an unmeasurable workflow yields REPAIR_FIRST and says why", async ({ page }) => {
    await page.goto("/assess/");
    await answer(page, { ...ALL_CLEAR, q2: "unmeasured" });
    await page.locator("#assess-submit").click();
    await expect(page.locator("#assess-verdict")).toHaveText("REPAIR_FIRST");
    await expect(page.locator("#assess-reasons")).toContainText("cannot be measured");
  });

  test("a non-AI alternative that removes the need yields STOP", async ({ page }) => {
    await page.goto("/assess/");
    await answer(page, { ...ALL_CLEAR, q3: "dominates" });
    await page.locator("#assess-submit").click();
    await expect(page.locator("#assess-verdict")).toHaveText("STOP");
  });

  test("a changing dependency yields DEFER", async ({ page }) => {
    await page.goto("/assess/");
    await answer(page, { ...ALL_CLEAR, q4: "changing" });
    await page.locator("#assess-submit").click();
    await expect(page.locator("#assess-verdict")).toHaveText("DEFER");
  });

  test("STOP takes precedence over REPAIR_FIRST", async ({ page }) => {
    await page.goto("/assess/");
    await answer(page, { ...ALL_CLEAR, q1: "not_useful", q2: "unmeasured" });
    await page.locator("#assess-submit").click();
    await expect(page.locator("#assess-verdict")).toHaveText("STOP");
  });

  test("an incomplete form abstains instead of guessing", async ({ page }) => {
    await page.goto("/assess/");
    await answer(page, { q1: "useful", q2: "measured" });
    await page.locator("#assess-submit").click();
    await expect(page.locator("#assess-verdict")).toHaveText("INSUFFICIENT_EVIDENCE");
    await expect(page.locator("#assess-reasons")).toContainText("question 3");
  });

  test("the recommendation is labelled provisional", async ({ page }) => {
    await page.goto("/assess/");
    await answer(page, ALL_CLEAR);
    await page.locator("#assess-submit").click();
    await expect(page.locator(".assess-provisional")).toContainText("provisional");
  });

  test("the record downloads locally and contains the verdict and answers", async ({ page }) => {
    await page.goto("/assess/");
    await answer(page, { ...ALL_CLEAR, q2: "unmeasured" });
    await page.locator("#e1").fill("An approved supplier invoice, consumed by finance.");
    await page.locator("#assess-submit").click();

    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.locator("#assess-download").click(),
    ]);
    expect(download.suggestedFilename()).toMatch(/^workflow-assessment-\d{4}-\d{2}-\d{2}\.md$/);

    const stream = await download.createReadStream();
    const chunks: Buffer[] = [];
    for await (const chunk of stream) chunks.push(Buffer.from(chunk));
    const body = Buffer.concat(chunks).toString("utf-8");

    expect(body).toContain("REPAIR_FIRST");
    expect(body).toContain("An approved supplier invoice, consumed by finance.");
    expect(body).toContain("What is the decision today?");
    expect(body).toContain("Verdict of record");
  });

  test("clearing the answers hides the recommendation", async ({ page }) => {
    await page.goto("/assess/");
    await answer(page, ALL_CLEAR);
    await page.locator("#assess-submit").click();
    await expect(page.locator("#assess-result")).toBeVisible();
    await page.locator("#assess-reset").click();
    await expect(page.locator("#assess-result")).toBeHidden();
  });

  test("the page issues no network request while being used", async ({ page }) => {
    const external: string[] = [];
    page.on("request", (req) => {
      const url = req.url();
      if (!url.startsWith("http://localhost") && !url.startsWith("http://127.0.0.1") && !url.startsWith("blob:") && !url.startsWith("data:")) {
        external.push(url);
      }
    });
    await page.goto("/assess/");
    await answer(page, ALL_CLEAR);
    await page.locator("#assess-submit").click();
    await expect(page.locator("#assess-verdict")).toHaveText("BUILD");
    // The analytics beacon in base.html.j2 is the site's, not the assessment's;
    // allow it explicitly and fail on anything else leaving the page.
    const unexpected = external.filter((u) => !u.includes("goatcounter") && !u.includes("gc.zgo.at"));
    expect(unexpected).toEqual([]);
  });
});
