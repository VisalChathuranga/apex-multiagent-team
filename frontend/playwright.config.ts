import { defineConfig, devices } from "@playwright/test";

/**
 * E2E tests for the APEX Team dashboard.
 *
 * Assumptions:
 *   - Next.js dev server runs on http://localhost:3000
 *   - api_server.py (FastAPI) runs on http://localhost:7000
 *     Start with: uvicorn api_server:app --port 7000
 *       (from D:\apex-team)
 */
export default defineConfig({
  testDir: "./e2e",
  globalSetup: "./e2e/global-setup.ts",
  timeout: 30_000,
  expect: { timeout: 8_000 },
  fullyParallel: false,   // panels share WS state — safer sequential
  retries: process.env.CI ? 2 : 0,
  reporter: [["list"], ["html", { open: "never" }]],

  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    video: "on-first-retry",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
