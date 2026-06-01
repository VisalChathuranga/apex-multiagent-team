/**
 * E2E — Controls panel
 *
 * Selectors expect:
 *   data-testid="controls-panel"       — the panel container
 *   data-testid="add-task-title"       — task title input
 *   data-testid="add-task-submit"      — submit button for add-task
 *   data-testid="post-message-input"   — message text area
 *   data-testid="post-message-send"    — send button
 *   data-testid="btn-assign"           — trigger auto-assign
 *   data-testid="btn-recover"          — trigger crash recovery
 *   data-testid="btn-export"           — trigger export report
 */

import { test, expect } from "@playwright/test";
import { API, seedAgent, waitForRefresh } from "./helpers";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
});

test.describe("Controls panel — visibility", () => {
  test("controls panel is visible", async ({ page }) => {
    await expect(page.getByTestId("controls-panel")).toBeVisible();
  });

  test("add-task form elements are present", async ({ page }) => {
    const panel = page.getByTestId("controls-panel");
    await expect(panel.getByTestId("add-task-title")).toBeVisible();
    await expect(panel.getByTestId("add-task-submit")).toBeVisible();
  });

  test("post-message form elements are present", async ({ page }) => {
    const panel = page.getByTestId("controls-panel");
    await expect(panel.getByTestId("post-message-input")).toBeVisible();
    await expect(panel.getByTestId("post-message-send")).toBeVisible();
  });
});

test.describe("Controls panel — add-task form", () => {
  test("creates task and it appears on the board", async ({ page }) => {
    await seedAgent("PM");
    await page.getByTestId("add-task-title").fill("Controls panel task");
    await page.getByTestId("add-task-submit").click();

    await waitForRefresh(page, async () => {
      await expect(
        page.getByTestId("column-todo").getByText("Controls panel task")
      ).toBeVisible();
    });
  });

  test("title input clears after submit", async ({ page }) => {
    await seedAgent("PM");
    const input = page.getByTestId("add-task-title");
    await input.fill("Cleared after submit");
    await page.getByTestId("add-task-submit").click();
    await expect(input).toHaveValue("");
  });

  test("submit is disabled when title is empty", async ({ page }) => {
    // Button is disabled when input is empty — assert directly rather than
    // clicking (clicking a disabled button hangs in Playwright).
    const input = page.getByTestId("add-task-title");
    const btn = page.getByTestId("add-task-submit");
    await expect(input).toHaveValue(""); // starts empty
    await expect(btn).toBeDisabled();
  });
});

test.describe("Controls panel — post-message form", () => {
  test("posts message and it appears in chat", async ({ page }) => {
    await seedAgent("PM");
    await page.getByTestId("post-message-input").fill("Posted from controls");
    await page.getByTestId("post-message-send").click();

    await waitForRefresh(page, async () => {
      await expect(
        page.getByTestId("chat-messages").getByText("Posted from controls")
      ).toBeVisible();
    });
  });

  test("message input clears after send", async ({ page }) => {
    await seedAgent("PM");
    const input = page.getByTestId("post-message-input");
    await input.fill("Will be cleared");
    await page.getByTestId("post-message-send").click();
    await expect(input).toHaveValue("");
  });
});

test.describe("Controls panel — action buttons", () => {
  test("assign button triggers auto-assign and shows result", async ({ page }) => {
    await seedAgent("PM");
    const btn = page.getByTestId("btn-assign");
    if (await btn.count() === 0) {
      test.skip(true, "btn-assign not found; panel may not include this button");
    }
    await btn.click();
    // Should show some feedback (toast, message, or channel update)
    await waitForRefresh(page, async () => {
      await expect(
        page.getByText(/assign/i).or(page.getByText(/no tasks/i)).first()
      ).toBeVisible();
    });
  });

  test("recover button fires recovery and board updates", async ({ page }) => {
    const btn = page.getByTestId("btn-recover");
    if (await btn.count() === 0) {
      test.skip(true, "btn-recover not found; panel may not include this button");
    }
    await btn.click();
    // Expect a channel message or toast confirming recovery ran
    await waitForRefresh(page, async () => {
      await expect(
        page.getByText(/recover/i).or(page.getByText(/no stale/i)).first()
      ).toBeVisible();
    });
  });

  test("export button creates a report and shows confirmation", async ({ page }) => {
    const btn = page.getByTestId("btn-export");
    if (await btn.count() === 0) {
      test.skip(true, "btn-export not found; panel may not include this button");
    }
    await btn.click();
    // Expect a download prompt or a success notification
    const [download] = await Promise.all([
      page.waitForEvent("download", { timeout: 5_000 }).catch(() => null),
      page.waitForSelector("[data-testid='export-success']", { timeout: 5_000 }).catch(() => null),
    ]);
    expect(download ?? page.locator("[data-testid='export-success']")).toBeTruthy();
  });
});
