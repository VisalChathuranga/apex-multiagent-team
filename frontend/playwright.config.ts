import { defineConfig, devices } from "@playwright/test";
import { join } from "path";

/**
 * E2E tests for the APEX Team dashboard.
 *
 * Playwright automatically starts two servers:
 *   - Test API on :7001 (TEAM_STATE_FILE=e2e_test_state.json, isolated from live board)
 *   - Next.js on :3001 pointing at the test API
 *
 * The globalSetup writes a clean e2e_test_state.json before each suite run.
 * The live APEX board on :7000 / :3000 is never touched.
 */
const E2E_API_PORT = 7001;
const E2E_NEXT_PORT = 3001;

export default defineConfig({
  testDir: "./e2e",
  globalSetup: "./e2e/global-setup.ts",
  timeout: 30_000,
  expect: { timeout: 8_000 },
  fullyParallel: false,
  retries: process.env.CI ? 2 : 0,
  reporter: [["list"], ["html", { open: "never" }]],

  use: {
    baseURL: `http://localhost:${E2E_NEXT_PORT}`,
    trace: "on-first-retry",
    video: "on-first-retry",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  webServer: [
    {
      command: `uvicorn api_server:app --port ${E2E_API_PORT} --log-level warning`,
      url: `http://localhost:${E2E_API_PORT}/api/state`,
      env: { TEAM_STATE_FILE: "./e2e_test_state.json" },
      cwd: join(__dirname, ".."),
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command: `npx next dev -p ${E2E_NEXT_PORT}`,
      url: `http://localhost:${E2E_NEXT_PORT}`,
      env: {
        NEXT_PUBLIC_API_URL: `http://localhost:${E2E_API_PORT}`,
        NEXT_PUBLIC_WS_URL: `ws://localhost:${E2E_API_PORT}/ws/updates`,
      },
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
});
