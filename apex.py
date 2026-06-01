#!/usr/bin/env python3
"""
apex.py — the ONE command you run.

TWO COMMAND TYPES (the --mode flag, or the apex-ask / apex-same wrappers):

  • ASK  mode :  python apex.py --mode ask  "Build X"
        Each new agent terminal opens and ASKS you which service
        (claude / cursor / codex / gemini) to run for that agent. Mix freely.

  • SAME mode :  python apex.py --mode same --cli claude  "Build X"
        Every new agent terminal uses the SAME service you started the PM with.
        No questions — one CLI type for the whole team.

Open a terminal, run it, type your goal, and APEX opens the PM terminal; the PM
then spawns the worker terminals itself and the team builds the project.
"""

import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spawn_util  # noqa: E402

BANNER = r"""
   _   ___ _____  __  ___ ___   _   __  __
  /_\ | _ \ __\ \/ / |_   _| __| | |    |
 / _ \|  _/ _| >  <    | | | _|/ _ |  |||
/_/ \_\_| |___/_/\_\   |_| |___\__,_|_|_|
      autonomous multi-agent team
"""


def ask(prompt, default=""):
    sfx = f" [{default}]" if default else ""
    return input(f"  {prompt}{sfx}: ").strip() or default


def main():
    ap = argparse.ArgumentParser(description="APEX autonomous multi-agent launcher")
    ap.add_argument("goal", nargs="*", help="What to build (prompts if omitted)")
    ap.add_argument("--mode", choices=["same", "ask"], help="same = one CLI for all; ask = each terminal asks")
    ap.add_argument("--cli", help="PM CLI for SAME mode: claude|codex|gemini|cursor")
    ap.add_argument("--dir", help="Project directory")
    ap.add_argument("--roles", help="Comma-separated worker roles")
    ap.add_argument("--yes", action="store_true", help="Skip confirmation")
    args = ap.parse_args()

    print(BANNER)
    installed = spawn_util.available_clis()
    print("  Detected CLIs: " + (", ".join(installed) if installed
          else "none (install claude/codex/gemini/cursor-agent or set APEX_CLI_*)"))

    # mode
    mode = args.mode
    if not mode:
        m = ask("Command type — (1) ASK each terminal  /  (2) SAME cli for all", "1")
        mode = "ask" if m.strip() in ("1", "ask") else "same"

    goal = " ".join(args.goal).strip() or ask("What should the team build?")
    if not goal:
        print("  No goal given. Exiting."); return 1

    project_dir = args.dir or ask("Project directory", str(Path.cwd()))
    project_dir = os.path.abspath(os.path.expanduser(project_dir.strip()))
    if project_dir.lower() in ("yes", "y", "no", "n", "ok"):
        print("  That is not a folder path. Use e.g. D:\\my-app or press Enter for the default.")
        return 1
    Path(project_dir).mkdir(parents=True, exist_ok=True)

    default_cli = installed[0] if installed else "claude"
    # In SAME mode we need the CLI now (PM + all workers use it).
    # In ASK mode the PM still runs on some CLI; workers will be asked.
    cli = (args.cli or ask("PM CLI (claude/codex/gemini/cursor)", default_cli)).lower()

    roles_raw = args.roles or ask("Worker roles (comma-sep)", "Backend,Frontend,QA")
    roles = [r.strip() for r in roles_raw.split(",") if r.strip()]

    print("\n  ───────────── PLAN ─────────────")
    print(f"  Mode      : {mode.upper()}  " +
          ("(each terminal asks which service)" if mode == "ask"
           else f"(all agents use '{cli}')"))
    print(f"  Goal      : {goal}")
    print(f"  Directory : {project_dir}")
    print(f"  PM CLI    : {cli}")
    print(f"  Workers   : {', '.join(roles)}")
    print("  ────────────────────────────────\n")

    if not args.yes and ask("Launch the team? (y/n)", "y").lower() not in ("y", "yes"):
        print("  Cancelled."); return 0

    seed = spawn_util.pm_seed(goal, os.path.expanduser(project_dir), roles, cli, mode=mode)
    print("  Opening PM terminal …\n")
    project_dir = os.path.expanduser(project_dir)
    if sys.platform == "win32":
        status = spawn_util.open_terminal_pm(cli, seed, project_dir)
    else:
        cmd = spawn_util.cli_command(cli, seed, title="APEX-PM")
        status = spawn_util.open_terminal("APEX-PM", cmd, cwd=project_dir)
    print(f"  {status}")
    if mode == "ask":
        print("\n  ✔ PM will open worker terminals; each will ASK you which service to use.")
    else:
        print(f"\n  ✔ PM will open worker terminals, all running '{cli}'.")
    print("    Optional dashboard: in any agent run start_dashboard().")
    return 0


if __name__ == "__main__":
    sys.exit(main())
