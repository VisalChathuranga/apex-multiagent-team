#!/usr/bin/env bash
# APEX Team one-shot installer (macOS / Linux)
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
echo "▶ Installing Python deps…"
python3 -m pip install -r "$HERE/requirements.txt" || \
  python3 -m pip install --user -r "$HERE/requirements.txt"

STATE="$HERE/shared_state.json"
BRAIN="$HERE/second_brain"
mkdir -p "$BRAIN"

if command -v claude >/dev/null 2>&1; then
  echo "▶ Registering combined server with Claude Code (global)…"
  claude mcp add team -s user -- \
    env TEAM_STATE_FILE="$STATE" BRAIN_DIR="$BRAIN" \
        APEX_ANTIGRAVITY_DIR="$HOME/.gemini/antigravity/skills" \
        APEX_CYBERSEC_DIR="$HOME/.gemini/cybersecurity-skills/skills" \
        MAX_AGENTS=4 MSG_ROTATE_LIMIT=800 \
    python3 "$HERE/apex_v25.py" || echo "  (already registered? run 'claude mcp list')"
  echo "▶ Done. Verify: claude mcp list  (expect 'team', 81 tools)"
else
  echo "⚠ 'claude' not found. Register manually — see README."
fi

cat <<TXT

For Codex / Gemini / Cursor, add this server block (same TEAM_STATE_FILE!):
  command: python3
  args:    ["$HERE/apex_v25.py"]
  env:     { "TEAM_STATE_FILE": "$STATE", "BRAIN_DIR": "$BRAIN", "MAX_AGENTS": "4" }

Launch the team:   python3 apex.py "Build my project"
TXT
