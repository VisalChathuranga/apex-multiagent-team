/**
 * E2E — Agent Status panel
 *
 * Selectors expect the panel to use data-testid="agents-panel" and each row
 * to carry data-testid="agent-row-{ROLE}" (e.g. "agent-row-PM").
 * Adjust if Frontend used different testids.
 */

import { test, expect } from "@playwright/test";
import { API, seedAgent, waitForRefresh } from "./helpers";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
});

test.describe("Agent Status panel — display", () => {
  test("panel is visible on the dashboard", async ({ page }) => {
    const panel = page.getByTestId("agents-panel");
    await expect(panel).toBeVisible();
  });

  test("shows each active agent's role", async ({ page }) => {
    // Seed three agents via API
    await seedAgent("PM");
    await seedAgent("Backend");
    await seedAgent("QA");

    await waitForRefresh(page, async () => {
      await expect(page.getByTestId("agent-row-PM")).toBeVisible();
      await expect(page.getByTestId("agent-row-Backend")).toBeVisible();
      await expect(page.getByTestId("agent-row-QA")).toBeVisible();
    });
  });

  test("displays agent status badge", async ({ page }) => {
    await seedAgent("Frontend");

    // Set Frontend status to idle
    await fetch(`${API}/api/agents/Frontend/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "idle" }),
    });

    await waitForRefresh(page, async () => {
      const row = page.getByTestId("agent-row-Frontend");
      await expect(row).toBeVisible();
      // Badge text should reflect status
      await expect(row.getByText(/idle/i)).toBeVisible();
    });
  });

  test("updates live when an agent status changes via WebSocket", async ({ page }) => {
    await seedAgent("Backend");

    // Mark busy via API, expect the panel to update without refresh
    await fetch(`${API}/api/agents/Backend/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "busy" }),
    });

    await waitForRefresh(page, async () => {
      const row = page.getByTestId("agent-row-Backend");
      await expect(row.getByText(/busy/i)).toBeVisible();
    });
  });

  test("shows current task for busy agent", async ({ page }) => {
    await seedAgent("Backend");
    const TITLE = "Build REST layer (agent-panel-e2e)";
    await fetch(`${API}/api/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: TITLE, assignee: "Backend", created_by: "PM" }),
    });
    // Look up by unique title to avoid last-element race in parallel workers
    const tasks = await fetch(`${API}/api/tasks`).then((x: Response) => x.json());
    const t = tasks.find((x: { title: string }) => x.title === TITLE);
    if (!t) throw new Error(`Task "${TITLE}" not found`);
    await fetch(`${API}/api/tasks/${t.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "in_progress", by_role: "Backend" }),
    });

    await waitForRefresh(page, async () => {
      const row = page.getByTestId("agent-row-Backend");
      await expect(row.getByText(TITLE)).toBeVisible();
    });
  });
});
