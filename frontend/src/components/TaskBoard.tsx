"use client";

import { Task } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

const COLS: { key: Task["status"]; label: string }[] = [
  { key: "todo", label: "To Do" },
  { key: "in_progress", label: "In Progress" },
  { key: "blocked", label: "Blocked" },
  { key: "done", label: "Done" },
];

const PRIORITY_VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  high: "destructive",
  medium: "secondary",
  low: "outline",
};

const STATUS_BG: Record<string, string> = {
  todo: "border-l-zinc-400",
  in_progress: "border-l-amber-400",
  blocked: "border-l-red-500",
  done: "border-l-green-500",
};

interface Props {
  tasks: Task[];
}

function TaskCard({ task }: { task: Task }) {
  return (
    <div
      data-testid={`task-card-${task.id}`}
      className={`rounded border border-l-4 bg-card p-2 text-sm space-y-1 ${STATUS_BG[task.status] ?? ""}`}
    >
      <div className="flex items-start justify-between gap-1">
        <span className="font-medium leading-snug">
          <span className="text-muted-foreground mr-1">#{task.id}</span>
          {task.title}
        </span>
        <Badge variant={PRIORITY_VARIANT[task.priority] ?? "outline"} className="text-xs shrink-0">
          {task.priority}
        </Badge>
      </div>
      {task.assignee && (
        <p className="text-xs text-muted-foreground">@{task.assignee}</p>
      )}
      {task.depends_on?.length > 0 && (
        <p className="text-xs text-muted-foreground">
          deps: {task.depends_on.map((d) => `#${d}`).join(", ")}
        </p>
      )}
    </div>
  );
}

export function TaskBoard({ tasks }: Props) {
  const tops = tasks.filter((t) => !t.parent_id);

  return (
    <Card className="col-span-full" data-testid="task-board">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
          Task Board
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {COLS.map((col) => {
            const colTasks = tops
              .filter((t) => t.status === col.key)
              .sort((a, b) => {
                const p = { high: 0, medium: 1, low: 2 };
                return (p[a.priority] ?? 1) - (p[b.priority] ?? 1) || a.id - b.id;
              });
            return (
              <div key={col.key} data-testid={`column-${col.key}`}>
                <p className="mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                  {col.label}{" "}
                  <span className="font-normal">({colTasks.length})</span>
                </p>
                <ScrollArea className="h-64">
                  <div className="space-y-2 pr-2">
                    {colTasks.length === 0 && (
                      <p className="text-xs text-muted-foreground">—</p>
                    )}
                    {colTasks.map((t) => (
                      <TaskCard key={t.id} task={t} />
                    ))}
                  </div>
                </ScrollArea>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
