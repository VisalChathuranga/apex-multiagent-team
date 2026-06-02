#!/usr/bin/env python3
"""
api_server.py — FastAPI REST + WebSocket bridge for the APEX team system.

Exposes the team_coordinator.py state file over HTTP so the Next.js dashboard
can read and write team state without going through MCP.

Endpoints:
  GET  /api/state              full state snapshot
  GET  /api/agents             agent roster
  GET  /api/tasks              task board
  GET  /api/messages?since=N   channel messages from index N
  GET  /api/metrics            computed metrics
  GET  /api/facts              all facts
  GET  /api/debate             current debate
  GET  /api/findings           security findings

  POST   /api/tasks             add_task
  PATCH  /api/tasks/{id}        update_task
  POST   /api/messages          post_message
  POST   /api/agents/join       join_team
  PATCH  /api/agents/{role}/status  set_status
  POST   /api/facts             set_fact
  POST   /api/recovery          recover stale tasks (crash recovery)

  WS     /ws/updates            push state snapshots when state changes

Run standalone:
  uvicorn api_server:app --host 0.0.0.0 --port 7000 --reload

Or from Python:
  import uvicorn; uvicorn.run("api_server:app", host="0.0.0.0", port=7000)
"""

from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import team_coordinator as tc
import spawn_util


# ---------------------------------------------------------------------------
# WebSocket connection manager
# ---------------------------------------------------------------------------

class _WSManager:
    def __init__(self):
        self._clients: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._clients.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self._clients:
            self._clients.remove(ws)

    async def broadcast(self, data: dict) -> None:
        msg = json.dumps(data, default=str)
        dead: list[WebSocket] = []
        for ws in list(self._clients):
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


_ws_manager = _WSManager()
_last_write_count: int = -1


async def _state_broadcaster() -> None:
    """Poll the state file every second; broadcast to WebSocket clients on change."""
    global _last_write_count
    while True:
        await asyncio.sleep(1)
        if not _ws_manager._clients:
            continue
        try:
            state = tc._load()
            wc = state.get("_write_count", 0)
            if wc != _last_write_count:
                _last_write_count = wc
                await _ws_manager.broadcast(_build_snapshot(state))
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_state_broadcaster())
    yield
    task.cancel()


app = FastAPI(title="APEX Team API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_snapshot(state: dict) -> dict:
    return {
        "metrics": tc._compute_metrics(state),
        "agents": state.get("agents", {}),
        "tasks": state.get("tasks", []),
        "messages": state.get("messages", []),
        "debate": state.get("debate"),
        "timeline": state.get("activity_log", []),
        "facts": {k: v["value"] if isinstance(v, dict) else v
                  for k, v in state.get("facts", {}).items()},
        "findings": state.get("findings", []),
    }


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class AddTaskBody(BaseModel):
    title: str
    assignee: str = ""
    created_by: str = ""
    priority: str = "medium"
    depends_on: str = ""
    parent_id: int = 0


class UpdateTaskBody(BaseModel):
    status: str = ""
    assignee: str = ""
    note: str = ""
    by_role: str = ""


class PostMessageBody(BaseModel):
    sender_role: str
    text: str
    mention: str = ""


class JoinTeamBody(BaseModel):
    role: str
    name: str = ""


class SetStatusBody(BaseModel):
    status: str


class SetFactBody(BaseModel):
    key: str
    value: str
    by_role: str = ""


class RecoverBody(BaseModel):
    stale_seconds: int = 0
    by_role: str = "PM"


class LaunchBody(BaseModel):
    goal: str
    mode: str = "ask"
    cli: str = "claude"
    roles: List[str] = ["Backend", "Frontend", "QA"]
    project_dir: str = ""


# ---------------------------------------------------------------------------
# GET endpoints
# ---------------------------------------------------------------------------

@app.get("/api/state")
def get_state():
    return _build_snapshot(tc._load())


@app.get("/api/agents")
def get_agents():
    return tc._load().get("agents", {})


@app.get("/api/tasks")
def get_tasks():
    return tc._load().get("tasks", [])


@app.get("/api/messages")
def get_messages(since: int = 0):
    msgs = tc._load().get("messages", [])
    return {"messages": msgs[since:], "next_index": len(msgs)}


@app.get("/api/metrics")
def get_metrics():
    return tc._compute_metrics(tc._load())


@app.get("/api/facts")
def get_facts():
    raw = tc._load().get("facts", {})
    return {k: (v["value"] if isinstance(v, dict) else v) for k, v in raw.items()}


@app.get("/api/debate")
def get_debate():
    return tc._load().get("debate")


@app.get("/api/findings")
def get_findings():
    return tc._load().get("findings", [])


# ---------------------------------------------------------------------------
# POST / PATCH endpoints
# ---------------------------------------------------------------------------

@app.post("/api/tasks", status_code=201)
def add_task(body: AddTaskBody):
    result = tc.add_task(
        title=body.title,
        assignee=body.assignee,
        created_by=body.created_by,
        priority=body.priority,
        depends_on=body.depends_on,
        parent_id=body.parent_id,
    )
    return {"message": result}


@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, body: UpdateTaskBody):
    result = tc.update_task(
        task_id=task_id,
        status=body.status,
        assignee=body.assignee,
        note=body.note,
        by_role=body.by_role,
    )
    if "No task" in result:
        raise HTTPException(status_code=404, detail=result)
    if "BLOCKED" in result:
        raise HTTPException(status_code=409, detail=result)
    return {"message": result}


