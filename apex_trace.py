"""Lightweight agent tracing — stored in shared team state."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import team_coordinator as tc

_MAX_EVENTS = 500


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def log_trace(
    event: str,
    role: str = "system",
    detail: str = "",
    tokens: int = 0,
    tool: str = "",
    status: str = "ok",
    meta: Optional[dict] = None,
) -> str:
    """Append a trace event (API, spawn, MCP tool, etc.)."""
    entry = {
        "time": _now(),
        "role": role,
        "event": event,
        "detail": detail[:2000],
        "tokens": int(tokens or 0),
        "tool": tool,
        "status": status,
        "meta": meta or {},
    }

    def op(state: dict) -> None:
        events: List[dict] = state.setdefault("trace_events", [])
        events.append(entry)
        if len(events) > _MAX_EVENTS:
            state["trace_events"] = events[-_MAX_EVENTS:]
        tc._log(state, role, f"trace:{event}")

    tc._mutate(op)
    return f"Trace logged: {event} ({role})"


def get_traces(limit: int = 100, role: str = "") -> List[Dict[str, Any]]:
    events = tc._load().get("trace_events", [])
    if role:
        events = [e for e in events if e.get("role", "").lower() == role.lower()]
    return list(reversed(events[-limit:]))


def trace_cost_summary() -> Dict[str, Any]:
    events = tc._load().get("trace_events", [])
    by_role: Dict[str, int] = {}
    total = 0
    for e in events:
        t = int(e.get("tokens") or 0)
        total += t
        r = e.get("role") or "unknown"
        by_role[r] = by_role.get(r, 0) + t
    return {"total_tokens": total, "by_role": by_role, "event_count": len(events)}
