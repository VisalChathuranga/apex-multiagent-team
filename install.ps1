# APEX Team one-shot installer (Windows PowerShell)
$Here  = Split-Path -Parent $MyInvocation.MyCommand.Path
$State = Join-Path $Here "shared_state.json"
$Brain = Join-Path $Here "second_brain"
New-Item -ItemType Directory -Force -Path $Brain | Out-Null

function Resolve-ApexPython {
  $candidates = @()
  if (Get-Command where.exe -ErrorAction SilentlyContinue) {
    foreach ($path in (& where.exe python 2>$null)) {
      if ($path -and (Test-Path $path)) {
        $candidates += @(@($path))
      }
    }
  }
  if (Get-Command py -ErrorAction SilentlyContinue) {
    $candidates += @(@("py", "-3.12"), @("py", "-3.11"))
  }
  if (Get-Command python -ErrorAction SilentlyContinue) {
    $candidates += @(@("python"))
  }

  foreach ($candidate in $candidates) {
    $cmd = $candidate[0]
    $args = @()
    if ($candidate.Count -gt 1) {
      $args += $candidate[1]
    }
    $args += @("-c", "import sys, mcp, fastapi, filelock; print(sys.executable)")
    try {
      $exe = (& $cmd @args 2>$null | Select-Object -First 1).Trim()
      if ($exe) {
        return $exe
      }
    } catch {}
  }

  foreach ($candidate in $candidates) {
    $cmd = $candidate[0]
    $args = @()
    if ($candidate.Count -gt 1) {
      $args += $candidate[1]
    }
    $args += @("-c", "import sys; print(sys.executable)")
    try {
      $exe = (& $cmd @args 2>$null | Select-Object -First 1).Trim()
      if ($exe) {
        return $exe
      }
    } catch {}
  }

  throw "No usable Python interpreter found. Install Python 3.11 or 3.12."
}

$PythonExe = Resolve-ApexPython

Write-Host "Using Python: $PythonExe"
Write-Host "Installing Python deps..."
& $PythonExe -m pip install -r (Join-Path $Here "requirements.txt")

$McpEnv = @{
  TEAM_STATE_FILE = $State
  BRAIN_DIR = $Brain
  APEX_ANTIGRAVITY_DIR = "$env:USERPROFILE\.gemini\antigravity\skills"
  APEX_CYBERSEC_DIR = "$env:USERPROFILE\.gemini\cybersecurity-skills\skills"
  MAX_AGENTS = "4"
  MSG_ROTATE_LIMIT = "800"
}

if (Get-Command claude -ErrorAction SilentlyContinue) {
  Write-Host "Registering combined server with Claude Code (global)..."
  claude mcp remove team -s user 2>$null
  claude mcp add team -s user `
    -e "TEAM_STATE_FILE=$($McpEnv.TEAM_STATE_FILE)" `
    -e "BRAIN_DIR=$($McpEnv.BRAIN_DIR)" `
    -e "APEX_ANTIGRAVITY_DIR=$($McpEnv.APEX_ANTIGRAVITY_DIR)" `
    -e "APEX_CYBERSEC_DIR=$($McpEnv.APEX_CYBERSEC_DIR)" `
    -e "MAX_AGENTS=$($McpEnv.MAX_AGENTS)" `
    -e "MSG_ROTATE_LIMIT=$($McpEnv.MSG_ROTATE_LIMIT)" `
    -- "$PythonExe" "$Here\apex_v25.py"
  Write-Host "Done. Verify: claude mcp list  (expect 'team', 81 tools)"
} else {
  Write-Host "WARNING: 'claude' not found. Register manually - see README." -ForegroundColor Yellow
}

if (Get-Command codex -ErrorAction SilentlyContinue) {
  Write-Host "Registering combined server with Codex..."
  codex mcp remove team 2>$null
  codex mcp add team `
    --env "TEAM_STATE_FILE=$($McpEnv.TEAM_STATE_FILE)" `
    --env "BRAIN_DIR=$($McpEnv.BRAIN_DIR)" `
    --env "APEX_ANTIGRAVITY_DIR=$($McpEnv.APEX_ANTIGRAVITY_DIR)" `
    --env "APEX_CYBERSEC_DIR=$($McpEnv.APEX_CYBERSEC_DIR)" `
    --env "MAX_AGENTS=$($McpEnv.MAX_AGENTS)" `
    --env "MSG_ROTATE_LIMIT=$($McpEnv.MSG_ROTATE_LIMIT)" `
    -- "$PythonExe" "$Here\apex_v25.py"
  Write-Host "Done. Verify: codex mcp list  (expect 'team')"
} else {
  Write-Host "WARNING: 'codex' not found. Install @openai/codex or pick another CLI." -ForegroundColor Yellow
}

Write-Host "`nLaunch the team:  python apex.py ""Build my project"""
