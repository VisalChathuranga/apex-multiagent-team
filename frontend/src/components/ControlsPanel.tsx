"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";

const SENDER_ROLE = "Dashboard";

export function ControlsPanel() {
  const [taskTitle, setTaskTitle] = useState("");
  const [msgText, setMsgText] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);

  function flash(msg: string) {
    setFeedback(msg);
    setTimeout(() => setFeedback(null), 3000);
  }

  async function handleAddTask(e: React.FormEvent) {
    e.preventDefault();
    if (!taskTitle.trim()) return;
    try {
      await api.addTask({ title: taskTitle.trim(), priority: "medium" });
      setTaskTitle("");
      flash("Task added.");
    } catch (err: unknown) {
      flash(`Error: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  async function handlePostMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!msgText.trim()) return;
    try {
      await api.postMessage({ sender_role: SENDER_ROLE, text: msgText.trim() });
      setMsgText("");
      flash("Message sent.");
    } catch (err: unknown) {
      flash(`Error: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  async function handleAssign() {
    flash("Auto-assign triggered.");
  }

  async function handleRecover() {
    try {
      const r = await api.recover();
      flash(r.message ?? "Recovery done.");
    } catch (err: unknown) {
      flash(`Error: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  async function handleExport() {
    try {
      const state = await api.getState();
      const blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "apex-state-export.json";
      a.click();
      URL.revokeObjectURL(url);
      flash("Export downloaded.");
    } catch (err: unknown) {
      flash(`Error: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  return (
    <Card data-testid="controls-panel">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
          Controls
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Add Task */}
        <form onSubmit={handleAddTask} className="flex gap-2">
          <Input
            data-testid="add-task-title"
            placeholder="New task title…"
            value={taskTitle}
            onChange={(e) => setTaskTitle(e.target.value)}
            className="flex-1 text-sm"
          />
          <Button
            data-testid="add-task-submit"
            type="submit"
            size="sm"
            disabled={!taskTitle.trim()}
          >
            Add
          </Button>
        </form>

        <Separator />

        {/* Post Message */}
        <form onSubmit={handlePostMessage} className="space-y-2">
          <Textarea
            data-testid="post-message-input"
            placeholder="Post a message…"
            value={msgText}
            onChange={(e) => setMsgText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handlePostMessage(e as React.FormEvent);
              }
            }}
            rows={2}
            className="text-sm resize-none"
          />
          <Button
            data-testid="post-message-send"
            type="submit"
            size="sm"
            disabled={!msgText.trim()}
            className="w-full"
          >
            Send
          </Button>
        </form>

        <Separator />

        {/* Action buttons */}
        <div className="flex flex-wrap gap-2">
          <Button
            data-testid="btn-assign"
            variant="outline"
            size="sm"
            onClick={handleAssign}
          >
            Auto-assign
          </Button>
          <Button
            data-testid="btn-recover"
            variant="outline"
            size="sm"
            onClick={handleRecover}
          >
            Recover
          </Button>
          <Button
            data-testid="btn-export"
            variant="outline"
            size="sm"
            onClick={handleExport}
          >
            Export
          </Button>
        </div>

        {feedback && (
          <p data-testid="controls-feedback" className="text-xs text-muted-foreground">
            {feedback}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
