"use client";

import { useEffect, useState } from "react";
import { api, TraceEvent } from "@/lib/api";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Activity } from "lucide-react";

export function TracesPanel({ liveEvents }: { liveEvents?: TraceEvent[] }) {
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [cost, setCost] = useState<{ total_tokens: number; by_role: Record<string, number> } | null>(null);

  useEffect(() => {
    api.getTraces(80).then((r) => {
      setEvents(r.events);
      setCost(r.cost ?? null);
    }).catch(() => {});
  }, []);

  const display = liveEvents?.length ? liveEvents : events;

  return (
    <div data-testid="traces-panel" className="rounded-xl border border-border/60 bg-card overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border/50 bg-white/[0.02]">
        <Activity className="h-3.5 w-3.5 text-muted-foreground" />
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Traces
        </span>
        {cost && (
          <span className="ml-auto text-xs text-muted-foreground tabular-nums">
            tokens: {cost.total_tokens}
          </span>
        )}
      </div>

      {cost && Object.keys(cost.by_role || {}).length > 0 && (
        <div className="px-4 py-2 flex flex-wrap gap-1.5 border-b border-border/40">
          {Object.entries(cost.by_role).map(([role, n]) => (
            <span
              key={role}
              className="text-[10px] rounded-full border border-violet-500/30 bg-violet-500/10 px-2 py-0.5 text-violet-300"
            >
              {role}: {n}
            </span>
          ))}
        </div>
      )}

      <ScrollArea className="h-[220px]">
        <ul className="px-3 py-2 space-y-1.5">
          {display.length === 0 && (
            <li className="text-xs text-muted-foreground py-4 text-center">
              No trace events yet. Launch team or use dashboard controls.
            </li>
          )}
          {display.map((e, i) => (
            <li
              key={`${e.time}-${i}`}
              className="text-xs rounded-md border border-border/40 px-2.5 py-1.5 bg-white/[0.02]"
            >
              <div className="flex items-center gap-2 text-muted-foreground">
                <span className="font-mono text-[10px]">{e.time}</span>
                <span className="font-medium text-foreground/80">{e.role}</span>
                <span className="text-primary/90">{e.event}</span>
                {e.status === "failed" && (
                  <span className="text-destructive">failed</span>
                )}
              </div>
              {e.detail && (
                <p className="mt-0.5 text-muted-foreground/80 truncate">{e.detail}</p>
              )}
            </li>
          ))}
        </ul>
      </ScrollArea>
    </div>
  );
}
