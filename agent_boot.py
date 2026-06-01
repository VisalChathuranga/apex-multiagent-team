#!/usr/bin/env python3
"""
agent_boot.py — runs INSIDE each freshly-opened agent terminal.

• "same" mode  : called with --cli <name> → launches that CLI immediately.
• "ask" mode   : called WITHOUT --cli → asks the user, in THIS terminal,
                 which service (claude / cursor / codex / gemini) to use for
                 this specific agent, then launches it.

Either way it then hands control to the chosen CLI (in the same window) with
the role's bootstrap prompt so the agent auto-joins the shared team.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spawn_util  # noqa: E402


def choose_cli(role: str) -> str:
    installed = spawn_util.available_clis()
    options = installed or ["claude", "codex", "cursor", "gemini"]
    print("\n" + "=" * 52)
    print(f"  APEX — new agent terminal:  {role}")
    print("=" * 52)
    if installed:
        print("  Installed services: " + ", ".join(installed))
    else:
        print("  (none detected on PATH — type one anyway, or fix PATH)")
    print("  Which service should run the " + role + " agent?")
    for i, c in enumerate(options, 1):
        print(f"    {i}) {c}")
    while True:
        ans = input("  choice (number or name): ").strip().lower()
        if not ans:
            return options[0]
        if ans.isdigit() and 1 <= int(ans) <= len(options):
            return options[int(ans) - 1]
        if ans in ("claude", "codex", "cursor", "gemini"):
            return ans
        print("  ? try a listed number or name (claude/codex/cursor/gemini)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", required=True)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--cli", default="")   # empty = ask mode
    args = ap.parse_args()

    project_dir = os.path.expanduser(args.dir)
    Path(project_dir).mkdir(parents=True, exist_ok=True)
    try:
        os.chdir(project_dir)
    except Exception:
        pass

    cli = args.cli.strip().lower() or choose_cli(args.role)
    seed = spawn_util.worker_seed(args.role, project_dir)
    title = f"APEX-{args.role}"

    print(f"\n  → launching {args.role} on '{cli}' …\n")
    return spawn_util.run_cli_with_seed(cli, seed, title=title, cwd=project_dir)


if __name__ == "__main__":
    sys.exit(main())
