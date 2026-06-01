"use client";

import { useEffect, useRef, useState } from "react";
import { Message, api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";

function renderText(text: string) {
  // Highlight @mentions
  return text.split(/(@\w+)/g).map((part, i) =>
    part.startsWith("@") ? (
      <span key={i} className="font-semibold text-amber-400">
        {part}
      </span>
    ) : (
      part
    )
  );
}

interface Props {
  messages: Message[];
}

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
    } catch {
      // silently ignore; user can retry
    }
  }

  return (
    <Card className="flex flex-col" data-testid="chat-panel">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
          Channel
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col gap-2">
        <ScrollArea className="h-56">
          <div className="space-y-1 pr-2" data-testid="chat-messages">
            {messages.length === 0 && (
              <p className="text-sm text-muted-foreground">No messages yet.</p>
            )}
            {messages.slice(-80).map((m, i) => (
              <div key={i} data-testid={`chat-message-${i}`} className="text-sm leading-snug">
                <span className="font-semibold text-blue-400">{m.from}</span>
                <span className="text-muted-foreground mx-1 text-xs">{m.time}</span>
                <span>{renderText(m.text)}</span>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        </ScrollArea>
        <form onSubmit={handleSend} className="flex gap-2">
          <Input
            data-testid="chat-input"
            placeholder="Send a message…"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            className="flex-1 text-sm"
          />
          <Button
            data-testid="chat-send"
            type="submit"
            size="sm"
            disabled={!text.trim()}
          >
            Send
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
