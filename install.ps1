# APEX Team one-shot installer (Windows PowerShell)
$Here  = Split-Path -Parent $MyInvocation.MyCommand.Path
$State = Join-Path $Here "shared_state.json"
$Brain = Join-Path $Here "second_brain"
New-Item -ItemType Directory -Force -Path $Brain | Out-Null

Write-Host "Installing Python deps..."
python -m pip install -r (Join-Path $Here "requirements.txt")

if (Get-Command claude -ErrorAction SilentlyContinue) {
  Write-Host "Registering combined server with Claude Code (global)..."
  # Windows has no Unix `env` command — use claude -e for environment variables.
  claude mcp remove team -s user 2>$null
  claude mcp add team -s user `
    -e "TEAM_STATE_FILE=$State" `
    -e "BRAIN_DIR=$Brain" `
    -e "APEX_ANTIGRAVITY_DIR=$env:USERPROFILE\.gemini\antigravity\skills" `
    -e "APEX_CYBERSEC_DIR=$env:USERPROFILE\.gemini\cybersecurity-skills\skills" `
    -e "MAX_AGENTS=4" `
    -e "MSG_ROTATE_LIMIT=800" `
    -- python "$Here\apex_v25.py"
  Write-Host "Done. Verify: claude mcp list  (expect 'team', 81 tools)"
} else {
  Write-Host "WARNING: 'claude' not found. Register manually - see README." -ForegroundColor Yellow
}
Write-Host "`nLaunch the team:  python apex.py ""Build my project"""
