"""A2A (Agent2Agent) bridge — Agent Card and task delegation stubs."""

from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Dict, List

import team_coordinator as tc

_A2A_VERSION = "1.0"


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def build_agent_card(
    name: str = "APEX-Team",
    description: str = "APEX autonomous multi-agent engineering team",
    project_dir: str = "",
) -> Dict[str, Any]:
    state = tc._load()
    roles = list(state.get("agents", {}).keys()) or ["PM", "Backend", "Frontend", "QA"]
    return {
        "name": name,
        "description": description,
        "version": _A2A_VERSION,
        "protocol": "a2a",
        "url": os.environ.get("APEX_A2A_URL", "http://localhost:8561/api/a2a"),
        "capabilities": {
            "streaming": True,
            "pushNotifications": False,
            "taskDelegation": True,
        },
        "skills": [
            {"id": r.lower(), "name": r, "description": f"APEX team role: {r}"}
            for r in roles
        ],
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
        "metadata": {
            "project_dir": project_dir or os.getcwd(),
            "mcp_server": "team",
            "updated": _now(),
        },
    }


def publish_agent_card(name: str = "APEX-Team", description: str = "") -> str:
    card = build_agent_card(name=name, description=description or build_agent_card()["description"])

    def op(state: dict) -> None:
        state["a2a_agent_card"] = card
        tc._log(state, "PM", "a2a agent card published")

    tc._mutate(op)
    return json.dumps(card, indent=2)


def get_agent_card() -> Dict[str, Any]:
    state = tc._load()
    return state.get("a2a_agent_card") or build_agent_card()


def register_remote_agent(card_json: str) -> str:
    try:
        card = json.loads(card_json)
    except json.JSONDecodeError as e:
        return f"Invalid Agent Card JSON: {e}"
    name = card.get("name") or "remote-agent"

    def op(state: dict) -> None:
        remotes: List[dict] = state.setdefault("a2a_remote_agents", [])
        remotes[:] = [r for r in remotes if r.get("name") != name]
        remotes.append({"name": name, "card": card, "registered_at": _now()})

    tc._mutate(op)
    return f"Remote A2A agent '{name}' registered."


def list_remote_agents() -> str:
    remotes = tc._load().get("a2a_remote_agents", [])
    if not remotes:
        return "No remote A2A agents. Use a2a_register_remote with an Agent Card JSON."
    lines = ["Remote A2A agents:"]
    for r in remotes:
        c = r.get("card") or {}
        lines.append(f"  • {r.get('name')}: {c.get('description', '')[:80]}")
    return "\n".join(lines)


def delegate_task(remote_name: str, task_text: str, assignee_role: str = "Backend") -> str:
    """Record an outbound A2A delegation and create a local board task."""
    remotes = {r["name"]: r for r in tc._load().get("a2a_remote_agents", [])}
    if remote_name not in remotes:
        return f"Unknown remote agent '{remote_name}'. Use a2a_list_remotes."

    task_id = str(uuid.uuid4())[:8]
    record = {
        "id": task_id,
        "remote": remote_name,
        "text": task_text[:2000],
        "time": _now(),
        "status": "delegated",
    }

    def op(state: dict) -> None:
        outbound: List[dict] = state.setdefault("a2a_outbound", [])
        outbound.append(record)
        tc._log(state, "PM", f"a2a delegate to {remote_name}: {task_text[:60]}")

    tc._mutate(op)
    tc.add_task(
        title=f"[A2A->{remote_name}] {task_text[:120]}",
        assignee=assignee_role,
        created_by="PM",
        priority="high",
    )
    card = remotes[remote_name].get("card") or {}
    endpoint = (card.get("url") or "unknown-endpoint")
    return (
        f"Delegated task {task_id} to '{remote_name}'. "
        f"Local board task created for {assignee_role}. "
        f"Send A2A message/send to {endpoint} with this payload (manual or HTTP client)."
    )
