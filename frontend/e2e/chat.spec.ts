/**
 * E2E — Team Chat panel
 *
 * Selectors expect:
 *   data-testid="chat-panel"            — the chat container
 *   data-testid="chat-messages"         — scrollable message feed
 *   data-testid="chat-message-{index}"  — individual message row
 *   data-testid="chat-input"            — message text input
 *   data-testid="chat-send"             — send button
 */

import { test, expect } from "@playwright/test";
import { seedAgent, seedMessage, waitForRefresh } from "./helpers";

const API = "http://localhost:7000";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
});

test.describe("Chat panel — display", () => {
  test("chat panel is visible", async ({ page }) => {
    await expect(page.getByTestId("chat-panel")).toBeVisible();
  });

  test("existing messages appear on load", async ({ page }) => {
    await seedAgent("PM");
    await seedMessage("PM", "Hello team");

    await waitForRefresh(page, async () => {
      const feed = page.getByTestId("chat-messages");
      await expect(feed.getByText("Hello team")).toBeVisible();
    });
  });

  test("messages show sender role", async ({ page }) => {
    await seedAgent("Backend");
    await seedMessage("Backend", "API layer done");

    await waitForRefresh(page, async () => {
      const feed = page.getByTestId("chat-messages");
      await expect(feed.getByText("Backend")).toBeVisible();
      await expect(feed.getByText("API layer done")).toBeVisible();
    });
  });

  test("@mention is highlighted", async ({ page }) => {
    await seedAgent("QA");
    await seedMessage("QA", "@PM tests green", "PM");

    await waitForRefresh(page, async () => {
      // ChatPanel wraps @mentions in <span class="font-semibold text-amber-400">
      const feed = page.getByTestId("chat-messages");
      const mention = feed.locator("span.text-amber-400").filter({ hasText: "@PM" });
      await expect(mention.first()).toBeVisible();
    });
  });

  test("new message arrives via WebSocket without page reload", async ({ page }) => {
    // Verify the feed is already showing, then post a message externally
    await expect(page.getByTestId("chat-messages")).toBeVisible();

    await seedMessage("PM", "WS-delivered message");

    await waitForRefresh(page, async () => {
      await expect(
        page.getByTestId("chat-messages").getByText("WS-delivered message")
      ).toBeVisible();
    });
  });
});

test.describe("Chat panel — sending messages", () => {
  test("user can type and send a message via controls", async ({ page }) => {
    await seedAgent("QA");

    const input = page.getByTestId("chat-input");
    await input.fill("E2E test message");
    await page.getByTestId("chat-send").click();

    await waitForRefresh(page, async () => {
      await expect(
        page.getByTestId("chat-messages").getByText("E2E test message")
      ).toBeVisible();
    });
  });

  test("input clears after sending", async ({ page }) => {
    await seedAgent("QA");
    const input = page.getByTestId("chat-input");
    await input.fill("Clear me");
    await page.getByTestId("chat-send").click();
    await expect(input).toHaveValue("");
  });

  test("send on Enter key works", async ({ page }) => {
    await seedAgent("QA");
    const input = page.getByTestId("chat-input");
    await input.fill("Sent via Enter");
    await input.press("Enter");

    await waitForRefresh(page, async () => {
      await expect(
        page.getByTestId("chat-messages").getByText("Sent via Enter")
      ).toBeVisible();
    });
  });

  test("empty message is not sent", async ({ page }) => {
    const beforeCount = await page.getByTestId("chat-messages").locator("[data-testid^='chat-message-']").count();
    await page.getByTestId("chat-send").click();
    const afterCount = await page.getByTestId("chat-messages").locator("[data-testid^='chat-message-']").count();
    expect(afterCount).toBe(beforeCount);
  });

  test("feed auto-scrolls to latest message", async ({ page }) => {
    // Post multiple messages to push scroll position down
    await seedAgent("PM");
    for (let i = 0; i < 5; i++) {
      await seedMessage("PM", `Scroll test message ${i}`);
    }
    await seedMessage("PM", "LAST_SCROLL_MSG");

    await waitForRefresh(page, async () => {
      const feed = page.getByTestId("chat-messages");
      const last = feed.getByText("LAST_SCROLL_MSG");
      await expect(last).toBeInViewport();
    });
  });
});
