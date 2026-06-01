/**
 * Shared helpers and fixtures for APEX dashboard E2E tests.
 */

import { Page, expect } from "@playwright/test";

export const API = process.env.E2E_API_URL ?? "http://localhost:7001";

// ---------------------------------------------------------------------------
// API seed helpers — call via fetch in tests to set up known state
// ---------------------------------------------------------------------------

export async function seedAgent(role: string, name = role) {
  const r = await fetch(`${API}/api/agents/join`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role, name }),
  });
  if (!r.ok) throw new Error(`seedAgent ${role} failed: ${r.status}`);
}

export async function seedTask(title: string, opts: {
  assignee?: string;
  priority?: "low" | "medium" | "high";
  created_by?: string;
} = {}) {
  const r = await fetch(`${API}/api/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title,
      assignee: opts.assignee ?? "",
      priority: opts.priority ?? "medium",
      created_by: opts.created_by ?? "PM",
    }),
  });
  if (!r.ok) throw new Error(`seedTask failed: ${r.status}`);
}

export async function seedMessage(senderRole: string, text: string, mention = "") {
  const r = await fetch(`${API}/api/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sender_role: senderRole, text, mention }),
  });
  if (!r.ok) throw new Error(`seedMessage failed: ${r.status}`);
}

export async function patchTaskStatus(
  page: Page,
  taskId: number,
  status: string
) {
  await page.request.patch(`${API}/api/tasks/${taskId}`, {
    data: { status, by_role: "test" },
  });
}

// ---------------------------------------------------------------------------
// Wait helpers
// ---------------------------------------------------------------------------

/** Wait for the WS-fed UI to refresh (poll every 1 s, up to 10 s). */
export async function waitForRefresh(page: Page, check: () => Promise<void>) {
  await expect(async () => {
    await check();
  }).toPass({ timeout: 10_000, intervals: [1_000] });
}
