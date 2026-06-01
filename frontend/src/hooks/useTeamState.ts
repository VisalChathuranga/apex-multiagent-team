"use client";

import { useEffect, useRef, useState } from "react";
import { TeamState, WS_URL, api } from "@/lib/api";

export function useTeamState(): TeamState | null {
  const [state, setState] = useState<TeamState | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let dead = false;

    function connect() {
      if (dead) return;
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onmessage = (e) => {
        try {
          setState(JSON.parse(e.data) as TeamState);
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

    // Initial REST fetch so the UI isn't blank while WS connects
    api.getState().then(setState).catch(() => null);
    connect();

    return () => {
      dead = true;
      if (retryRef.current) clearTimeout(retryRef.current);
      wsRef.current?.close();
    };
  }, []);

  return state;
}
