"use client";

import { TeamState } from "@/lib/api";

export function SpawnHealthPanel({ spawnStatus }: { spawnStatus?: TeamState["spawn_status"] }) {
  if (!spawnStatus?.entries?.length) return null;

  return (
    <div className="rounded-xl border border-border/60 bg-card overflow-hidden mb-4">
      <div className="px-4 py-2 border-b border-border/50 bg-white/[0.02]">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Last launch — {spawnStatus.time}
        </span>
      </div>
      <ul className="px-4 py-2 flex flex-wrap gap-2">
        {spawnStatus.entries.map((e) => (
          <li
            key={e.title}
            className={`text-xs rounded-full border px-2.5 py-1 ${
              e.status === "spawned"
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                : "border-red-500/30 bg-red-500/10 text-red-400"
            }`}
          >
            {e.title}
            {e.cli && e.cli !== "ask-on-open" ? ` (${e.cli})` : ""}
          </li>
        ))}
      </ul>
    </div>
  );
}
