# APEX Team — Autonomous Multi-Agent System

> Open **one** terminal, say what you want built, and a team of AI agents
> (Claude, Codex, Cursor, Gemini) opens its **own** terminals, splits the work,
> and builds the whole project together — coordinating live, debating decisions,
> and sharing memory. Token-efficient by design.

APEX = **Claude-Team-MCP** (live coordination) **+ Multi-Agent v2.5** (per-agent
intelligence: skill routing, prompt-engineering, token discipline, 17 specialist
personas) fused into **one** MCP server, plus a one-command launcher.

```
   one command  →  PM terminal  →  PM spawns Backend / Frontend / QA terminals
                                    every agent joins the same shared "world"
                                    they plan → build → test → report, autonomously
```

---

## ✨ What you get

- **One-command launch** (`python apex.py`) — type a goal, the team self-assembles.
- **Self-spawning team** — the PM opens teammate terminals itself, on any CLI mix.
- **81 MCP tools** on one server: 73 coordination + 8 APEX intelligence/autonomy.
- **Live coordination** — shared channel, task board, real-time `wait_for_message`,
  structured debate (propose → critique → revise → judge), project memory, second brain.
- **Per-agent intelligence** — skill routing over 2,195+ skills, framework-correct
  padding-free prompts, polyglot stack detection, 17 specialist personas.
- **Token-efficient** — agents reload a compact shared summary instead of full
  history; prompts are trimmed and hash-cached; debate is gated to high-stakes calls.
- **Vendor-agnostic** — Claude Code, Codex CLI, Gemini CLI, Cursor all join one world.
- **Cross-platform** — Windows / macOS / Linux terminal spawning.

---

## 🧱 Architecture

```
                       ┌──────────────────────────────┐
   you ── apex.py ────▶│  APEX-PM terminal (any CLI)   │
                       │  plans · apex_orchestrate()   │
                       └───────────────┬──────────────┘
                                       │ spawns
              ┌────────────────────────┼────────────────────────┐
              ▼                        ▼                         ▼
      ┌───────────────┐       ┌───────────────┐         ┌───────────────┐
      │ APEX-Backend  │       │ APEX-Frontend │         │ APEX-QA        │
      │ (claude)      │       │ (codex)       │         │ (cursor)       │
      └───────┬───────┘       └───────┬───────┘         └───────┬───────┘
              └───────────── one file-locked shared_state.json ─┘
                         channel · board · debate · memory · brain
              + apex_build_prompt() gives each agent skills+budget+context
```

| Layer | Job | Provided by |
|---|---|---|
| L0 — Token discipline | budget directive per task | `apex_token_budget` |
| L1 — Shared brain ★ | write-once decisions, reload compact summary (the token saver) | base `save/load_summary`, `set/get_facts` |
| L2 — Intelligence | skill routing + framework-correct, padding-free, cached prompts | `apex_recommend_skills`, `apex_build_prompt` |
| L3 — Coordination | live channel, board, gated debate, autonomy | base team tools + `apex_orchestrate`, `apex_spawn` |

---

## 📦 Prerequisites

