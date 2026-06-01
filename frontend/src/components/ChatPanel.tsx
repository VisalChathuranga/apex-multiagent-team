"use client";

import { useEffect, useRef } from "react";
import { Message } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  return (
    <Card className="flex flex-col" data-testid="chat-panel">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
          Channel
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1">
        <ScrollArea className="h-64">
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
      </CardContent>
    </Card>
  );
}
