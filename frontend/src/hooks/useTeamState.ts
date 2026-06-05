"use client";

import { useEffect, useRef, useState } from "react";
import { TeamState, WS_URL, api } from "@/lib/api";

export function useTeamState(): { state: TeamState | null; ready: boolean } {
  const [state, setState] = useState<TeamState | null>(null);
  const [ready, setReady] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const readyTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let dead = false;

    function connect() {
      if (dead) return;
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onmessage = (e) => {
        try {
          setState(JSON.parse(e.data) as TeamState);
          setReady(true);
        } catch {
          // ignore malformed frames
        }
      };

      ws.onclose = () => {
        if (!dead) {
          retryRef.current = setTimeout(connect, 2000);
        }
      };

      ws.onerror = () => ws.close();
    }

    api.getState().then((s) => { setState(s); setReady(true); }).catch(() => null);
    // Show the UI after 3 s even if the API hasn't responded yet
    readyTimerRef.current = setTimeout(() => setReady(true), 3000);
    connect();

    return () => {
      dead = true;
      if (retryRef.current) clearTimeout(retryRef.current);
      if (readyTimerRef.current) clearTimeout(readyTimerRef.current);
      wsRef.current?.close();
    };
  }, []);

  return { state, ready };
}
