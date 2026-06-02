"use client";

import { useEffect, useRef, useState } from "react";
import { Message, api } from "@/lib/api";
import { Button }       from "@/components/ui/button";
import { Input }        from "@/components/ui/input";
import { ScrollArea }   from "@/components/ui/scroll-area";
import { Send, Radio }  from "lucide-react";

/* ── Avatar helpers ─────────────────────────────────────────── */
const AVATAR_PALETTES = [
  "bg-violet-500/25 text-violet-300",
  "bg-cyan-500/25   text-cyan-300",
  "bg-amber-500/25  text-amber-300",
  "bg-emerald-500/25 text-emerald-300",
  "bg-rose-500/25   text-rose-300",
  "bg-blue-500/25   text-blue-300",
  "bg-indigo-500/25 text-indigo-300",
  "bg-orange-500/25 text-orange-300",
];

function avatarColor(name: string): string {
  let h = 0;
  for (const c of name) h = ((h << 5) - h + c.charCodeAt(0)) | 0;
  return AVATAR_PALETTES[Math.abs(h) % AVATAR_PALETTES.length];
}

function initials(name: string): string {
  const parts = name.trim().split(/[\s_\-]+/);
  return parts.length >= 2
    ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
    : name.slice(0, 2).toUpperCase();
}

/* ── @mention highlight ─────────────────────────────────────── */
function renderText(text: string) {
  return text.split(/(@\w+)/g).map((part, i) =>
    part.startsWith("@")
      ? <span key={i} className="font-semibold text-cyan-400">{part}</span>
      : part
  );
}

/* ── Component ──────────────────────────────────────────────── */
interface Props { messages: Message[] }

export function ChatPanel({ messages }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [text, setText] = useState("");

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  async function handleSend(e?: React.FormEvent) {
    e?.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) return;
    try {
      await api.postMessage({ sender_role: "Dashboard", text: trimmed });
      setText("");
    } catch { /* silent */ }
  }

  const visible = messages.slice(-80);

  return (
    <div
      data-testid="chat-panel"
      className="rounded-xl border border-border/60 bg-card flex flex-col"
      style={{ minHeight: "440px" }}
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border/50 bg-white/[0.02] shrink-0">
        <Radio className="h-3.5 w-3.5 text-muted-foreground" />
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Channel</span>
        {messages.length > 0 && (
          <span className="ml-auto rounded-full bg-white/5 border border-border/40 px-2 py-0.5 text-[11px] text-muted-foreground tabular-nums">
            {messages.length}
          </span>
        )}
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 px-4 py-3">
        <div className="space-y-4" data-testid="chat-messages">
          {visible.length === 0 && (
            <p className="py-10 text-center text-sm text-muted-foreground/60">
              No messages yet — the team will start posting here once launched.
            </p>
          )}

          {visible.map((m, i) => (
            <div
              key={i}
              data-testid={`chat-message-${i}`}
              className="flex items-start gap-3 animate-fade-up"
            >
              {/* Avatar */}
              <div
                className={`h-7 w-7 shrink-0 rounded-lg flex items-center justify-center text-[10px] font-bold ${avatarColor(m.from)}`}
              >
                {initials(m.from)}
              </div>

              {/* Body */}
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-2 mb-0.5">
                  <span className="text-xs font-semibold text-foreground">{m.from}</span>
                  <span className="text-[10px] text-muted-foreground/60">{m.time}</span>
                </div>
                <p className="text-sm text-foreground/80 leading-relaxed break-words">
                  {renderText(m.text)}
                </p>
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="px-3 pb-3 pt-2 border-t border-border/50 shrink-0">
        <form onSubmit={handleSend} className="flex gap-2">
          <Input
            data-testid="chat-input"
            placeholder="Message the team…"
            value={text}
            onChange={e => setText(e.target.value)}
            onKeyDown={e => {
              if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
            }}
            className="flex-1 h-9 text-sm bg-background/40 border-border/50 focus:border-primary/60 focus:ring-0 placeholder:text-muted-foreground/50"
          />
          <Button
            data-testid="chat-send"
            type="submit"
            size="sm"
            disabled={!text.trim()}
            className="h-9 w-9 p-0 shrink-0"
          >
            <Send className="h-3.5 w-3.5" />
          </Button>
        </form>
      </div>
    </div>
  );
}