1. **Python 3.8+**
2. **At least one agent CLI** on your PATH:
   - [Claude Code](https://claude.ai/code) — `claude`
   - Codex CLI — `codex`
   - Gemini CLI — `gemini`
   - Cursor agent — `cursor-agent`
3. *(Optional)* the v2.5 skill libraries for full skill routing — APEX falls back
   to a built-in keyword map if they're absent, so this is **not** required:
   ```bash
   npx antigravity-awesome-skills                 # ~/.gemini/antigravity/skills
   git clone https://github.com/mukul975/Anthropic-Cybersecurity-Skills.git \
     ~/.gemini/cybersecurity-skills
   ```

---

## 🚀 Install (one shot)

```bash
# macOS / Linux
cd apex-team
bash install.sh

# Windows (PowerShell)
cd apex-team
./install.ps1
```

The installer: installs Python deps (`mcp`, `filelock`) and **registers the
combined server globally** with Claude Code (and prints the snippets for Codex /
Gemini / Cursor). It points the registration at **`apex_v25.py`** — which imports
`team_coordinator.py`, so all base + APEX tools load together.

Verify:
```bash
claude mcp list          # "team" should appear with 81 tools
```

> **Manual registration** (if you skip the installer):
> ```bash
> claude mcp add team -s user -- \
>   env TEAM_STATE_FILE="$PWD/shared_state.json" \
>       BRAIN_DIR="$PWD/second_brain" \
>       APEX_ANTIGRAVITY_DIR="$HOME/.gemini/antigravity/skills" \
>       APEX_CYBERSEC_DIR="$HOME/.gemini/cybersecurity-skills/skills" \
>       MAX_AGENTS=4 MSG_ROTATE_LIMIT=800 \
>   python "$PWD/apex_v25.py"
> ```
> Restart your CLI client after registering so the tools load.
>
> **Codex / Cursor / Gemini:** copy the ready-made blocks in `examples/` (they
> point at `apex_v25.py`) into each client's config — just replace `/ABS/PATH`.

---

## ▶️ Usage — two command types

Run one command, type your goal, watch it build. Pick how new agent terminals
choose their CLI:

### ① ASK mode — each terminal asks which service
Every worker terminal opens and **asks you** which service (claude / cursor /
codex / gemini) to run for **that** agent. Mix freely.

```bash
./apex-ask.sh "Build a REST API for cheque processing"
#  Windows:  apex-ask.bat "..."
#  or:       python apex.py --mode ask "..."
```
A new window shows:
```
====================================================
  APEX — new agent terminal:  Backend
====================================================
  Installed services: claude, codex, cursor
  Which service should run the Backend agent?
    1) claude   2) codex   3) cursor   4) gemini
  choice (number or name): _
```

### ② SAME mode — one CLI for the whole team
Every worker terminal uses the **same** service you started the PM with — no
questions.

```bash
./apex-same.sh --cli claude "Build a REST API for cheque processing"
#  Windows:  apex-same.bat --cli claude "..."
#  or:       python apex.py --mode same --cli claude "..."
```

Fully interactive (asks mode, goal, dir, CLI, roles):
```bash
python apex.py
#   Command type — (1) ASK each terminal / (2) SAME cli for all : 1
#   What should the team build? : <goal>
#   Project directory           : ./my-project
#   PM CLI / Worker roles        : claude / Backend,Frontend,QA
```

**What happens automatically (both modes):**
1. A **PM terminal** opens on your chosen CLI.
2. PM joins the team, detects the stack, calls `apex_orchestrate(...)` with the mode.
3. `apex_orchestrate` opens a terminal per worker role — **ASK** lets each ask which
   service; **SAME** launches them all on one CLI.
4. Every agent auto-joins the shared team, pulls the goal, works the board.
5. PM assigns tasks, gates any debate, runs `export_report` when done.

**Explicit per-role mix** (skip asking, set each directly):
```
apex_orchestrate(goal=..., roles="Backend,Frontend,QA", clis="claude,codex,cursor")
```

**Grow the team mid-run** — tell the PM:
- *"spawn a DevOps agent and ask me which service"* → `apex_spawn("DevOps", dir, cli="ask")`
- *"spawn a DevOps agent on codex"* → `apex_spawn("DevOps", dir, cli="codex")`

**Live dashboard** — in any agent: `start_dashboard()` → opens a local web view of
the board, channel, and metrics.

---

## 🧰 The 8 APEX tools

| Tool | Purpose |
|---|---|
| `apex_orchestrate` | One call: record goal + spawn the whole worker team |
| `apex_spawn` | Open new terminal(s) for a role on any CLI, auto-joining the team |
| `apex_build_prompt` ★ | budget + shared context + persona + skills → optimized, cached prompt |
| `apex_recommend_skills` | Scan 2,195+ skill catalogs, pick ≤5 for a role+task |
| `apex_persona` | The v2.5 specialist body + prompting framework for a role |
| `apex_detect_stack` | Polyglot detection (Next.js-priority frontend + backend lang) |
| `apex_token_budget` | L0 budget directive for a task |
| `apex_status` | What's loaded: catalogs, personas, cache |

Plus the 73 base tools: `join_team`, `post_message`, `wait_for_message`,
`add_task`, `assign_work`, `view_board`, `start_debate`/`judge_debate`,
`save_summary`/`load_summary`, `set_fact`/`get_facts`, `report_finding`,
`brain_add`, `start_dashboard`, `export_report`, … (see `team_coordinator.py`).

---

## 🛡️ Robustness & intelligence (auto-used by the team)

The base engine ships 65+ tools; the PM now drives the important ones for you
(full reference in `FEATURES_GUIDE.md`):

- **Correct build order** — tasks use `add_task(priority, depends_on)`; blocked
  tasks wait until dependencies finish (backend API before frontend wiring).
- **Skill-based assignment** — `set_skills` + `auto_assign` route each task to the
  right role automatically.
- **No file collisions** — `suggest_worktrees` gives each agent its own git
  worktree; `check_conflicts` flags overlap before it happens.
- **Crash recovery** — if an agent goes silent the PM runs `ping` →
  `recover_tasks` → reassigns. State auto-backs-up every 15 writes
  (`backup_now` / `restore_backup` available).
- **Live dashboard** — the PM calls `start_dashboard()` at launch
  (http://localhost:8765/): board, chat, agents, debate, timeline, 2s refresh.
- **Completion notice** — set `WEBHOOK_URL` and the PM fires `webhook_notify`
  (Slack/Discord/Teams) when the project is done; `export_report` writes a
  Markdown summary.
- **Better debate** — proposals are scored (`score_debate`, `cast_vote`) before
  `judge_debate` decides.

## 💰 Token-saving knobs

| Setting / habit | Effect |
|---|---|
| `apex_build_prompt(pull_context=True)` | agents read a ~200-token summary, not full history |
| `MSG_ROTATE_LIMIT=800` | smaller channel → less context bloat |
| `MAX_AGENTS=4` | cap live agents (each consumes tokens independently) |
| Debate gated to high-stakes | avoids expensive multi-round loops |
| `APEX_CACHE_TTL=3600` | reuse optimized prompts within the hour (repeat calls = 0 build tokens) |
| `APEX_PROMPT_ENGINEER=1` | strip padding from every prompt (30–70% smaller) |
| `context_checkpoint` (long runs) | save a summary then /clear — frees the window |
| `BACKUP_EVERY=15` | auto-backup cadence (reliability, not tokens) |
| `DASHBOARD_HOST=0.0.0.0` | expose the live dashboard on your LAN |
| `WEBHOOK_URL=...` | get pinged when the build completes |

---

## ⚠️ Safety

- Spawned agents launch with permission prompts skipped (`--dangerously-skip-permissions`
  for Claude) so they run unattended — **use only in trusted projects.** Edit the
  CLI templates in `spawn_util.py` (or `APEX_CLI_*` env) to require approvals.
- Give each agent its own **git worktree** to avoid file-edit conflicts when several
  work in one repo. Ask the PM: *"use worktrees"* (base tool `suggest_worktrees`).
- `MAX_AGENTS` guards against runaway spawning. Raise it deliberately.

---

## 🔧 Troubleshooting

| Symptom | Fix |
|---|---|
| `claude: command not found` in spawned terminal | Install the CLI / fix PATH; restart |
| No new terminal opens (Linux) | Install `gnome-terminal`/`konsole`/`xterm`, or use `tmux` |
| `team` not listed / 0 tools | Re-run install; registration must point at `apex_v25.py`; restart client |
| Agents don't share a world | All must use the **same** `TEAM_STATE_FILE` (set once in global registration) |
| `apex_recommend_skills` returns fallback only | Skill libs not installed — optional; set `APEX_ANTIGRAVITY_DIR`/`APEX_CYBERSEC_DIR` |
| Tokens spiking | Lower `MAX_AGENTS`, `MSG_ROTATE_LIMIT`; keep debate gated |
| Test without opening windows | `export APEX_SPAWN_DRYRUN=1` |

---

## 📁 Project layout

```
apex-team/
├── apex.py                 ← the one command you run (launcher, --mode same|ask)
├── apex-ask.sh/.bat        ← command type ①: each terminal asks which service
├── apex-same.sh/.bat       ← command type ②: one CLI for the whole team
├── agent_boot.py           ← runs in each new terminal; asks/launches the CLI
├── apex_v25.py             ← combined MCP server: base + APEX intelligence + autonomy
├── team_coordinator.py     ← base coordination server (Claude-Team-MCP v7.0, MIT)
├── spawn_util.py           ← cross-platform terminal spawning + seeds
├── install.sh / install.ps1← one-shot installers
├── examples/               ← MCP registration configs (claude/codex/cursor/gemini)
├── config.example.env      ← env template (incl. backup/dashboard/webhook vars)
├── requirements.txt
├── roles/                  ← role playbooks (pm, backend, frontend, qa)
├── FEATURES_GUIDE.md       ← full base tool reference (65+ tools, by batch)
├── CHANGELOG.md            ← base server version history
├── README.md
└── LICENSE
```

---

## 🙏 Credits & License

- **Base coordination server** (`team_coordinator.py`): *Claude-Team-MCP* by
  **Shalinda Jayasinghe** — https://github.com/shalinda-j/Claude-Team-MCP (MIT).
- **APEX intelligence + autonomy layer** (`apex_v25.py`, `apex.py`, `spawn_util.py`):
  ports the Multi-Agent v2.5 framework's skill routing, prompt-engineering, token
  discipline, and personas into the MCP protocol, and adds the one-command
  self-spawning launcher.

Released under the **MIT License** (see `LICENSE`). The base server retains its
original MIT terms and authorship.
