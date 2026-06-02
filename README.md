<div align="center">

```
   _   ___ _____  __  ___ ___   _   __  __
  /_\ | _ \ __\ \/ / |_   _| __| | |    |
 / _ \|  _/ _| >  <    | | | _|/ _ |  |||
/_/ \_\_| |___/_/\_\   |_| |___\__,_|_|_|
```

# APEX Team

### Autonomous Multi-Agent AI Orchestrator

**Open one terminal. Say what you want built. A full team of AI agents plans, codes, tests, and ships it — together.**

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat-square&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MCP](https://img.shields.io/badge/MCP-81%20tools-orange?style=flat-square)](https://github.com/anthropics/mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue?style=flat-square)]()

</div>

---

## What is APEX?

APEX is a **self-coordinating AI team system**. You describe a goal; APEX opens a Project Manager terminal that automatically spawns specialist agent terminals (Backend, Frontend, QA, DevOps, etc.), divides the work, and drives the whole team to completion — without further input from you.

```
you  ──▶  python apex.py  ──▶  PM terminal opens
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                       ▼
       APEX-Backend           APEX-Frontend            APEX-QA
       (claude)               (codex)                  (cursor)
              └──────── shared_state.json ────────────────┘
                   channel · board · debate · memory
```

Every agent shares one file-locked state file — they post messages, pick up tasks, debate high-stakes decisions, and report progress in real time through the **live web dashboard**.

---

## ✨ Features

| | |
|---|---|
| 🚀 **One-command launch** | `python apex.py` or use the web UI — type a goal and the team self-assembles |
| 🤖 **14 specialist agents** | architect, analyst, backend, frontend, DBA, AI integrator, tester, reviewer, perf-tuner, security auditor, pen tester, DFIR analyst, writer, devops |
| 🔀 **Any CLI mix** | Claude Code, Codex CLI, Gemini CLI, Cursor — agents can each run on a different service |
| 🛠 **81 MCP tools** | 73 coordination tools + 8 APEX intelligence tools, served on one MCP server |
| 🧠 **Per-agent intelligence** | Skill routing over 2 195+ skills, cached framework-correct prompts, 17 specialist personas |
| 📊 **Live dashboard** | Next.js web UI: task board, chat feed, agent roster, metrics, one-click team launch |
| 💬 **Structured debate** | Propose → critique → revise → vote → judge — gated to high-stakes decisions only |
| 💾 **Token-efficient** | Compact shared summary reload; padding-stripped cached prompts; rotation limits |
| 🔄 **Crash recovery** | PM pings silent agents, recovers stale tasks, auto-backups every 15 writes |
| 🔗 **Git-safe** | Per-agent worktrees, conflict detection, task-to-commit linking |
| 📣 **Completion webhook** | Slack / Discord / Teams notify when the board clears |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         APEX System                             │
│                                                                 │
│   ┌──────────────┐    REST/WS    ┌──────────────────────────┐  │
│   │  Next.js     │◀────────────▶│  FastAPI  api_server.py   │  │
│   │  Dashboard   │              │  POST /api/launch          │  │
│   │  :8562       │              │  GET  /api/state           │  │
│   └──────────────┘              │  WS   /ws/updates          │  │
│                                 └────────────┬─────────────┘  │
│                                              │                  │
│                                     spawn_util.py               │
│                                              │                  │
│              ┌───────────────────────────────▼──────────────┐  │
│              │            apex_v25.py  (MCP server)          │  │
│              │   81 tools: coordination + APEX intelligence   │  │
│              │   team_coordinator.py (base 73 tools)          │  │
│              └──────────────────┬────────────────────────────┘  │
│                                 │  shared_state.json             │
│         ┌───────────────────────┼────────────────────┐          │
│         ▼                       ▼                     ▼          │
│   ┌───────────┐          ┌────────────┐        ┌──────────┐     │
│   │ APEX-PM   │          │ APEX-Agent │  ···   │ APEX-Agent│     │
│   │ (any CLI) │          │ (any CLI)  │        │ (any CLI) │     │
│   └───────────┘          └────────────┘        └──────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

| Layer | What it does |
|---|---|
| **L0 — Token discipline** | Budget directive injected per task via `apex_token_budget` |
| **L1 — Shared brain** | Write-once decisions; agents reload a compact summary (the main token saver) |
| **L2 — Intelligence** | 2 195+ skill routing + framework-correct, padding-free, hash-cached prompts |
| **L3 — Coordination** | Live channel, task board, gated debate, auto-spawn, crash recovery |

---

## 📋 Prerequisites

Before installing, make sure you have:

- **Python 3.8 or newer** — [download](https://python.org/downloads)
- **Node.js 18+** — [download](https://nodejs.org) *(for the web dashboard)*
- **At least one agent CLI** installed and on your PATH:

| CLI | Install |
|---|---|
| [Claude Code](https://claude.ai/code) | Follow Anthropic's install guide |
| Codex CLI | `npm install -g @openai/codex` |
| Gemini CLI | `npm install -g @google/gemini-cli` |
| Cursor Agent | Install from [cursor.sh](https://cursor.sh) |

> You only need **one** CLI to get started. You can mix them later.

---

## 🚀 Installation

### 1 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/apex-team.git
cd apex-team
```

### 2 — Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3 — Register the MCP server

**macOS / Linux:**
```bash
bash install.sh
```

**Windows (PowerShell):**
```powershell
./install.ps1
```

The installer registers `apex_v25.py` globally with Claude Code and prints the config snippets for Codex / Gemini / Cursor.

**Verify the registration worked:**
```bash
claude mcp list
# you should see "team" with 81 tools
```

<details>
<summary>Manual registration (if you skip the installer)</summary>

```bash
claude mcp add team -s user -- \
  env TEAM_STATE_FILE="$PWD/shared_state.json" \
      BRAIN_DIR="$PWD/second_brain" \
      APEX_ANTIGRAVITY_DIR="$HOME/.gemini/antigravity/skills" \
      APEX_CYBERSEC_DIR="$HOME/.gemini/cybersecurity-skills/skills" \
      MAX_AGENTS=4 MSG_ROTATE_LIMIT=800 \
  python "$PWD/apex_v25.py"
```

Restart your CLI client after registering. For Codex / Cursor / Gemini, copy the ready-made config blocks from `examples/` into each client's config — just replace `/ABS/PATH`.

</details>

<details>
<summary>Optional — install skill libraries for full skill routing</summary>

```bash
npx antigravity-awesome-skills          # → ~/.gemini/antigravity/skills
git clone https://github.com/mukul975/Anthropic-Cybersecurity-Skills.git \
  ~/.gemini/cybersecurity-skills
```

Without these, APEX falls back to a built-in keyword map — still fully functional.

</details>

### 4 — Set up the web dashboard

```bash
cd frontend
npm install
npm run dev        # starts at http://localhost:8562
```

In a second terminal, start the API server:
```bash
# from the apex-team root
uvicorn api_server:app --host 0.0.0.0 --port 8561 --reload
```

---

## ▶️ Usage

### Option A — Web Dashboard (recommended)

1. Open **http://localhost:8562** in your browser
2. Click **Launch Team** in the top-right corner
3. Fill in the wizard:
   - **Goal** — describe what you want built
   - **Mode** — ASK (each terminal asks which CLI) or SAME (all use one CLI)
   - **CLI tool** — claude / codex / gemini / cursor
   - **Project directory** — where to build (blank = current dir)
   - **Agents** — tick the checkboxes for the specialists you need
4. Click **Launch** — the PM terminal opens and the team self-assembles

![Dashboard screenshot placeholder](https://via.placeholder.com/800x400/1a1a2e/ffffff?text=APEX+Team+Dashboard)

### Option B — Terminal

**ASK mode** — each agent terminal asks which CLI to use (mix freely):
```bash
# macOS / Linux
./apex-ask.sh "Build a REST API with user auth and a React dashboard"

# Windows
apex-ask.bat "Build a REST API with user auth and a React dashboard"

# or directly
python apex.py --mode ask "Build a REST API with user auth and a React dashboard"
```

**SAME mode** — all agents use one CLI (no prompts):
```bash
./apex-same.sh --cli claude "Build a REST API with user auth and a React dashboard"

# Windows
apex-same.bat --cli claude "..."

python apex.py --mode same --cli claude "..."
```

**Interactive mode** — step-by-step prompts:
```bash
python apex.py
#  Command type — (1) ASK / (2) SAME : 1
#  What should the team build?       : Build a billing system
#  Project directory                 : ./my-project
#  PM CLI                            : claude
#  Worker roles                      : Backend,Frontend,QA
```

### What happens automatically

```
1. PM terminal opens on your chosen CLI
2. PM joins the team, detects the stack, calls apex_orchestrate()
3. apex_orchestrate() opens one terminal per agent role
4. Every agent auto-joins the shared team, reads the goal, works the board
5. PM assigns tasks (by skill), monitors progress, runs debates on hard calls
6. When the board clears: export_report, webhook_notify "project complete"
```

---

## 🤖 Available Agents

Select any combination when launching:

| Agent | Specialisation |
|---|---|
| `architect` | C4 diagrams, ADRs, system design, tech-stack decisions |
| `analyst` | User stories, acceptance criteria, MVP scope |
| `backend` | APIs & server logic — Node / Go / Python / Rust / .NET |
| `frontend` | UI & components — Next.js, React, Vue, SvelteKit, Astro |
| `dba` | Schemas, migrations, indexes, query optimisation |
| `ai-integrator` | LLM / RAG pipelines, vector stores, AI service clients |
| `tester` | Unit, integration & E2E — pytest / jest / Playwright |
| `reviewer` | Code review — SOLID, DRY, readability, refactor suggestions |
| `perf-tuner` | Profiling, latency, N+1 hunting, bundle-size triage |
| `security-auditor` | OWASP Top 10, CVEs, weak auth/crypto, secrets — read-only |
| `pen-tester` | Offensive testing, exploit validation — read-only |
| `dfir-analyst` | Incident response, log analysis, Sigma / YARA detection rules |
| `writer` | README, CHANGELOG, API docs, release notes |
| `devops` | CI/CD pipelines, Dockerfiles, GitHub Actions, Vercel / AWS |

---

## 🧰 APEX Intelligence Tools (8)

| Tool | What it does |
|---|---|
| `apex_orchestrate` | Record goal + spawn the full worker team in one call |
| `apex_spawn` | Open new terminal(s) for any role on any CLI, auto-joining the team |
| `apex_build_prompt` ★ | Budget + shared context + persona + skills → optimised, cached prompt |
| `apex_recommend_skills` | Scan 2 195+ skill catalogs; pick ≤ 5 for a role + task |
| `apex_persona` | Specialist body + prompting framework for a given role |
| `apex_detect_stack` | Polyglot stack detection (Next.js-priority frontend + backend lang) |
| `apex_token_budget` | L0 budget directive for a task |
| `apex_status` | Show loaded catalogs, active personas, cache stats |

Plus **73 base coordination tools**: `join_team`, `post_message`, `wait_for_message`, `add_task`, `assign_work`, `view_board`, `start_debate` / `judge_debate`, `save_summary` / `load_summary`, `report_finding`, `brain_add`, `start_dashboard`, `export_report`, … See `FEATURES_GUIDE.md` for the full reference.

---

## ⚙️ Configuration

Copy `config.example.env` to `.env` and adjust as needed:

| Variable | Default | Description |
|---|---|---|
| `TEAM_STATE_FILE` | `./shared_state.json` | Shared state file path (all agents must point here) |
| `MAX_AGENTS` | `4` | Cap on concurrent live agents |
| `MSG_ROTATE_LIMIT` | `800` | Channel message rotation limit (keeps context small) |
| `BACKUP_EVERY` | `15` | Auto-backup every N writes |
| `BACKUP_KEEP` | `10` | Number of backups to retain |
| `DASHBOARD_PORT` | `8765` | Legacy MCP dashboard port |
| `DASHBOARD_HOST` | `127.0.0.1` | Set `0.0.0.0` for LAN access |
| `APEX_CACHE_TTL` | `3600` | Prompt cache TTL in seconds |
| `APEX_PROMPT_ENGINEER` | `1` | Strip padding from prompts (30–70% smaller) |
| `WEBHOOK_URL` | *(unset)* | Slack / Discord / Teams webhook for completion notify |
| `OBSIDIAN_VAULT` | *(unset)* | Vault path for `obsidian_sync` |

---

## 🛡️ Safety Notes

> Agents run with **`--dangerously-skip-permissions`** so they work unattended. Use only in trusted, non-production environments.

- Edit `_CLI_TEMPLATES` in `spawn_util.py` (or set `APEX_CLI_*` env vars) to re-enable confirmation prompts.
- Ask the PM to *"use worktrees"* — `suggest_worktrees` gives each agent its own git branch so they never overwrite each other.
- `MAX_AGENTS` guards against runaway spawning — raise it deliberately.
- Test without opening any terminal windows: `set APEX_SPAWN_DRYRUN=1` (Windows) / `export APEX_SPAWN_DRYRUN=1` (Unix).

---

## 🔧 Troubleshooting

| Symptom | Fix |
|---|---|
| `claude: command not found` in spawned terminal | Install the CLI and ensure it is on PATH; restart |
| No new terminal opens on Linux | Install `gnome-terminal`, `konsole`, `xterm`, or `tmux` |
| `team` not listed / 0 tools after `claude mcp list` | Re-run the installer; registration must point at `apex_v25.py`; restart client |
| Agents don't share tasks | All agents must use the **same** `TEAM_STATE_FILE` (set once in the global registration) |
| `apex_recommend_skills` returns fallback only | Skill libraries not installed — set `APEX_ANTIGRAVITY_DIR` / `APEX_CYBERSEC_DIR` |
| Tokens spiking | Lower `MAX_AGENTS` and `MSG_ROTATE_LIMIT`; keep debate gated to hard decisions |
| Dashboard shows "Connecting…" | Start `api_server.py` on port 8561 and ensure `NEXT_PUBLIC_API_URL` matches |
| Frontend build errors | `cd frontend && npm install` then `npm run dev` |

---

## 📁 Project Structure

```
apex-team/
│
├── apex.py                  ← one-command launcher (--mode ask|same)
├── apex-ask.sh / .bat       ← shortcut: ASK mode
├── apex-same.sh / .bat      ← shortcut: SAME mode
│
├── apex_v25.py              ← MCP server: base + APEX intelligence (81 tools)
├── team_coordinator.py      ← base coordination engine (73 tools)
├── spawn_util.py            ← cross-platform terminal spawning + seed prompts
├── agent_boot.py            ← runs inside each new terminal; selects/launches CLI
├── api_server.py            ← FastAPI REST + WebSocket bridge for the dashboard
├── launch_agent.py          ← thin wrapper that calls the chosen CLI with a seed
│
├── frontend/                ← Next.js 14 web dashboard
│   └── src/
│       ├── app/             ← pages (page.tsx = main dashboard)
│       └── components/
│           ├── AgentPanel.tsx
│           ├── ChatPanel.tsx
│           ├── ControlsPanel.tsx
│           ├── LaunchWizard.tsx   ← team launch dialog (checkboxes, dropdowns)
│           └── TaskBoard.tsx
│
├── roles/                   ← role playbooks (pm, backend, frontend, qa)
├── seeds/                   ← auto-generated seed prompt files per agent
├── second_brain/            ← persistent brain notes (brain_* tools)
├── examples/                ← MCP config snippets for Codex / Cursor / Gemini
│
├── install.sh               ← one-shot installer (macOS / Linux)
├── install.ps1              ← one-shot installer (Windows)
├── requirements.txt         ← Python deps: mcp, filelock, fastapi, uvicorn
├── config.example.env       ← env template
│
├── FEATURES_GUIDE.md        ← full reference for all 81 tools
├── CHANGELOG.md             ← version history
└── LICENSE                  ← MIT
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

Please keep PRs focused — one feature or fix per PR.

---

## 🙏 Credits

| Component | Author | License |
|---|---|---|
| Base coordination server (`team_coordinator.py`) | **Shalinda Jayasinghe** — [Claude-Team-MCP](https://github.com/shalinda-j/Claude-Team-MCP) | MIT |
| APEX intelligence + autonomy layer (`apex_v25.py`, `apex.py`, `spawn_util.py`) | Multi-Agent v2.5 framework — skill routing, prompt-engineering, token discipline, personas ported to MCP | MIT |
| Web dashboard (`frontend/`) | APEX Team project | MIT |

---

<div align="center">

Released under the **[MIT License](LICENSE)**

*Build autonomously. Ship confidently.*

</div>
