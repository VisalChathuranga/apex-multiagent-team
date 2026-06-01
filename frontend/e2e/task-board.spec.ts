/**
 * E2E — Task Board (Kanban)
 *
 * Selectors expect:
 *   data-testid="task-board"            — the whole board
 *   data-testid="column-todo"           — todo column
 *   data-testid="column-in-progress"    — in-progress column
 *   data-testid="column-done"           — done column
 *   data-testid="task-card-{id}"        — individual card
 */

import { test, expect, Page } from "@playwright/test";
import { seedAgent, seedTask, waitForRefresh } from "./helpers";

const API = "http://localhost:7000";

async function getTaskId(title: string): Promise<number> {
  const tasks = await fetch(`${API}/api/tasks`).then((r) => r.json());
  const t = tasks.find((x: any) => x.title === title);
  if (!t) throw new Error(`task "${title}" not found`);
  return t.id;
}

test.beforeEach(async ({ page }) => {
  await page.goto("/");
});

test.describe("Task Board — columns", () => {
  test("board is visible", async ({ page }) => {
    await expect(page.getByTestId("task-board")).toBeVisible();
  });

  test("shows three Kanban columns", async ({ page }) => {
    const board = page.getByTestId("task-board");
    await expect(board.getByTestId("column-todo")).toBeVisible();
    await expect(board.getByTestId("column-in-progress")).toBeVisible();
    await expect(board.getByTestId("column-done")).toBeVisible();
  });
});

test.describe("Task Board — task cards", () => {
  test("new task appears in todo column via WebSocket feed", async ({ page }) => {
    await seedAgent("PM");
    await seedTask("Live-feed task", { created_by: "PM" });
    const tid = await getTaskId("Live-feed task");

    await waitForRefresh(page, async () => {
      const column = page.getByTestId("column-todo");
      await expect(column.getByTestId(`task-card-${tid}`)).toBeVisible();
    });
  });

  test("card moves to in-progress column when status changes", async ({ page }) => {
    await seedAgent("Backend");
    await seedTask("In-flight task", { assignee: "Backend" });
    const tid = await getTaskId("In-flight task");

    await fetch(`${API}/api/tasks/${tid}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "in_progress", by_role: "Backend" }),
    });

    await waitForRefresh(page, async () => {
      const col = page.getByTestId("column-in-progress");
      await expect(col.getByTestId(`task-card-${tid}`)).toBeVisible();
    });
  });

  test("card moves to done column when completed", async ({ page }) => {
    await seedAgent("PM");
    await seedTask("Done task");
    const tid = await getTaskId("Done task");

    await fetch(`${API}/api/tasks/${tid}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "done" }),
    });

    await waitForRefresh(page, async () => {
      const col = page.getByTestId("column-done");
      await expect(col.getByTestId(`task-card-${tid}`)).toBeVisible();
    });
  });

  test("priority badge is displayed on card", async ({ page }) => {
    await seedAgent("PM");
    await seedTask("High priority task", { priority: "high" });
    const tid = await getTaskId("High priority task");

    await waitForRefresh(page, async () => {
      const card = page.getByTestId(`task-card-${tid}`);
      await expect(card).toBeVisible();
      await expect(card.getByText(/high/i)).toBeVisible();
    });
  });

  test("assignee name shown on card", async ({ page }) => {
    await seedAgent("Frontend");
    await seedTask("Frontend task", { assignee: "Frontend" });
    const tid = await getTaskId("Frontend task");

    await waitForRefresh(page, async () => {
      const card = page.getByTestId(`task-card-${tid}`);
      await expect(card.getByText("Frontend")).toBeVisible();
    });
  });
});

test.describe("Task Board — full CRUD via controls", () => {
  test("add-task form creates a card on the board", async ({ page }) => {
    // This test requires the Controls panel to have an add-task form
    // Navigate and fill the form
    const addInput = page.getByTestId("add-task-title");
    await addInput.fill("E2E created task");
    await page.getByTestId("add-task-submit").click();

    await waitForRefresh(page, async () => {
      await expect(
        page.getByTestId("column-todo").getByText("E2E created task")
      ).toBeVisible();
    });
  });
});
