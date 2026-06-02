"use client";

import { Task }       from "@/lib/api";
import { ScrollArea } from "@/components/ui/scroll-area";
import { LayoutGrid } from "lucide-react";

/* ── Column definitions ─────────────────────────────────────── */
const COLS: {
  key: Task["status"];
  label: string;
  header: string;
  dot: string;
  cardBorder: string;
}[] = [
  {
    key: "todo",
    label: "To Do",
    header:     "text-slate-300  bg-slate-500/8   border-slate-500/20",
    dot:        "bg-slate-400",
    cardBorder: "border-l-slate-500/50",
  },
  {
    key: "in_progress",
    label: "In Progress",
    header:     "text-amber-300  bg-amber-500/8   border-amber-500/20",
    dot:        "bg-amber-400 animate-pulse",
    cardBorder: "border-l-amber-500/70",
  },
  {
    key: "blocked",
    label: "Blocked",
    header:     "text-red-300    bg-red-500/8     border-red-500/20",
    dot:        "bg-red-400",
    cardBorder: "border-l-red-500/70",
  },
  {
    key: "done",
    label: "Done",
    header:     "text-emerald-300 bg-emerald-500/8 border-emerald-500/20",
    dot:        "bg-emerald-400",
    cardBorder: "border-l-emerald-500/70",
  },
];

/* ── Priority badge styles ──────────────────────────────────── */
const PRIORITY: Record<string, string> = {
  high:   "bg-red-500/12    text-red-400    border-red-500/30",
  medium: "bg-amber-500/12  text-amber-400  border-amber-500/30",
  low:    "bg-slate-500/12  text-slate-400  border-slate-500/30",
};

/* ── Task card ──────────────────────────────────────────────── */
function TaskCard({ task, borderClass }: { task: Task; borderClass: string }) {
  return (
    <div
      data-testid={`task-card-${task.id}`}
      className={`rounded-lg border border-border/40 border-l-2 ${borderClass} bg-background/40 px-3 py-2.5 space-y-1.5 hover:bg-background/70 hover:border-border/70 transition-colors group`}
    >
      {/* Title row */}
      <div className="flex items-start justify-between gap-2">
        <span className="text-sm font-medium text-foreground leading-snug flex-1 min-w-0">
          <span className="text-muted-foreground/50 text-[10px] font-normal mr-1">#{task.id}</span>
          {task.title}
        </span>
        <span
          className={`shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-semibold leading-none ${
            PRIORITY[task.priority] ?? PRIORITY.medium
          }`}
        >
          {task.priority}
        </span>
      </div>

      {/* Assignee */}
      {task.assignee && (
        <p className="text-xs font-medium text-cyan-400/80">@{task.assignee}</p>
      )}

      {/* Dependencies */}
      {task.depends_on?.length > 0 && (
        <p className="text-[10px] text-muted-foreground/50">
          needs: {task.depends_on.map(d => `#${d}`).join(", ")}
        </p>
      )}
    </div>
  );
}

/* ── Board ──────────────────────────────────────────────────── */
interface Props { tasks: Task[] }

export function TaskBoard({ tasks }: Props) {
  const tops = tasks.filter(t => !t.parent_id);

  return (
    <div data-testid="task-board" className="rounded-xl border border-border/60 bg-card overflow-hidden">

      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border/50 bg-white/[0.02]">
        <LayoutGrid className="h-3.5 w-3.5 text-muted-foreground" />
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Task Board</span>
        <span className="ml-auto rounded-full bg-white/5 border border-border/40 px-2 py-0.5 text-[11px] text-muted-foreground tabular-nums">
          {tops.length} tasks
        </span>
      </div>

      {/* Kanban */}
      <div className="p-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {COLS.map(col => {
          const colTasks = tops
            .filter(t => t.status === col.key)
            .sort((a, b) => {
              const p = { high: 0, medium: 1, low: 2 } as Record<string, number>;
              return (p[a.priority] ?? 1) - (p[b.priority] ?? 1) || a.id - b.id;
            });

          return (
            <div key={col.key} data-testid={`column-${col.key.replace(/_/g, "-")}`}>
              {/* Column header */}
              <div className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 mb-3 ${col.header}`}>
                <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${col.dot}`} />
                <span className="flex-1 text-xs font-semibold">{col.label}</span>
                <span className="text-xs font-bold tabular-nums">{colTasks.length}</span>
              </div>

              <ScrollArea className="h-64">
                <div className="space-y-2 pr-1">
                  {colTasks.length === 0 && (
                    <p className="py-6 text-center text-xs text-muted-foreground/40">—</p>
                  )}
                  {colTasks.map(t => (
                    <TaskCard key={t.id} task={t} borderClass={col.cardBorder} />
                  ))}
                </div>
              </ScrollArea>
            </div>
          );
        })}
      </div>
    </div>
  );
}
