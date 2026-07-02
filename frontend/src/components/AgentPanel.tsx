"use client";

import { Agent, Task } from "@/lib/api";
import { Users } from "lucide-react";

/* Role → colour palette */
const ROLE_BADGE: Record<string, string> = {
  pm:                "bg-violet-500/20  text-violet-300  border-violet-500/30",
  backend:           "bg-cyan-500/20    text-cyan-300    border-cyan-500/30",
  frontend:          "bg-blue-500/20    text-blue-300    border-blue-500/30",
  architect:         "bg-purple-500/20  text-purple-300  border-purple-500/30",
  analyst:           "bg-indigo-500/20  text-indigo-300  border-indigo-500/30",
  dba:               "bg-orange-500/20  text-orange-300  border-orange-500/30",
  "ai-integrator":   "bg-teal-500/20    text-teal-300    border-teal-500/30",
  tester:            "bg-green-500/20   text-green-300   border-green-500/30",
  qa:                "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  reviewer:          "bg-sky-500/20     text-sky-300     border-sky-500/30",
  "perf-tuner":      "bg-yellow-500/20  text-yellow-300  border-yellow-500/30",
  "security-auditor":"bg-red-500/20     text-red-300     border-red-500/30",
  "pen-tester":      "bg-rose-500/20    text-rose-300    border-rose-500/30",
  "dfir-analyst":    "bg-pink-500/20    text-pink-300    border-pink-500/30",
  writer:            "bg-amber-500/20   text-amber-300   border-amber-500/30",
  devops:            "bg-lime-500/20    text-lime-300    border-lime-500/30",
};

const DEFAULT_COLORS = [
  "bg-violet-500/20  text-violet-300  border-violet-500/30",
  "bg-cyan-500/20    text-cyan-300    border-cyan-500/30",
  "bg-blue-500/20    text-blue-300    border-blue-500/30",
  "bg-purple-500/20  text-purple-300  border-purple-500/30",
  "bg-indigo-500/20  text-indigo-300  border-indigo-500/30",
  "bg-orange-500/20  text-orange-300  border-orange-500/30",
  "bg-teal-500/20    text-teal-300    border-teal-500/30",
  "bg-green-500/20   text-green-300   border-green-500/30",
  "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  "bg-sky-500/20     text-sky-300     border-sky-500/30",
  "bg-yellow-500/20  text-yellow-300  border-yellow-500/30",
  "bg-red-500/20     text-red-300     border-red-500/30",
  "bg-rose-500/20    text-rose-300    border-rose-500/30",
  "bg-pink-500/20    text-pink-300    border-pink-500/30",
  "bg-amber-500/20   text-amber-300   border-amber-500/30",
  "bg-lime-500/20    text-lime-300    border-lime-500/30",
];

function getBadgeColor(role: string) {
  if (ROLE_BADGE[role]) return ROLE_BADGE[role];
  let hash = 0;
  for (let i = 0; i < role.length; i++) {
    hash = role.charCodeAt(i) + ((hash << 5) - hash);
  }
  return DEFAULT_COLORS[Math.abs(hash) % DEFAULT_COLORS.length];
}

const STATUS_DOT: Record<string, string> = {
  busy:    "bg-amber-400 animate-status-pulse",
  idle:    "bg-blue-400/70",
  online:  "bg-emerald-400",
  offline: "bg-zinc-600",
};

const STATUS_TEXT: Record<string, string> = {
  idle:    "text-blue-400/80",
  busy:    "text-amber-400",
  online:  "text-emerald-400",
  offline: "text-zinc-500",
};

const STATUS_LABEL: Record<string, string> = {
  idle: "Idle", busy: "Busy", online: "Online", offline: "Offline",
};

interface Props {
  agents: Record<string, Agent>;
  tasks?: Task[];
}

export function AgentPanel({ agents, tasks = [] }: Props) {
  const list        = Object.values(agents);
  const onlineCount = list.filter(a => a.status !== "offline").length;

  function currentTask(role: string) {
    const active = tasks.filter(t => t.assignee === role && t.status === "in_progress");
    return active.length ? active.reduce((a, b) => (b.id > a.id ? b : a)) : undefined;
  }

  return (
    <div data-testid="agents-panel" className="rounded-xl border border-border/60 bg-card overflow-hidden">

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/50 bg-white/[0.02]">
        <div className="flex items-center gap-2">
          <Users className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Agents</span>
        </div>
        {list.length > 0 && (
          <div className="flex items-center gap-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            <span className="text-[11px] font-semibold text-emerald-400 tabular-nums">
              {onlineCount}/{list.length}
            </span>
          </div>
        )}
      </div>

      {/* List */}
      <div className="p-2.5 space-y-1.5">
        {list.length === 0 && (
          <p className="py-8 text-center text-sm text-muted-foreground/60">No agents online.</p>
        )}

        {list.map(a => {
          const rk      = a.role.toLowerCase().replace(/\s+/g, "-");
          const badge   = getBadgeColor(rk);
          const task    = currentTask(a.role);

          return (
            <div
              key={a.role}
              data-testid={`agent-row-${a.role}`}
              className="flex items-start justify-between gap-2 rounded-lg border border-border/40 bg-background/30 px-3 py-2.5 hover:border-border/70 hover:bg-background/50 transition-colors"
            >
              {/* Left: dot + name + badge + task */}
              <div className="flex items-start gap-2.5 flex-1 min-w-0">
                <span className={`mt-1 h-2 w-2 shrink-0 rounded-full ${STATUS_DOT[a.status] ?? "bg-zinc-500"}`} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-sm font-semibold text-foreground leading-none">{a.name}</span>
                    <span className={`inline-flex rounded border px-1.5 py-0.5 text-[10px] font-semibold leading-none ${badge}`}>
                      {a.role}
                    </span>
                  </div>
                  {task && (
                    <p className="mt-1 truncate text-xs text-muted-foreground/70 leading-snug">
                      ↳ {task.title}
                    </p>
                  )}
                </div>
              </div>

              {/* Right: status label */}
              <span
                data-testid={`agent-status-${a.role}`}
                className={`shrink-0 text-xs font-medium mt-0.5 ${STATUS_TEXT[a.status] ?? "text-muted-foreground"}`}
              >
                {STATUS_LABEL[a.status] ?? a.status}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
