"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";

const AGENTS = [
  { id: "architect",        desc: "C4 diagrams, ADRs, system design, tech-stack decisions" },
  { id: "analyst",          desc: "User stories, acceptance criteria, MVP scope" },
  { id: "backend",          desc: "APIs & server logic — Node / Go / Python / Rust / .NET" },
  { id: "frontend",         desc: "UI & components — Next.js, React, Vue, SvelteKit, Astro" },
  { id: "dba",              desc: "Schemas, migrations, indexes, query optimization" },
  { id: "ai-integrator",    desc: "LLM/RAG pipelines, vector stores, AI service clients" },
  { id: "tester",           desc: "Unit, integration & E2E tests — pytest / jest / Playwright" },
  { id: "reviewer",         desc: "Code review — SOLID, DRY, readability, refactor suggestions" },
  { id: "perf-tuner",       desc: "Profiling, latency, N+1 hunting, bundle-size triage" },
  { id: "security-auditor", desc: "OWASP Top 10, CVEs, weak auth/crypto, secrets — read-only" },
  { id: "pen-tester",       desc: "Offensive testing, exploit validation — read-only" },
  { id: "dfir-analyst",     desc: "Incident response, log analysis, Sigma/YARA detection rules" },
  { id: "writer",           desc: "README, CHANGELOG, API docs, release notes" },
  { id: "devops",           desc: "CI/CD pipelines, Dockerfiles, GitHub Actions, Vercel/AWS" },
];

const CLI_OPTIONS = [
  { value: "claude",  label: "Claude (claude-code)" },
  { value: "codex",   label: "Codex (openai codex)" },
  { value: "gemini",  label: "Gemini (gemini-cli)" },
  { value: "cursor",  label: "Cursor Agent" },
];

const DEFAULT_AGENTS = new Set(["backend", "frontend", "tester"]);

