// APEX Team API client types and fetch helpers

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:7000";
export const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:7000/ws/updates";

// ---- Data types ----

export interface Agent {
  name: string;
  role: string;
  status: "idle" | "busy" | "online" | "offline";
  joined_at?: string;
  last_seen?: number;
}

export interface Task {
  id: number;
  title: string;
  assignee: string;
  status: "todo" | "in_progress" | "blocked" | "done";
  priority: "high" | "medium" | "low";
  depends_on: number[];
  parent_id: number;
  created_by?: string;
  updated?: string;
  git?: { branch?: string; commits?: Array<{ ref: string; time: string }> };
}

export interface Message {
  from: string;
  text: string;
  time: string;
  mention?: string;
}

export interface Metrics {
  agents_total: number;
  agents_online: number;
  messages: number;
  tasks_total: number;
  tasks_done: number;
  tasks_in_progress: number;
  tasks_todo: number;
  tasks_blocked: number;
  notes: number;
  decisions: number;
  active_debate: boolean;
}

export interface TeamState {
  metrics: Metrics;
  agents: Record<string, Agent>;
  tasks: Task[];
  messages: Message[];
  debate: unknown;
  timeline: Array<{ time: string; who: string; action: string }>;
  facts: Record<string, string>;
  findings: unknown[];
}

// ---- REST helpers ----

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getState: () => apiFetch<TeamState>("/api/state"),
  getAgents: () => apiFetch<Record<string, Agent>>("/api/agents"),
  getTasks: () => apiFetch<Task[]>("/api/tasks"),
  getMessages: (since = 0) =>
    apiFetch<{ messages: Message[]; next_index: number }>(`/api/messages?since=${since}`),
  getMetrics: () => apiFetch<Metrics>("/api/metrics"),

  addTask: (body: { title: string; assignee?: string; priority?: string; depends_on?: string }) =>
    apiFetch<{ message: string }>("/api/tasks", { method: "POST", body: JSON.stringify(body) }),

  updateTask: (id: number, body: { status?: string; assignee?: string; note?: string; by_role?: string }) =>
    apiFetch<{ message: string }>(`/api/tasks/${id}`, { method: "PATCH", body: JSON.stringify(body) }),

  postMessage: (body: { sender_role: string; text: string; mention?: string }) =>
    apiFetch<{ message: string }>("/api/messages", { method: "POST", body: JSON.stringify(body) }),

  joinTeam: (body: { role: string; name?: string }) =>
    apiFetch<{ message: string }>("/api/agents/join", { method: "POST", body: JSON.stringify(body) }),

  setStatus: (role: string, status: string) =>
    apiFetch<{ message: string }>(`/api/agents/${encodeURIComponent(role)}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),

  setFact: (body: { key: string; value: string; by_role?: string }) =>
    apiFetch<{ message: string }>("/api/facts", { method: "POST", body: JSON.stringify(body) }),

  recover: () =>
    apiFetch<{ message: string }>("/api/recovery", { method: "POST", body: JSON.stringify({}) }),
};
