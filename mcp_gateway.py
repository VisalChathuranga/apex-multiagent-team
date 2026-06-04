"""MCP Hub / Gateway — register downstream MCP targets and OpenAPI specs."""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List

import team_coordinator as tc

HERE = Path(__file__).resolve().parent
ADAPTERS_DIR = HERE / "gateway_adapters"


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def list_targets() -> List[Dict[str, Any]]:
    return tc._load().get("gateway_targets", [])


def register_target(
    name: str,
    transport: str = "stdio",
    command: str = "",
    url: str = "",
    description: str = "",
) -> str:
    name = (name or "").strip()
    if not name:
        return "Error: name is required."
    entry = {
        "name": name,
        "transport": transport,
        "command": command,
        "url": url,
        "description": description,
        "registered_at": _now(),
        "status": "registered",
    }

    def op(state: dict) -> None:
        targets: List[dict] = state.setdefault("gateway_targets", [])
        targets[:] = [t for t in targets if t.get("name") != name]
        targets.append(entry)
        tc._log(state, "PM", f"gateway registered: {name}")

    tc._mutate(op)
    return f"Gateway target '{name}' registered ({transport})."


def remove_target(name: str) -> str:
    def op(state: dict) -> None:
        targets = state.setdefault("gateway_targets", [])
        state["gateway_targets"] = [t for t in targets if t.get("name") != name]

    tc._mutate(op)
    return f"Removed gateway target '{name}' (if it existed)."


def gateway_capabilities() -> str:
    targets = list_targets()
    if not targets:
        return "No gateway targets registered. Use gateway_register or gateway_openapi_import."
    lines = [f"Gateway targets ({len(targets)}):"]
    for t in targets:
        lines.append(
            f"  • {t.get('name')}: {t.get('transport')} — {t.get('description') or t.get('command') or t.get('url')}"
        )
    return "\n".join(lines)


def gateway_call(target_name: str, tool_name: str, arguments_json: str = "{}") -> str:
    """Route a call to a registered target (audit + stub execution)."""
    targets = {t["name"]: t for t in list_targets()}
    if target_name not in targets:
        return f"Unknown target '{target_name}'. Use gateway_capabilities."

    try:
        args = json.loads(arguments_json or "{}")
    except json.JSONDecodeError as e:
        return f"Invalid arguments_json: {e}"

    audit = {
        "time": _now(),
        "target": target_name,
        "tool": tool_name,
        "args_keys": list(args.keys()) if isinstance(args, dict) else [],
        "status": "routed",
    }

    def op(state: dict) -> None:
        log = state.setdefault("gateway_audit", [])
        log.append(audit)
        if len(log) > 200:
            state["gateway_audit"] = log[-200:]
        tc._log(state, "PM", f"gateway_call {target_name}.{tool_name}")

    tc._mutate(op)
    t = targets[target_name]
    return (
        f"[gateway] Routed {target_name}.{tool_name} "
        f"(transport={t.get('transport')}). "
        f"Connect MCP client to this target's command/url to execute. "
        f"Args: {json.dumps(args)[:500]}"
    )


def _parse_openapi_paths(spec: dict) -> List[dict]:
    paths = spec.get("paths") or {}
    tools = []
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, detail in methods.items():
            if method.lower() not in ("get", "post", "put", "patch", "delete"):
                continue
            if not isinstance(detail, dict):
                continue
            op_id = detail.get("operationId") or f"{method}_{path}".replace("/", "_").strip("_")
            tools.append({
                "name": op_id[:80],
                "method": method.upper(),
                "path": path,
                "summary": (detail.get("summary") or "")[:200],
            })
    return tools


def openapi_import(name: str, spec_json: str, base_url: str = "") -> str:
    """Register an OpenAPI spec as a gateway target and write a stub adapter file."""
    name = (name or "").strip()
    if not name:
        return "Error: name is required."
    try:
        spec = json.loads(spec_json)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"

    tools = _parse_openapi_paths(spec)
    ADAPTERS_DIR.mkdir(exist_ok=True)
    safe = re.sub(r"[^\w\-]", "_", name)
    adapter_path = ADAPTERS_DIR / f"{safe}_openapi.json"
    adapter_path.write_text(
        json.dumps({"name": name, "base_url": base_url, "tools": tools}, indent=2),
        encoding="utf-8",
    )

    desc = f"OpenAPI adapter ({len(tools)} operations) -> {adapter_path.name}"
    register_target(
        name=name,
        transport="openapi",
        command=str(adapter_path),
        url=base_url,
        description=desc,
    )
    return f"Imported OpenAPI as '{name}': {len(tools)} tools. Adapter: {adapter_path}"