export function LaunchWizard() {
  const [open, setOpen]                   = useState(false);
  const [goal, setGoal]                   = useState("");
  const [mode, setMode]                   = useState<"ask" | "same">("ask");
  const [cli, setCli]                     = useState("claude");
  const [projectDir, setProjectDir]       = useState("");
  const [selected, setSelected]           = useState<Set<string>>(new Set(DEFAULT_AGENTS));
  const [feedback, setFeedback]           = useState<{ ok: boolean; text: string } | null>(null);
  const [launching, setLaunching]         = useState(false);

  function toggleAgent(id: string) {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function reset() {
    setGoal("");
    setMode("ask");
    setCli("claude");
    setProjectDir("");
    setSelected(new Set(DEFAULT_AGENTS));
    setFeedback(null);
  }

  function handleOpenChange(v: boolean) {
    setOpen(v);
    if (!v) reset();
  }

  async function handleLaunch() {
    if (!goal.trim() || selected.size === 0) return;
    setLaunching(true);
    setFeedback(null);
    try {
      const res = await api.launchTeam({
        goal:        goal.trim(),
        mode,
        cli,
        roles:       Array.from(selected),
        project_dir: projectDir.trim(),
      });
      setFeedback({ ok: true, text: res.message });
      setTimeout(() => handleOpenChange(false), 1800);
    } catch (err: unknown) {
      setFeedback({ ok: false, text: err instanceof Error ? err.message : String(err) });
    } finally {
      setLaunching(false);
    }
  }

  return (
    <>
      <Button size="sm" onClick={() => setOpen(true)}>
        Launch Team
      </Button>

      <Dialog open={open} onOpenChange={handleOpenChange}>
        <DialogContent
          className="sm:max-w-2xl overflow-y-auto max-h-[90vh]"
          showCloseButton
        >
          <DialogHeader>
            <DialogTitle>Launch APEX Team</DialogTitle>
          </DialogHeader>

          <div className="space-y-5 pb-1">

            {/* ── Goal ── */}
            <section>
              <SectionLabel>What should the team build?</SectionLabel>
              <Textarea
                placeholder="e.g. Build a REST API with auth and a React dashboard…"
                value={goal}
                onChange={e => setGoal(e.target.value)}
                rows={3}
                className="text-sm resize-none mt-1.5"
              />
            </section>

            <Separator />

            {/* ── Mode ── */}
            <section>
              <SectionLabel>Agent mode</SectionLabel>
              <div className="grid grid-cols-2 gap-2 mt-1.5">
                <ModeCard
                  active={mode === "ask"}
                  onClick={() => setMode("ask")}
                  title="ASK"
                  desc="Each terminal asks which CLI to use — mix freely"
                />
                <ModeCard
                  active={mode === "same"}
                  onClick={() => setMode("same")}
                  title="SAME"
                  desc="All agents use the same CLI as the PM"
                />
              </div>
            </section>

            {/* ── CLI ── */}
            <section>
              <SectionLabel>
                CLI tool{mode === "ask" ? " (for PM terminal)" : " (all agents)"}
              </SectionLabel>
              <select
                value={cli}
                onChange={e => setCli(e.target.value)}
                className="mt-1.5 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                {CLI_OPTIONS.map(o => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </section>

            {/* ── Project dir ── */}
            <section>
              <SectionLabel>
                Project directory{" "}
                <span className="normal-case font-normal opacity-60">(leave blank for current dir)</span>
              </SectionLabel>
              <Input
                placeholder="e.g. D:\my-project"
                value={projectDir}
                onChange={e => setProjectDir(e.target.value)}
                className="mt-1.5 text-sm font-mono"
              />
            </section>

            <Separator />

            {/* ── Agent checkboxes ── */}
            <section>
              <div className="flex items-center justify-between">
                <SectionLabel>{selected.size} agent{selected.size !== 1 ? "s" : ""} selected</SectionLabel>
                <div className="flex gap-3 text-xs">
                  <button
                    type="button"
                    onClick={() => setSelected(new Set(AGENTS.map(a => a.id)))}
                    className="text-primary hover:underline"
                  >
                    Select all
                  </button>
                  <span className="text-muted-foreground">·</span>
                  <button
                    type="button"
                    onClick={() => setSelected(new Set())}
                    className="text-primary hover:underline"
                  >
                    Clear
                  </button>
                </div>
              </div>

              <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                {AGENTS.map(agent => (
                  <AgentCheckbox
                    key={agent.id}
                    id={agent.id}
                    desc={agent.desc}
                    checked={selected.has(agent.id)}
                    onChange={() => toggleAgent(agent.id)}
                  />
                ))}
              </div>
            </section>

            {/* ── Feedback ── */}
            {feedback && (
              <p
                className={`rounded px-3 py-2 text-xs ${
                  feedback.ok
                    ? "bg-green-500/10 text-green-700 dark:text-green-400"
                    : "bg-destructive/10 text-destructive"
                }`}
              >
                {feedback.text}
              </p>
            )}

            {/* ── Actions ── */}
            <div className="flex justify-end gap-2 pt-1">
              <Button variant="outline" size="sm" onClick={() => handleOpenChange(false)}>
                Cancel
              </Button>
              <Button
                size="sm"
                disabled={!goal.trim() || selected.size === 0 || launching}
                onClick={handleLaunch}
              >
                {launching
                  ? "Launching…"
                  : `Launch ${selected.size} Agent${selected.size !== 1 ? "s" : ""}`}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

/* ── Small presentational helpers ── */

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
      {children}
    </p>
  );
}

function ModeCard({
  active, onClick, title, desc,
}: {
  active: boolean;
  onClick: () => void;
  title: string;
  desc: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-lg border p-3 text-left transition-colors ${
        active
          ? "border-primary bg-primary/5 text-foreground"
          : "border-border text-muted-foreground hover:border-primary/40"
      }`}
    >
      <p className="text-sm font-semibold">{title}</p>
      <p className="mt-0.5 text-xs opacity-70 leading-tight">{desc}</p>
    </button>
  );
}

function AgentCheckbox({
  id, desc, checked, onChange,
}: {
  id: string;
  desc: string;
  checked: boolean;
  onChange: () => void;
}) {
  return (
    <label
      className={`flex cursor-pointer items-start gap-2.5 rounded-lg border p-2.5 transition-colors ${
        checked
          ? "border-primary/60 bg-primary/5"
          : "border-border hover:border-primary/30"
      }`}
    >
      <input
        type="checkbox"
        checked={checked}
        onChange={onChange}
        className="mt-0.5 h-4 w-4 shrink-0 accent-primary"
      />
      <div className="min-w-0">
        <p className="font-mono text-sm font-medium leading-none">{id}</p>
        <p className="mt-0.5 text-xs leading-tight text-muted-foreground">{desc}</p>
      </div>
    </label>
  );
}
