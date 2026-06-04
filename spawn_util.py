#!/usr/bin/env python3
"""
spawn_util.py — cross-platform "open a new terminal and run a command",
plus the seed prompts and the per-terminal bootstrap command builder.

Used by apex.py (launcher) and apex_v25.py (in-conversation orchestrator).

Two spawn behaviours:
  • "same"  : every new terminal launches a fixed CLI (the one you started with)
  • "ask"   : each new terminal asks the user which service to use for THAT agent

Set APEX_SPAWN_DRYRUN=1 to print commands instead of opening terminals.
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

HERE = Path(__file__).resolve().parent

# CLI launch templates. {seed} is the bootstrap instruction passed to the agent.
# Override with env, e.g. APEX_CLI_CLAUDE="claude {seed}".
_CLI_TEMPLATES = {
    "claude": os.environ.get("APEX_CLI_CLAUDE", 'claude --dangerously-skip-permissions {seed}'),
    "codex":  os.environ.get("APEX_CLI_CODEX",  'codex {seed}'),
    "gemini": os.environ.get("APEX_CLI_GEMINI", 'gemini {seed}'),
    "cursor": os.environ.get("APEX_CLI_CURSOR", 'cursor-agent {seed}'),
}
_CLI_EXES = {"claude": "claude", "codex": "codex", "gemini": "gemini", "cursor": "cursor-agent"}

# Frontend dashboard role ids -> spawn / join_team names
_ROLE_ALIASES = {
    "backend": "Backend",
    "frontend": "Frontend",
    "tester": "Tester",
    "qa": "QA",
    "pm": "PM",
    "architect": "Architect",
    "analyst": "Analyst",
    "dba": "Dba",
    "ai-integrator": "Ai-Integrator",
    "reviewer": "Reviewer",
    "perf-tuner": "Perf-Tuner",
    "security-auditor": "Security-Auditor",
    "pen-tester": "Pen-Tester",
    "dfir-analyst": "Dfir-Analyst",
    "writer": "Writer",
    "devops": "DevOps",
}


def normalize_role(role: str) -> str:
    """Map UI ids (backend, tester) to stable team role names."""
    r = (role or "").strip()
    if not r:
        return r
    low = r.lower()
    if low in _ROLE_ALIASES:
        return _ROLE_ALIASES[low]
    if r == r.upper() or (r[0].isupper() and "-" not in r and "_" not in r):
        return r
    parts = r.replace("_", "-").split("-")
    return "-".join(p.capitalize() for p in parts)


def normalize_roles(roles: list) -> list:
    out = []
    for r in roles:
        nr = normalize_role(str(r))
        if nr and nr not in out:
            out.append(nr)
    return out or ["Backend", "Frontend", "QA"]


def _seed_dir() -> Path:
    d = HERE / "seeds"
    d.mkdir(exist_ok=True)
    return d


def _write_seed_file(title: str, seed: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)
    path = _seed_dir() / f"{safe}.txt"
    path.write_text(seed, encoding="utf-8")
    return path


def _quote_win(s: str) -> str:
    """Quote for cmd.exe."""
    if not s:
        return '""'
    if any(c in s for c in ' \t&|<>^()%!'):
        return '"' + s.replace('"', '\\"') + '"'
    return s


def _cmdline(argv: list) -> str:
    """Platform-correct command line for shell execution."""
    if sys.platform == "win32":
        return subprocess.list2cmdline(argv)
    return " ".join(shlex.quote(str(a)) for a in argv)


def _argv_launch_agent(cli: str, seed_path: Path, cwd: str = "") -> list:
    argv = [
        sys.executable or "python",
        str(HERE / "launch_agent.py"),
        "--cli", (cli or "claude").lower().strip(),
        "--seed-file", str(seed_path),
    ]
    if cwd:
        argv += ["--cwd", os.path.abspath(os.path.expanduser(cwd))]
    return argv


def _argv_agent_boot(role: str, project_dir: str, cli: str = "ask") -> list:
    argv = [
        sys.executable or "python",
        str(HERE / "agent_boot.py"),
        "--role", role,
        "--dir", os.path.abspath(os.path.expanduser(project_dir)),
    ]
    if cli and cli.lower() != "ask":
        argv += ["--cli", cli.lower().strip()]
    return argv


def cli_command(cli: str, seed: str, title: str = "agent") -> str:
    """Shell command that launches an agent CLI with a seed prompt."""
    cli = (cli or "claude").lower().strip()
    seed_path = _write_seed_file(title, seed)
    if sys.platform == "win32":
        return _cmdline(_argv_launch_agent(cli, seed_path))
    tmpl = _CLI_TEMPLATES.get(cli, _CLI_TEMPLATES["claude"])
    return tmpl.replace("{seed}", shlex.quote(seed))


def run_cli_with_seed(cli: str, seed: str, title: str = "agent", cwd: str = "") -> int:
    """Run agent CLI in-process (no shell), reading seed from a file on Windows."""
    cli = (cli or "claude").lower().strip()
    seed_path = _write_seed_file(title, seed)
    args = [
        sys.executable,
        str(HERE / "launch_agent.py"),
        "--cli", cli,
        "--seed-file", str(seed_path),
    ]
    if cwd:
        args += ["--cwd", os.path.abspath(os.path.expanduser(cwd))]
    if os.environ.get("APEX_SPAWN_DRYRUN") == "1":
        print(f"  [dry-run] {' '.join(args)}")
        return 0
    return subprocess.call(args)


def available_clis() -> list:
    """Which agent CLIs are installed on this machine."""
    return [cli for cli, exe in _CLI_EXES.items() if shutil.which(exe)]


def get_cli_status() -> List[Dict]:
    """Preflight: which CLIs are on PATH (for dashboard before launch)."""
    labels = {
        "claude": "Claude Code",
        "codex": "OpenAI Codex",
        "gemini": "Gemini CLI",
        "cursor": "Cursor Agent",
    }
    out = []
    for cli, exe in _CLI_EXES.items():
        path = shutil.which(exe)
        if cli == "cursor" and not path:
            path = shutil.which("cursor")
        out.append({
            "id": cli,
            "label": labels.get(cli, cli),
            "executable": exe,
            "installed": bool(path),
            "path": path or "",
        })
    return out


def record_spawn_batch(entries: List[Dict], goal: str = "", project_dir: str = "") -> None:
    """Persist last launch spawn results for dashboard spawn-health UI."""
    try:
        import team_coordinator as tc
        import time

        batch = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "goal": goal[:500],
            "project_dir": project_dir,
            "entries": entries,
        }

        def op(state: dict) -> None:
            state["spawn_status"] = batch
            history = state.setdefault("spawn_history", [])
            history.append(batch)
            if len(history) > 20:
                state["spawn_history"] = history[-20:]

        tc._mutate(op)
    except Exception:
        pass


# --------------------------------------------------------------------------
# Seed prompts
# --------------------------------------------------------------------------
def worker_seed(role: str, project_dir: str) -> str:
    rl = role.lower()
    return (
        f"You are the {role} agent on an APEX autonomous team. The MCP server "
        f"'team' is connected. Do this loop without asking me:\n"
        f"1) join_team('{role}') ; set_status('idle')\n"
        f"2) apex_persona('{rl}')  -- adopt this specialist behavior\n"
        f"3) load_summary() and get_facts()  -- cheap shared context\n"
        f"4) Repeat: view_board(my_role='{role}'); acknowledge new messages; if a "
        f"task is assigned to you, set_status('busy'), call check_conflicts first, "
        f"then apex_build_prompt('{rl}', <task title>) and DO the work in "
        f"{project_dir}; commit and git_link the task; update_task(status='done'); "
        f"post_message a short update; set_status('idle'). If nothing is assigned, "
        f"wait_for_message(...) and re-check.\n"
        f"5) On a milestone: save_summary(...) and set_fact(key, value).\n"
        f"6) If your context gets large, context_checkpoint then continue from the "
        f"summary (saves tokens).\n"
        f"Respect task dependencies (don't start blocked tasks). Stay in your file "
        f"scope, coordinate through the board, keep going until the board is clear. "
        f"Be concise to save tokens."
    )


def pm_seed(
    goal: str,
    project_dir: str,
    roles,
    cli: str,
    mode: str = "same",
    workers_pre_spawned: bool = False,
) -> str:
    norm = normalize_roles(list(roles))
    rolelist = ",".join(norm)
    if workers_pre_spawned:
        spawn_line = (
            f"Worker terminals are ALREADY open for: {rolelist}. "
            f"Do NOT call apex_orchestrate (would duplicate tabs). "
            f"Use view_board / metrics to confirm each role joined the team."
        )
    elif mode == "ask":
        spawn_line = (f"apex_orchestrate(goal=<goal>, project_dir='{project_dir}', "
                      f"roles='{rolelist}', mode='ask')  -- each new terminal will "
                      f"ASK the user which service (claude/cursor/codex) to use")
    else:
        spawn_line = (f"apex_orchestrate(goal=<goal>, project_dir='{project_dir}', "
                      f"roles='{rolelist}', cli='{cli}', mode='same')  -- all workers "
                      f"use '{cli}', same as you")
    return (
        f"You are the PM / team-lead of an APEX autonomous team. The MCP server "
        f"'team' is connected. The user's goal:\n\n  {goal}\n\n"
        f"Do this WITHOUT asking the user:\n"
        f"1) join_team('PM') ; apex_persona('team-lead') ; start_dashboard() so the "
        f"user can watch progress live\n"
        f"2) apex_detect_stack('{project_dir}')\n"
        f"3) {spawn_line}\n"
        f"4) Plan: break the goal into board tasks. Use add_task with priority and "
        f"depends_on so order is correct (e.g. backend API before frontend wiring). "
        f"set_skills for each agent, then auto_assign (or assign_work) so tasks go to "
        f"the skill-matched role. suggest_worktrees so agents don't collide in git. "
        f"post_message to kick off.\n"
        f"5) Monitor: view_board / metrics / wait_for_message. who_is_free -> assign "
        f"more. check_conflicts if agents overlap. If an agent goes silent: ping, "
        f"then recover_tasks and reassign. Debate only high-stakes calls (schema, "
        f"security, irreversible) -> proposals -> score_debate -> judge_debate. "
        f"Record decisions with set_fact / save_note.\n"
        f"6) When the board is clear: export_report, save_summary, and if WEBHOOK_URL "
        f"is set, webhook_notify 'project complete'. Tell the user it's done.\n"
        f"Keep everything lean (apex_build_prompt; context_checkpoint on long runs) "
        f"to save tokens."
    )


# --------------------------------------------------------------------------
# Bootstrap command: each spawned terminal runs agent_boot.py, which either
# uses a fixed --cli (same mode) or asks the user (ask mode).
# --------------------------------------------------------------------------
def agent_boot_command(role: str, project_dir: str, cli: str = "ask") -> str:
    return _cmdline(_argv_agent_boot(role, project_dir, cli=cli))


# --------------------------------------------------------------------------
# Open a NEW OS terminal that runs `command`
# --------------------------------------------------------------------------
def open_terminal(title: str, command: str, cwd: str = "") -> str:
    """Open a new OS terminal. On Windows, prefer argv-based spawn when possible."""
    abscwd = os.path.abspath(os.path.expanduser(cwd)) if cwd else ""
    if os.environ.get("APEX_SPAWN_DRYRUN") == "1":
        return f"[dry-run] {title}: cwd={abscwd or HERE} cmd={command}"

    plat = sys.platform
    try:
        if plat == "win32":
            workdir = abscwd or str(HERE)
            inner = f"cd /d {_quote_win(workdir)} && {command}"
            if shutil.which("wt"):
                subprocess.Popen(
                    ["wt", "-w", "0", "new-tab", "--title", title, "-d", workdir,
                     "cmd", "/k", inner],
                    shell=False,
                )
            else:
                subprocess.Popen(
                    f'start "{title}" cmd /k "{inner}"',
                    shell=True,
                )
            return f"spawned (windows): {title}"
        cd = f'cd {shlex.quote(cwd)} && ' if cwd else ""
        full = cd + command
        if plat == "darwin":
            script = f'tell application "Terminal" to do script "{full.replace(chr(34), chr(92)+chr(34))}"'
            subprocess.Popen(["osascript", "-e", script])
            subprocess.Popen(["osascript", "-e", 'tell application "Terminal" to activate'])
            return f"spawned (macOS): {title}"
        else:
            keep = f"{full}; echo; echo '[APEX] agent exited -- press Enter to close'; read"
            if shutil.which("gnome-terminal"):
                subprocess.Popen(["gnome-terminal", f"--title={title}", "--", "bash", "-lc", keep])
            elif shutil.which("konsole"):
                subprocess.Popen(["konsole", "--new-tab", "-p", f"tabtitle={title}", "-e", "bash", "-lc", keep])
            elif shutil.which("xterm"):
                subprocess.Popen(["xterm", "-T", title, "-e", "bash", "-lc", keep])
            elif shutil.which("tmux"):
                subprocess.Popen(["tmux", "new-window", "-n", title, keep])
            else:
                return f"[no terminal emulator found] run this manually:\n  {full}"
            return f"spawned (linux): {title}"
    except Exception as e:
        return f"[spawn failed for {title}: {e}] run manually:\n  {command}"


def spawn_team_workers(
    roles: list,
    project_dir: str,
    mode: str = "same",
    cli: str = "claude",
    clis: str = "",
) -> List[Dict]:
    """Open one terminal tab per worker role. Returns spawn results for API/UI."""
    role_list = normalize_roles(roles)
    cli_list = [c.strip().lower() for c in clis.split(",") if c.strip()]
    mode = (mode or "same").lower()
    cli = (cli or "claude").lower().strip()
    project_dir = os.path.abspath(os.path.expanduser(project_dir))
    results = []

    for i, role in enumerate(role_list):
        if i < len(cli_list):
            use = cli_list[i]
        elif mode == "ask":
            use = "ask"
        else:
            use = cli
        title = f"APEX-{role}"
        if sys.platform == "win32":
            res = open_terminal_boot(title, role, project_dir, cli=use)
        else:
            boot = agent_boot_command(role, project_dir, cli=use)
            res = open_terminal(title, boot, cwd=project_dir)
        shown = "ask-on-open" if use == "ask" else use
        ok = "failed" not in res.lower() and "error" not in res.lower()[:20]
        results.append({
            "title": title,
            "role": role,
            "cli": shown,
            "message": res,
            "status": "spawned" if ok else "failed",
        })
    return results


def open_terminal_boot(title: str, role: str, project_dir: str, cli: str = "ask") -> str:
    """Spawn a worker terminal running agent_boot.py (Windows-safe)."""
    workdir = os.path.abspath(os.path.expanduser(project_dir))
    argv = _argv_agent_boot(role, workdir, cli=cli)
    if os.environ.get("APEX_SPAWN_DRYRUN") == "1":
        return f"[dry-run] {title}: {_cmdline(argv)}"
    return _open_terminal_argv(title, argv, workdir)


def open_terminal_pm(cli: str, seed: str, cwd: str) -> str:
    """Spawn the PM terminal running launch_agent.py (Windows-safe)."""
    workdir = os.path.abspath(os.path.expanduser(cwd))
    cli = (cli or "claude").lower().strip()
    seed_path = _write_seed_file("APEX-PM", seed)
    argv = _argv_launch_agent(cli, seed_path, cwd=workdir)
    if os.environ.get("APEX_SPAWN_DRYRUN") == "1":
        return f"[dry-run] APEX-PM: {_cmdline(argv)}"
    return _open_terminal_argv("APEX-PM", argv, workdir)


def _open_terminal_argv(title: str, argv: list, cwd: str) -> str:
    """Open terminal running argv directly (no cmd quoting bugs)."""
    try:
        if shutil.which("wt"):
            subprocess.Popen(
                ["wt", "-w", "0", "new-tab", "--title", title, "-d", cwd] + argv,
                shell=False,
            )
        else:
            cmdline = _cmdline(argv)
            subprocess.Popen(
                f'start "{title}" cmd /k "cd /d {_quote_win(cwd)} && {cmdline}"',
                shell=True,
            )
        return f"spawned (windows): {title}"
    except Exception as e:
        return f"[spawn failed for {title}: {e}] run manually in {cwd}:\n  {_cmdline(argv)}"
