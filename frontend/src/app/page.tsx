"use client";

import { AgentPanel }   from "@/components/AgentPanel";
import { TaskBoard }    from "@/components/TaskBoard";
import { ChatPanel }    from "@/components/ChatPanel";
import { ControlsPanel } from "@/components/ControlsPanel";
import { LaunchWizard } from "@/components/LaunchWizard";
import { SpawnHealthPanel } from "@/components/SpawnHealthPanel";
import { TracesPanel } from "@/components/TracesPanel";
import { useTeamState } from "@/hooks/useTeamState";
import { Metrics, TeamState } from "@/types/api";

const EMPTY_STATE: TeamState = {
  metrics: {
    agents_total: 0, agents_online: 0, messages: 0,
    tasks_total: 0, tasks_done: 0, tasks_in_progress: 0,
    tasks_todo: 0, tasks_blocked: 0, notes: 0, decisions: 0,
    active_debate: false,
  },
  agents: {},
  tasks: [],
  messages: [],
  debate: null,
  timeline: [],
  facts: {},
  findings: [],
};

/* ── Header metric chip ─────────────────────────────────────── */
const CHIP: Record<string, string> = {
  green:  "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  amber:  "bg-amber-500/10   text-amber-400   border-amber-500/20",
  violet: "bg-violet-500/10  text-violet-400  border-violet-500/20",
  slate:  "bg-white/4        text-slate-400   border-white/8",
};

function MetricChip({
  label, value, color,
}: {
  label: string; value: number; color: keyof typeof CHIP;
}) {
  return (
    <div
      className={`hidden sm:flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${CHIP[color] ?? CHIP.slate}`}
    >
      {label}
      <span className="font-bold tabular-nums">{value}</span>
    </div>
  );
}

/* ── Loading screen ──────────────────────────────────────────── */
function LoadingScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center flex-col gap-4 bg-background">
      <div className="relative h-12 w-12">
        <div className="absolute inset-0 rounded-2xl bg-primary/30 blur-xl animate-pulse" />
        <div className="relative h-12 w-12 rounded-2xl bg-primary/20 border border-primary/40 flex items-center justify-center">
          <span className="text-primary font-bold text-xl">⬡</span>
        </div>
      </div>
      <p className="text-muted-foreground text-sm animate-pulse">Connecting to APEX Team…</p>
      <p className="text-muted-foreground/40 text-xs">API on :8561 · Dashboard on :8562</p>
    </div>
  );
}

/* ── Main page ───────────────────────────────────────────────── */
export default function Home() {
  const { state, ready } = useTeamState();
  if (!ready) return <LoadingScreen />;

  const connected = state !== null;
  const s = state ?? EMPTY_STATE;
  const m: Metrics = s.metrics;

  return (
    <div className="min-h-screen bg-background flex flex-col">

      {/* ── Sticky header ── */}
      <header className="sticky top-0 z-20 border-b border-border/50 bg-background/75 backdrop-blur-md">
        <div className="px-4 md:px-6 h-14 flex items-center gap-3">

          {/* Logo */}
          <div className="flex items-center gap-2.5 shrink-0 mr-2">
            <div className="relative h-7 w-7">
              <div className="absolute inset-0 rounded-lg bg-primary/50 blur-lg" />
              <div className="relative h-7 w-7 rounded-lg bg-primary/20 border border-primary/40 flex items-center justify-center">
                <span className="text-primary text-xs font-bold">⬡</span>
              </div>
            </div>
            <span className="text-sm font-bold tracking-tight">
              <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
                APEX
              </span>
              <span className="text-foreground/60 font-normal ml-1">Team</span>
            </span>
          </div>

          <div className="h-4 w-px bg-border/60" />

          {/* Connection dot */}
          <div className="flex items-center gap-1.5 shrink-0">
            <span className={`h-1.5 w-1.5 rounded-full ${connected ? "bg-emerald-400 animate-pulse" : "bg-slate-500"}`} />
            <span className="text-xs text-muted-foreground">{connected ? "Live" : "Offline"}</span>
          </div>

          {/* Metrics */}
          <div className="flex items-center gap-1.5 flex-1 overflow-hidden ml-1">
            <MetricChip label="Online" value={m.agents_online}     color="green"  />
            <MetricChip label="Active" value={m.tasks_in_progress} color="amber"  />
            <MetricChip label="Done"   value={m.tasks_done}        color="violet" />
            <MetricChip label="Total"  value={m.tasks_total}       color="slate"  />
          </div>

          <LaunchWizard />
        </div>
      </header>

      {/* ── 3-column grid ── */}
      <div className="flex-1 p-4 md:p-5 grid gap-4 md:grid-cols-[280px_1fr_290px] items-start">
        <AgentPanel  agents={s.agents}   tasks={s.tasks} />
        <ChatPanel   messages={s.messages} />
        <ControlsPanel />
      </div>

      {/* ── Spawn health + traces ── */}
      <div className="px-4 md:px-5 grid gap-4 md:grid-cols-2 pb-4">
        <SpawnHealthPanel spawnStatus={s.spawn_status} />
        <TracesPanel liveEvents={s.trace_events} />
      </div>

      {/* ── Task board ── */}
      <div className="px-4 md:px-5 pb-6">
        <TaskBoard tasks={s.tasks} />
      </div>
    </div>
  );
}
