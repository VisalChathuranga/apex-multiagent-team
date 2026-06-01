#!/usr/bin/env python3
"""Launch an agent CLI with a seed prompt read from a file (avoids Windows cmd quoting bugs)."""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

_CLI_NAMES = {
    "claude": "claude",
    "codex": "codex",
    "gemini": "gemini",
    "cursor": "cursor-agent",
}

_CLI_ARGS = {
    "claude": ["--dangerously-skip-permissions"],
    "codex": [],
    "gemini": [],
    "cursor": [],
}

# Above this length, pass prompt via stdin (Windows argv limit / .cmd wrappers).
_STDIN_PROMPT_THRESHOLD = 6000


def _resolve_exe(cli: str) -> str:
    name = _CLI_NAMES.get(cli, cli)
    path = shutil.which(name)
    if not path:
        raise FileNotFoundError(
            f"'{name}' was not found on PATH. Install it, or pick another service (claude/codex/gemini/cursor)."
        )
    return path


def _run(argv: list, seed: str, use_stdin: bool) -> int:
    env = os.environ.copy()
    if env.get("TERM") == "dumb":
        env.pop("TERM", None)
    if use_stdin:
        return subprocess.run(
            argv,
            input=seed,
            text=True,
            env=env,
        ).returncode
    return subprocess.call(argv + [seed], env=env)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli", required=True)
    ap.add_argument("--seed-file", required=True)
    ap.add_argument("--cwd", default="")
    args = ap.parse_args()

    if args.cwd:
        try:
            os.chdir(os.path.expanduser(args.cwd))
        except OSError:
            pass

    seed_path = Path(args.seed_file)
    seed = seed_path.read_text(encoding="utf-8")
    cli = (args.cli or "claude").lower().strip()
    exe = _resolve_exe(cli)
    extra = list(_CLI_ARGS.get(cli, _CLI_ARGS["claude"]))
    argv = [exe] + extra

    use_stdin = len(seed) > _STDIN_PROMPT_THRESHOLD

    try:
        return _run(argv, seed, use_stdin)
    except FileNotFoundError:
        raise
    except OSError as e:
        if sys.platform != "win32":
            raise
        # Fallback: .cmd wrappers via shell
        cmdline = subprocess.list2cmdline(argv + ([] if use_stdin else [seed]))
        env = os.environ.copy()
        if env.get("TERM") == "dumb":
            env.pop("TERM", None)
        if use_stdin:
            return subprocess.run(
                cmdline,
                input=seed,
                text=True,
                shell=True,
                env=env,
            ).returncode
        return subprocess.call(cmdline, shell=True, env=env)


if __name__ == "__main__":
    try:
        sys.exit(main() or 0)
    except FileNotFoundError as e:
        print(f"\n  ERROR: {e}\n", file=sys.stderr)
        sys.exit(1)
