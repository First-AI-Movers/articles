import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E configuration for the First AI Movers Article Archive.
 *
 * Prerequisites:
 *   python3 tools/rebuild_local.py   # builds site/ directory
 *   npx playwright install chromium  # install browser binary
 *
 * Run:
 *   npm run test:e2e
 *   npm run test:e2e:report          # open HTML report
 */
export default defineConfig({
  testDir: './tests-e2e/specs',

  /* Run tests in files in parallel */
  fullyParallel: true,

  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,

  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,

  /* Opt out of parallel tests on CI for stability */
  workers: process.env.CI ? 1 : undefined,

  /* Reporter to use */
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['line'],
  ],

  /* Shared settings for all the projects below */
  use: {
    /* Base URL to use in actions like `await page.goto('/')` */
    baseURL: 'http://127.0.0.1:4173',

    /* Collect trace when retrying the failed test */
    trace: 'retain-on-failure',

    /* Screenshot on failure only */
    screenshot: 'only-on-failure',

    /* No video by default (traces + screenshots are enough) */
    video: 'off',

    /* Browser */
    ...devices['Desktop Chrome'],
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  /* Run local static server before starting the tests */
  webServer: {
    command: 'python3 -m http.server 4173 --directory site',
    url: 'http://127.0.0.1:4173',
    reuseExistingServer: !process.env.CI,
    stdout: 'pipe',
    stderr: 'pipe',
  },
});
