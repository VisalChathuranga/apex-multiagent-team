#!/usr/bin/env python3
"""Launch an agent CLI with a seed prompt read from a file (avoids Windows cmd quoting bugs)."""

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spawn_util  # noqa: E402

_CLI_NAMES = {
    "claude": "claude",
    "codex": "codex",
    "gemini": "gemini",
    "cursor": "cursor-agent",
}

_CLI_FALLBACKS = {
    "cursor": ["cursor-agent", "cursor"],
}

_STDIN_PROMPT_THRESHOLD = 6000


def _resolve_exe(cli: str) -> str:
    cli = (cli or "claude").lower().strip()
    names = [_CLI_NAMES.get(cli, cli)]
    names.extend(_CLI_FALLBACKS.get(cli, []))
    seen = set()
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        path = shutil.which(name)
        if path:
            return path
    raise FileNotFoundError(
        f"'{names[0]}' was not found on PATH. Install it, or pick another service "
        "(claude / codex / gemini / cursor-agent)."
    )


def _argv_prefix_from_template(cli: str, exe: str) -> list:
    """Parse APEX_CLI_* template flags (everything before {seed})."""
    tmpl = spawn_util._CLI_TEMPLATES.get(cli, spawn_util._CLI_TEMPLATES["claude"])
    if "{seed}" not in tmpl:
        prefix = tmpl.strip()
    else:
        prefix = tmpl.split("{seed}")[0].strip()
    if not prefix:
        return [exe]
    parts = shlex.split(prefix, posix=(sys.platform != "win32"))
    cmd_names = {cli, _CLI_NAMES.get(cli, ""), "cursor-agent", "cursor"}
    if parts and parts[0] in cmd_names:
        parts = parts[1:]
    return [exe] + parts


def _needs_shell(exe: str) -> bool:
    return sys.platform == "win32" and exe.lower().endswith((".cmd", ".bat", ".ps1"))


def _clean_env() -> dict:
    env = os.environ.copy()
    if env.get("TERM") == "dumb":
        env.pop("TERM", None)
    return env


def _run_cli(argv: list, seed: str, cli: str, use_stdin: bool) -> int:
    env = _clean_env()
    exe = argv[0] if argv else ""
    run_argv = argv + (["-"] if use_stdin and cli == "codex" else [])

    if use_stdin and cli == "codex":
        try:
            return subprocess.run(run_argv, input=seed, text=True, env=env).returncode
        except (OSError, FileNotFoundError):
            pass

    if _needs_shell(exe):
        cmdline = subprocess.list2cmdline(run_argv if use_stdin else argv + [seed])
        if use_stdin:
            return subprocess.run(cmdline, input=seed, text=True, shell=True, env=env).returncode
        return subprocess.call(cmdline, shell=True, env=env)

    try:
        if use_stdin:
            return subprocess.run(run_argv, input=seed, text=True, env=env).returncode
        return subprocess.call(argv + [seed], env=env)
    except OSError:
        if sys.platform != "win32":
            raise
        cmdline = subprocess.list2cmdline(run_argv if use_stdin else argv + [seed])
        if use_stdin:
            return subprocess.run(cmdline, input=seed, text=True, shell=True, env=env).returncode
        return subprocess.call(cmdline, shell=True, env=env)


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
    argv = _argv_prefix_from_template(cli, exe)

    use_stdin = len(seed) > _STDIN_PROMPT_THRESHOLD
    if cli == "codex" and _needs_shell(exe) and len(seed) > 400:
        use_stdin = True

    return _run_cli(argv, seed, cli, use_stdin)


if __name__ == "__main__":
    try:
        sys.exit(main() or 0)
    except FileNotFoundError as e:
        print(f"\n  ERROR: {e}\n", file=sys.stderr)
        sys.exit(1)