@app.post("/api/messages", status_code=201)
def post_message(body: PostMessageBody):
    result = tc.post_message(
        sender_role=body.sender_role,
        text=body.text,
        mention=body.mention,
    )
    return {"message": result}


@app.post("/api/agents/join", status_code=201)
def join_team(body: JoinTeamBody):
    result = tc.join_team(role=body.role, name=body.name)
    return {"message": result}


@app.patch("/api/agents/{role}/status")
def set_status(role: str, body: SetStatusBody):
    result = tc.set_status(role=role, status=body.status)
    if "must be one of" in result:
        raise HTTPException(status_code=400, detail=result)
    return {"message": result}


@app.post("/api/facts")
def set_fact(body: SetFactBody):
    result = tc.set_fact(key=body.key, value=body.value, by_role=body.by_role)
    return {"message": result}


@app.post("/api/recovery")
def recover_tasks(body: RecoverBody = RecoverBody()):
    result = tc.recover_tasks(stale_seconds=body.stale_seconds, by_role=body.by_role)
    return {"message": result}


@app.post("/api/launch", status_code=200)
def launch_team(body: LaunchBody):
    goal = body.goal.strip()
    if not goal:
        raise HTTPException(status_code=400, detail="goal is required")

    _VALID_MODES = {"ask", "same"}
    _VALID_CLIS  = {"claude", "codex", "gemini", "cursor"}
    mode = body.mode if body.mode in _VALID_MODES else "ask"
    cli  = body.cli.lower() if body.cli.lower() in _VALID_CLIS else "claude"
    roles = body.roles if body.roles else ["Backend", "Frontend", "QA"]

    here = os.path.dirname(os.path.abspath(__file__))
    project_dir = (
        os.path.abspath(os.path.expanduser(body.project_dir))
        if body.project_dir.strip()
        else here
    )
    os.makedirs(project_dir, exist_ok=True)

    seed   = spawn_util.pm_seed(goal, project_dir, roles, cli, mode=mode)
    status = spawn_util.open_terminal_pm(cli, seed, project_dir)
    return {"message": status, "project_dir": project_dir}


# ---------------------------------------------------------------------------
# WebSocket live updates
# ---------------------------------------------------------------------------

@app.websocket("/ws/updates")
async def ws_updates(ws: WebSocket):
    await _ws_manager.connect(ws)
    try:
        # Send current state immediately on connect
        await ws.send_text(json.dumps(_build_snapshot(tc._load()), default=str))
        # Keep connection open; client may send pings
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        _ws_manager.disconnect(ws)
    except Exception:
        _ws_manager.disconnect(ws)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=7000, reload=False)
