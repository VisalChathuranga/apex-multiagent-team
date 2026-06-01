import { request } from "@playwright/test";

/**
 * Playwright global setup: reset API state before the test suite runs.
 * This ensures each test run starts from a clean slate, avoiding message/task
 * accumulation from prior runs.
 *
 * Requires the FastAPI server to be running on port 7000.
 */
async function globalSetup() {
  try {
    const context = await request.newContext({ baseURL: "http://localhost:7000" });
    await context.post("/api/state/reset");
    await context.dispose();
  } catch {
    // Server not running yet — Playwright's webServer directive will start Next.js
    // but api_server must be started separately. Silently continue; tests will
    // show meaningful errors if the API is unreachable.
    console.warn("[global-setup] WARNING: could not reset API state (server not reachable). Run: uvicorn api_server:app --port 7000");
  }
}

export default globalSetup;
