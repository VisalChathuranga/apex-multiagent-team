#!/usr/bin/env python3
"""
api_server.py — FastAPI REST + WebSocket bridge for the APEX team system.

Exposes the team_coordinator.py state file over HTTP so the Next.js dashboard
can read and write team state without going through MCP.
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
import apex_trace
import mcp_gateway
import a2a_bridge
import apex_rag
import apex_v25

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


app = FastAPI(title="APEX Team API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        "spawn_status": state.get("spawn_status"),
        "trace_events": state.get("trace_events", [])[-50:],
        "trace_cost": apex_trace.trace_cost_summary(),
        "gateway_targets": state.get("gateway_targets", []),
        "a2a_card": state.get("a2a_agent_card") or a2a_bridge.build_agent_card(),
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
    auto_agents: bool = False


class GatewayRegisterBody(BaseModel):
    name: str
    transport: str = "stdio"
    command: str = ""
    url: str = ""
    description: str = ""


class GatewayCallBody(BaseModel):
    target_name: str
    tool_name: str
    arguments_json: str = "{}"


class OpenAPIImportBody(BaseModel):
    name: str
    spec_json: str
    base_url: str = ""


class A2ADelegateBody(BaseModel):
    remote_name: str
    task_text: str
    assignee_role: str = "Backend"


class RagIndexBody(BaseModel):
    title: str
    content: str
    tags: str = ""


class SandboxBody(BaseModel):
    script: str
    by_role: str = "PM"


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


@app.get("/api/clis")
def get_clis():
    """Preflight: which agent CLIs are installed on PATH."""
    clis = spawn_util.get_cli_status()
    return {
        "clis": clis,
        "any_installed": any(c["installed"] for c in clis),
        "installed": [c["id"] for c in clis if c["installed"]],
    }


@app.get("/api/personas/divisions")
def get_divisions():
    idx = apex_v25._build_persona_index()
    divisions = set(meta.get("division", "unknown") for meta in idx.values())
    return {"divisions": sorted(list(divisions))}


@app.get("/api/personas/roles")
def get_roles(division: str = ""):
    idx = apex_v25._build_persona_index()
    if division:
        roles = [role for role, meta in idx.items() if meta.get("division") == division]
    else:
        roles = list(idx.keys())
    return {"roles": sorted(roles)}


@app.get("/api/spawn-status")
def get_spawn_status():
    state = tc._load()
    return {
        "current": state.get("spawn_status"),
        "history": state.get("spawn_history", [])[-10:],
    }


@app.get("/api/traces")
def get_traces(limit: int = 100, role: str = ""):
    return {
        "events": apex_trace.get_traces(limit=limit, role=role),
        "cost": apex_trace.trace_cost_summary(),
    }


@app.get("/api/gateway")
def get_gateway():
    state = tc._load()
    return {
        "targets": state.get("gateway_targets", []),
        "audit": state.get("gateway_audit", [])[-30:],
    }


@app.get("/api/a2a/card")
def get_a2a_card():
    return a2a_bridge.get_agent_card()


@app.get("/.well-known/agent.json")
def well_known_agent():
    return a2a_bridge.get_agent_card()


# ---------------------------------------------------------------------------
# POST / PATCH endpoints
# ---------------------------------------------------------------------------

@app.post("/api/tasks", status_code=201)
def add_task(body: AddTaskBody):
    apex_trace.log_trace("add_task", role=body.created_by or "Dashboard", detail=body.title)
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
    apex_trace.log_trace("update_task", role=body.by_role or "Dashboard", detail=f"#{task_id}")
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
    apex_trace.log_trace("post_message", role=body.sender_role, detail=body.text[:200])
    result = tc.post_message(
        sender_role=body.sender_role,
        text=body.text,
        mention=body.mention,
    )
    return {"message": result}


@app.post("/api/agents/join", status_code=201)
def join_team(body: JoinTeamBody):
    apex_trace.log_trace("join_team", role=body.role, detail=body.name or body.role)
    result = tc.join_team(role=body.role, name=body.name)
    return {"message": result}


@app.patch("/api/agents/{role}/status")
def set_status(role: str, body: SetStatusBody):
    apex_trace.log_trace("set_status", role=role, detail=body.status)
    result = tc.set_status(role=role, status=body.status)
    if "must be one of" in result:
        raise HTTPException(status_code=400, detail=result)
    return {"message": result}


@app.post("/api/facts")
def set_fact(body: SetFactBody):
    apex_trace.log_trace("set_fact", role=body.by_role or "Dashboard", detail=body.key)
    result = tc.set_fact(key=body.key, value=body.value, by_role=body.by_role)
    return {"message": result}


@app.post("/api/recovery")
def recover_tasks(body: RecoverBody = RecoverBody()):
    apex_trace.log_trace("recover_tasks", role=body.by_role, detail="crash recovery")
    result = tc.recover_tasks(stale_seconds=body.stale_seconds, by_role=body.by_role)
    return {"message": result}


@app.post("/api/launch", status_code=200)
def launch_team(body: LaunchBody):
    goal = body.goal.strip()
    if not goal:
        raise HTTPException(status_code=400, detail="goal is required")

    _VALID_MODES = {"ask", "same"}
    _VALID_CLIS = {"claude", "codex", "gemini", "cursor"}
    mode = body.mode if body.mode in _VALID_MODES else "ask"
    cli = body.cli.lower() if body.cli.lower() in _VALID_CLIS else "claude"
    auto_agents = bool(body.auto_agents)
    roles = [] if auto_agents else spawn_util.normalize_roles(body.roles if body.roles else ["Backend", "Frontend", "QA"])

    installed = spawn_util.available_clis()
    if mode == "same" and cli not in installed:
        raise HTTPException(
            status_code=400,
            detail=f"CLI '{cli}' is not on PATH. Installed: {', '.join(installed) or 'none'}",
        )

    here = os.path.dirname(os.path.abspath(__file__))
    project_dir = (
        os.path.abspath(os.path.expanduser(body.project_dir))
        if body.project_dir.strip()
        else here
    )
    os.makedirs(project_dir, exist_ok=True)

    mcp_clis = [cli]
    if mode == "ask":
        mcp_clis.extend(c for c in installed if c in {"claude", "codex"})
    mcp_setup = spawn_util.ensure_launch_mcp(mcp_clis, project_root=project_dir)

    seed = spawn_util.pm_seed(
        goal, project_dir, roles, cli, mode=mode, auto_agents=auto_agents,
    )
    pm_status = spawn_util.open_terminal_pm(cli, seed, project_dir)
    spawn_entries = [{
        "title": "APEX-PM",
        "role": "PM",
        "cli": cli,
        "message": pm_status,
        "status": "spawned" if "failed" not in pm_status.lower() else "failed",
    }]
    spawned = [e["title"] for e in spawn_entries]

    spawn_util.record_spawn_batch(spawn_entries, goal=goal, project_dir=project_dir)
    apex_trace.log_trace(
        "launch_team",
        role="Dashboard",
        detail=f"{len(spawned)} tab: {', '.join(spawned)}; PM will spawn workers",
        meta={"goal": goal[:100], "mode": mode, "cli": cli, "auto_agents": auto_agents, "roles": roles},
    )

    return {
        "message": f"{pm_status}; PM will choose and spawn workers" if auto_agents else f"{pm_status}; PM will spawn selected workers: {', '.join(roles)}",
        "project_dir": project_dir,
        "spawned": spawned,
        "spawn_details": spawn_entries,
        "clis_installed": installed,
        "mcp_setup": mcp_setup,
        "auto_agents": auto_agents,
        "planned_roles": roles,
    }


@app.post("/api/gateway/register")
def api_gateway_register(body: GatewayRegisterBody):
    msg = mcp_gateway.register_target(
        body.name, body.transport, body.command, body.url, body.description,
    )
    apex_trace.log_trace("gateway_register", detail=body.name)
    return {"message": msg}


@app.post("/api/gateway/call")
def api_gateway_call(body: GatewayCallBody):
    msg = mcp_gateway.gateway_call(body.target_name, body.tool_name, body.arguments_json)
    return {"message": msg}


@app.post("/api/gateway/openapi")
def api_gateway_openapi(body: OpenAPIImportBody):
    msg = mcp_gateway.openapi_import(body.name, body.spec_json, body.base_url)
    return {"message": msg}


@app.post("/api/a2a/publish")
def api_a2a_publish(name: str = "APEX-Team", description: str = ""):
    card = a2a_bridge.publish_agent_card(name=name, description=description)
    return {"message": "Agent Card published", "card": json.loads(card)}


@app.post("/api/a2a/delegate")
def api_a2a_delegate(body: A2ADelegateBody):
    msg = a2a_bridge.delegate_task(body.remote_name, body.task_text, body.assignee_role)
    return {"message": msg}


@app.post("/api/rag/index")
def api_rag_index(body: RagIndexBody):
    msg = apex_rag.index_document(body.title, body.content, body.tags)
    return {"message": msg}


@app.get("/api/rag/search")
def api_rag_search(q: str, limit: int = 5):
    return {"result": apex_rag.semantic_search(q, limit=limit)}


@app.post("/api/sandbox/run")
def api_sandbox_run(body: SandboxBody):
    msg = apex_rag.run_tool_script(body.script, body.by_role)
    apex_trace.log_trace("sandbox_run", role=body.by_role, detail=body.script[:100])
    return {"message": msg}


@app.websocket("/ws/updates")
async def ws_updates(ws: WebSocket):
    await _ws_manager.connect(ws)
    try:
        await ws.send_text(json.dumps(_build_snapshot(tc._load()), default=str))
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        _ws_manager.disconnect(ws)
    except Exception:
        _ws_manager.disconnect(ws)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8561, reload=False)
