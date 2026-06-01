#!/usr/bin/env node
/**
 * Starts the FastAPI E2E test server on port 7001 using an isolated state file.
 * Playwright's globalSetup writes a clean e2e_test_state.json before this runs.
 * This process is managed by playwright.config.ts webServer — do not run manually.
 */
const { spawn } = require("child_process");
const path = require("path");

const backendDir = path.resolve(__dirname, "..", "..");
const stateFile = path.join(backendDir, "e2e_test_state.json");

const proc = spawn(
  "python",
  ["-m", "uvicorn", "api_server:app", "--host", "127.0.0.1", "--port", "7001"],
  {
    cwd: backendDir,
    env: { ...process.env, TEAM_STATE_FILE: stateFile },
    stdio: "inherit",
  }
);

proc.on("error", (err) => {
  console.error("[e2e-api] Failed to start:", err.message);
  process.exit(1);
});

process.on("SIGTERM", () => proc.kill("SIGTERM"));
process.on("SIGINT", () => proc.kill("SIGINT"));
