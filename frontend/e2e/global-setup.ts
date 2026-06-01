import { writeFileSync } from "fs";
import { join } from "path";

/**
 * Playwright global setup: write a fresh empty state file for the E2E test
 * server (port 7001, separate from the production server on port 7000).
 *
 * The E2E server is started via playwright.config.ts webServer and uses
 * TEAM_STATE_FILE=./e2e_test_state.json so it never touches shared_state.json.
 */
const EMPTY_STATE = {
  agents: {},
  messages: [],
  tasks: [],
  notes: [],
  facts: {},
  summaries: [],
  activity_log: [],
  findings: [],
  debate: null,
  _write_count: 0,
};

async function globalSetup() {
  const stateFile = join(process.cwd(), "..", "e2e_test_state.json");
  writeFileSync(stateFile, JSON.stringify(EMPTY_STATE, null, 2), "utf-8");
  console.log("[global-setup] Wrote clean test state to", stateFile);
}

export default globalSetup;
