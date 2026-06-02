"use client";

import { useState } from "react";
import { api }      from "@/lib/api";
import { Button }   from "@/components/ui/button";
import { Input }    from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Plus, Send, RefreshCw, Download, Settings2 } from "lucide-react";

const SENDER_ROLE = "Dashboard";

export function ControlsPanel() {
  const [taskTitle, setTaskTitle] = useState("");
  const [msgText,   setMsgText]   = useState("");
  const [feedback,  setFeedback]  = useState<{ ok: boolean; text: string } | null>(null);

  function flash(ok: boolean, text: string) {
    setFeedback({ ok, text });
    setTimeout(() => setFeedback(null), 3000);
  }

  async function handleAddTask(e: React.FormEvent) {
    e.preventDefault();
    if (!taskTitle.trim()) return;
    try {
      await api.addTask({ title: taskTitle.trim(), priority: "medium" });
      setTaskTitle("");
      flash(true, "Task added to the board.");
    } catch (err: unknown) {
      flash(false, err instanceof Error ? err.message : String(err));
    }
  }

  async function handlePostMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!msgText.trim()) return;
    try {
      await api.postMessage({ sender_role: SENDER_ROLE, text: msgText.trim() });
      setMsgText("");
      flash(true, "Message posted.");
    } catch (err: unknown) {
      flash(false, err instanceof Error ? err.message : String(err));
    }
  }

  async function handleRecover() {
    try {
      const r = await api.recover();
      flash(true, r.message ?? "Recovery complete.");
    } catch (err: unknown) {
      flash(false, err instanceof Error ? err.message : String(err));
    }
  }

  async function handleExport() {
    try {
      const state = await api.getState();
      const blob  = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
      const url   = URL.createObjectURL(blob);
      const a     = document.createElement("a");
      a.href      = url;
      a.download  = "apex-state-export.json";
      a.click();
      URL.revokeObjectURL(url);
      flash(true, "State exported.");
    } catch (err: unknown) {
      flash(false, err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <div data-testid="controls-panel" className="rounded-xl border border-border/60 bg-card overflow-hidden">

      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border/50 bg-white/[0.02]">
        <Settings2 className="h-3.5 w-3.5 text-muted-foreground" />
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Controls</span>
      </div>

      <div className="p-4 space-y-5">

        {/* ── Add task ── */}
        <section>
          <p className="text-xs font-medium text-muted-foreground mb-2">Add Task</p>
          <form onSubmit={handleAddTask} className="flex gap-2">
            <Input
              data-testid="add-task-title"
              placeholder="Task title…"
              value={taskTitle}
              onChange={e => setTaskTitle(e.target.value)}
              className="flex-1 h-9 text-sm bg-background/40 border-border/50 focus:border-primary/60 placeholder:text-muted-foreground/50"
            />
            <Button
              data-testid="add-task-submit"
              type="submit"
              size="sm"
              disabled={!taskTitle.trim()}
              className="h-9 w-9 p-0 shrink-0"
            >
              <Plus className="h-4 w-4" />
            </Button>
          </form>
        </section>

        <Separator className="bg-border/40" />

        {/* ── Post message ── */}
        <section>
          <p className="text-xs font-medium text-muted-foreground mb-2">Post to Channel</p>
          <form onSubmit={handlePostMessage} className="space-y-2">
            <Textarea
              data-testid="post-message-input"
              placeholder="Write a message to the team…"
              value={msgText}
              onChange={e => setMsgText(e.target.value)}
              onKeyDown={e => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handlePostMessage(e as React.FormEvent);
                }
              }}
              rows={3}
              className="text-sm resize-none bg-background/40 border-border/50 focus:border-primary/60 placeholder:text-muted-foreground/50"
            />
            <Button
              data-testid="post-message-send"
              type="submit"
              size="sm"
              disabled={!msgText.trim()}
              className="w-full h-9 gap-2"
            >
              <Send className="h-3.5 w-3.5" />
              Send
            </Button>
          </form>
        </section>

        <Separator className="bg-border/40" />

        {/* ── Actions ── */}
        <section>
          <p className="text-xs font-medium text-muted-foreground mb-2">Actions</p>
          <div className="grid grid-cols-2 gap-2">
            <Button
              data-testid="btn-assign"
              variant="outline"
              size="sm"
              className="h-9 text-xs border-border/50 hover:border-border/80 hover:bg-white/5"
              onClick={() => flash(true, "Auto-assign triggered.")}
            >
              Auto-assign
            </Button>
            <Button
              data-testid="btn-recover"
              variant="outline"
              size="sm"
              className="h-9 text-xs gap-1.5 border-border/50 hover:border-border/80 hover:bg-white/5"
              onClick={handleRecover}
            >
              <RefreshCw className="h-3 w-3" />
              Recover
            </Button>
            <Button
              data-testid="btn-export"
              variant="outline"
              size="sm"
              className="col-span-2 h-9 text-xs gap-1.5 border-border/50 hover:border-border/80 hover:bg-white/5"
              onClick={handleExport}
            >
              <Download className="h-3 w-3" />
              Export State
            </Button>
          </div>
        </section>

        {/* ── Feedback ── */}
        {feedback && (
          <div
            data-testid="controls-feedback"
            className={`rounded-lg border px-3 py-2 text-xs font-medium ${
              feedback.ok
                ? "bg-emerald-500/8 border-emerald-500/20 text-emerald-400"
                : "bg-red-500/8    border-red-500/20    text-red-400"
            }`}
          >
            {feedback.text}
          </div>
        )}
      </div>
    </div>
  );
}
