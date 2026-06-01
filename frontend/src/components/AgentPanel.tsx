"use client";

import { Agent, Task } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const STATUS_COLOR: Record<string, string> = {
  idle: "bg-blue-500",
  busy: "bg-amber-500",
  online: "bg-green-500",
  offline: "bg-zinc-500",
};

const STATUS_LABEL: Record<string, string> = {
  idle: "Idle",
  busy: "Busy",
  online: "Online",
  offline: "Offline",
};

interface Props {
  agents: Record<string, Agent>;
  tasks?: Task[];
}

export function AgentPanel({ agents, tasks = [] }: Props) {
  const list = Object.values(agents);

  function currentTask(role: string) {
    const matches = tasks.filter((t) => t.assignee === role && t.status === "in_progress");
    return matches.length > 0 ? matches.reduce((a, b) => (b.id > a.id ? b : a)) : undefined;
  }

  return (
    <Card data-testid="agents-panel">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
          Agents
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {list.length === 0 && (
          <p className="text-sm text-muted-foreground">No agents online.</p>
        )}
        {list.map((a) => (
          <div
            key={a.role}
            data-testid={`agent-row-${a.role}`}
            className="flex items-start justify-between gap-2"
          >
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <span
                className={`h-2 w-2 rounded-full flex-shrink-0 ${STATUS_COLOR[a.status] ?? "bg-zinc-400"}`}
              />
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{a.name}</span>
                  <Badge variant="outline" className="text-xs px-1 py-0">
                    {a.role}
                  </Badge>
                </div>
                {currentTask(a.role) && (
                  <p className="text-xs text-muted-foreground truncate">
                    {currentTask(a.role)!.title}
                  </p>
                )}
              </div>
            </div>
            <span className="text-xs text-muted-foreground shrink-0" data-testid={`agent-status-${a.role}`}>
              {STATUS_LABEL[a.status] ?? a.status}
            </span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
