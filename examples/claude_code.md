# Claude Code — register the APEX combined server

Replace /ABS/PATH with your apex-team folder (use the real absolute path).

```bash
claude mcp add team -s user -- \
  env TEAM_STATE_FILE=/ABS/PATH/apex-team/shared_state.json \
      BRAIN_DIR=/ABS/PATH/apex-team/second_brain \
      APEX_ANTIGRAVITY_DIR=$HOME/.gemini/antigravity/skills \
      APEX_CYBERSEC_DIR=$HOME/.gemini/cybersecurity-skills/skills \
      MAX_AGENTS=4 MSG_ROTATE_LIMIT=800 \
  python /ABS/PATH/apex-team/apex_v25.py
claude mcp list   # expect "team" with 81 tools
```
Windows: use %USERPROFILE% and back-slashed paths, e.g. C:\apex-team\apex_v25.py
