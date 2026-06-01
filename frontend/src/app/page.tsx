"use client";

import { AgentPanel } from "@/components/AgentPanel";
import { TaskBoard } from "@/components/TaskBoard";
import { ChatPanel } from "@/components/ChatPanel";
import { ControlsPanel } from "@/components/ControlsPanel";
import { useTeamState } from "@/hooks/useTeamState";

export default function Home() {
  const state = useTeamState();

  if (!state) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground text-sm">
        Connecting to APEX Team…
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-background p-4 md:p-6">
      <h1 className="text-lg font-semibold mb-4">APEX Team Dashboard</h1>

      <div className="grid gap-4 md:grid-cols-3">
        {/* Left column: agents + controls */}
        <div className="space-y-4">
          <AgentPanel agents={state.agents} />
          <ControlsPanel />
        </div>

        {/* Middle: chat */}
        <ChatPanel messages={state.messages} />

        {/* Right: metrics summary (inline) */}
        <div className="rounded border bg-card p-4 text-sm space-y-1">
          <p className="font-semibold uppercase tracking-wide text-xs text-muted-foreground mb-2">
            Metrics
          </p>
          <p>Agents online: <span className="font-medium">{state.metrics.agents_online}</span></p>
          <p>Tasks total: <span className="font-medium">{state.metrics.tasks_total}</span></p>
          <p>Done: <span className="font-medium text-green-500">{state.metrics.tasks_done}</span></p>
          <p>In progress: <span className="font-medium text-amber-500">{state.metrics.tasks_in_progress}</span></p>
          <p>Messages: <span className="font-medium">{state.metrics.messages}</span></p>
        </div>
      </div>

      {/* Task board — full width */}
      <div className="mt-4">
        <TaskBoard tasks={state.tasks} />
      </div>
    </main>
  );
}
