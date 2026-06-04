#!/usr/bin/env python3
"""
APEX v2.5 — Intelligence layer for Claude-Team-MCP
==================================================
Turns the team-coordination server into an *intelligent* one by porting the
core of the Multi-Agent v2.5 framework INTO the MCP protocol as new tools.

It is PURELY ADDITIVE: it imports the existing `team_coordinator` module
(which builds the FastMCP `mcp` object and registers all ~60 coordination
tools at import time) and registers extra `apex_*` tools on the SAME `mcp`
instance, sharing the SAME locked state file. The original file is untouched.

What v2.5 brings that the base server lacks:
  L0  token discipline  -> apex_token_budget        (budget directive per task)
  L1  shared brain      -> reuses team save/load_summary + get_facts (cheap ctx)
  L2  skill routing     -> apex_recommend_skills     (scans 2,195+ skill catalogs)
      prompt-engineer   -> apex_build_prompt         (framework-correct, padding-free, cached)
      polyglot detect   -> apex_detect_stack
      17 personas        -> apex_persona

Run the combined server with apex_server.py (see that file). Any MCP client
that connects now gets BOTH worlds: live coordination + per-agent intelligence.
"""

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

import team_coordinator as tc   # base server; importing it registers all base tools
import spawn_util               # cross-platform terminal spawning

mcp = tc.mcp  # register apex tools on the SAME FastMCP instance


# ---------------------------------------------------------------------------
# Config — skill libraries (graceful fallback if absent)
# ---------------------------------------------------------------------------
def _expand(p: str) -> Path:
    return Path(os.path.expanduser(os.path.expandvars(p)))

ANTIGRAVITY_DIR = _expand(os.environ.get("APEX_ANTIGRAVITY_DIR", "~/.gemini/antigravity/skills"))
CYBERSEC_DIR = _expand(os.environ.get("APEX_CYBERSEC_DIR", "~/.gemini/cybersecurity-skills/skills"))
PROMPT_ENGINEER_ON = os.environ.get("APEX_PROMPT_ENGINEER", "1") != "0"
PROMPT_CACHE_TTL = int(os.environ.get("APEX_CACHE_TTL", "3600"))
MAX_SKILL_SNIPPET = int(os.environ.get("APEX_SKILL_SNIPPET_CHARS", "600"))

_skill_index = None  # lazy-built {slug: {"lib": "AG"/"CS", "desc": str, "path": Path, "kw": set}}


# ---------------------------------------------------------------------------
# 17 specialized personas (compact v2.5 bodies, framework + hard rules)
# ---------------------------------------------------------------------------
_FRAMEWORK = {  # role -> prompting framework v2.5 assigns
    "backend": "ReAct+Stop", "frontend": "ReAct+Stop", "dba": "ReAct+Stop",
    "ai-integrator": "ReAct+Stop", "tester": "RTF", "writer": "CO-STAR",
    "security-auditor": "CoT+File-Scope", "pen-tester": "CoT+Scope-Lock",
    "dfir-analyst": "Evidence-First", "architect": "Chain-of-Thought",
    "analyst": "RTF", "reviewer": "Checklist", "perf-tuner": "Measure-First",
    "devops": "RTF", "team-lead": "Orchestrate", "PM": "Orchestrate",
}

_PERSONAS = {
    "architect":        ("Phase 1 · System design. C4 diagrams, ADRs, DDD. "
                         "Output design + tradeoffs; do NOT write feature code."),
    "analyst":          ("Phase 1 · Requirements. User stories, MVP scope, acceptance criteria. "
                         "Clarify before assuming."),
    "backend":          ("Phase 2 · POLYGLOT backend (Python/Node/Go/Rust/.NET — auto-detect). "
                         "API design, error handling, tests. Stop when task done; no scope creep."),
    "frontend":         ("Phase 2 · POLYGLOT frontend, Next.js PRIORITY then Nuxt/Astro/Angular/"
                         "SvelteKit/Vue/React/Solid/Qwik/HTML. TS by default. Accessible, responsive."),
    "dba":              ("Phase 2 · Schemas, migrations, indexes, queries "
                         "(PG/MySQL/SQL Server/Mongo/Chroma). Migrations must be reversible."),
    "ai-integrator":    ("Phase 2 · Prompt engineering, RAG, AI API integration. "
                         "Validate model outputs; never trust unparsed JSON."),
    "tester":           ("Phase 3 · Unit + E2E (Playwright/Jest/Pytest/Vitest). "
                         "Cover happy path + edges + failure modes. Report coverage."),
    "security-auditor": ("Phase 3 · DEFENSIVE code audit. OWASP, secrets, SAST, dependency CVEs. "
                         "Map findings to MITRE/NIST; file findings via report_finding."),
    "pen-tester":       ("Phase 3 · OFFENSIVE. ONLY within written, authorized scope. "
                         "NEVER touch production. Validate exploits in staging only."),
    "dfir-analyst":     ("Phase 3 · Forensics & IR. Evidence-first: cite artifacts (logs/memory/disk). "
                         "No hypothesis without evidence."),
    "reviewer":         ("Phase 3 · Code quality. SOLID, readability, refactors. "
                         "Concrete suggestions, not vague praise."),
    "perf-tuner":       ("Phase 3 · Profiling & latency. Measure first, optimize the hot path, "
                         "re-measure. No premature optimization."),
    "writer":           ("Phase 4 · README, changelog, docs. Clear, accurate, example-driven."),
    "devops":           ("Phase 4 · CI/CD, Docker, deploy. Reproducible builds; secrets via env, "
                         "never committed."),
    "team-lead":        ("Phase 0.8 · Cross-terminal orchestrator + debate JUDGE. "
                         "join_team, load_summary BEFORE reading files, assign_work, "
                         "start_debate ONLY for high-stakes calls, save_summary on milestones."),
}
# aliases
_PERSONAS["pm"] = _PERSONAS["team-lead"]
_PERSONAS["frontend-react"] = _PERSONAS["frontend"]
_PERSONAS["security"] = _PERSONAS["security-auditor"]

# fallback keyword routing when catalogs are absent
_FALLBACK_SKILLS = {
    "architect": ["software-architecture", "architecture-decision-records", "domain-driven-design"],
    "backend": ["api-design-principles", "error-handling-patterns", "testing-patterns"],
    "frontend": ["nextjs-app-router", "accessibility", "responsive-design"],
    "dba": ["database-schema-design", "sql-query-optimization", "safe-migrations"],
    "tester": ["playwright-e2e", "test-strategy", "edge-case-coverage"],
    "security-auditor": ["owasp-top-10", "secrets-detection", "dependency-cve-scan"],
    "pen-tester": ["penetration-testing", "vulnerability-scanning", "exploit-validation"],
    "dfir-analyst": ["memory-forensics-volatility3", "log-analysis", "threat-hunting-mitre-attack"],
    "writer": ["technical-writing", "changelog"],
    "devops": ["ci-cd-pipelines", "docker-best-practices"],
}


# ---------------------------------------------------------------------------
# Skill catalog scanning (L2)
# ---------------------------------------------------------------------------
def _build_skill_index() -> dict:
    global _skill_index
    if _skill_index is not None:
        return _skill_index
    idx = {}
    for lib, base in (("AG", ANTIGRAVITY_DIR), ("CS", CYBERSEC_DIR)):
        if not base.exists():
            continue
        for entry in base.iterdir():
            sk = entry / "SKILL.md"
            if not (entry.is_dir() and sk.exists()):
                continue
            slug = entry.name
            desc = ""
            try:
                head = sk.read_text(encoding="utf-8", errors="ignore")[:1200]
                m = re.search(r"description:\s*(.+)", head)
                desc = (m.group(1).strip() if m else head.split("\n")[0]).strip("# ").strip()
            except Exception:
                pass
            kw = set(re.findall(r"[a-z0-9]+", (slug + " " + desc).lower()))
            idx[slug] = {"lib": lib, "desc": desc[:160], "path": sk, "kw": kw}
    _skill_index = idx
    return idx


def _recommend(role: str, task: str, max_skills: int) -> list:
    role = role.lower().strip()
    idx = _build_skill_index()
    if not idx:  # no libraries installed -> fallback
        return [{"slug": s, "lib": "FB", "desc": "(fallback keyword skill)"}
                for s in _FALLBACK_SKILLS.get(role, [])[:max_skills]]
    task_kw = set(re.findall(r"[a-z0-9]+", task.lower()))
    role_kw = set(re.findall(r"[a-z0-9]+", role)) | task_kw
    scored = []
    for slug, meta in idx.items():
        score = len(role_kw & meta["kw"])
        # bias cyber skills toward security roles
        if meta["lib"] == "CS" and role in ("security-auditor", "pen-tester", "dfir-analyst"):
            score += 2
        if score > 0:
            scored.append((score, slug, meta))
    scored.sort(key=lambda x: -x[0])
    return [{"slug": s, "lib": m["lib"], "desc": m["desc"]} for _, s, m in scored[:max_skills]]


def _load_skill_snippet(slug: str) -> str:
    idx = _build_skill_index()
    meta = idx.get(slug)
    if not meta:
        return ""
    try:
        txt = meta["path"].read_text(encoding="utf-8", errors="ignore")
        return txt[:MAX_SKILL_SNIPPET]
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# L0 token discipline
# ---------------------------------------------------------------------------
def _budget(task: str) -> str:
    words = len(task.split())
    if words < 15:
        return "BUDGET: trivial task — answer directly, skip ceremony, <400 tokens."
    if words < 60:
        return "BUDGET: standard — be concise, no preamble, cite shared facts not full history."
    return "BUDGET: complex — plan in <=5 bullets, reuse loaded summary, avoid re-deriving known facts."


# ---------------------------------------------------------------------------
# Prompt-engineer (L2 optimize) — strip padding, enforce framework
# ---------------------------------------------------------------------------
_PAD = re.compile(r"\b(please|kindly|in order to|as you know|it is important to note that|"
                  r"basically|simply|just|very|really|actually)\b", re.I)


def _optimize(raw: str) -> str:
    if not PROMPT_ENGINEER_ON:
        return raw
    out = _PAD.sub("", raw)
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


# shared cache lives in team state under "apex_cache"
def _cache_get(key: str):
    state = tc._load()
    rec = state.get("apex_cache", {}).get(key)
    if rec and (time.time() - rec["t"]) < PROMPT_CACHE_TTL:
        return rec["v"]
    return None


def _cache_put(key: str, value: str):
    def op(state):
        state.setdefault("apex_cache", {})[key] = {"v": value, "t": time.time()}
    tc._mutate(op)


# ---------------------------------------------------------------------------
# Polyglot stack detection
# ---------------------------------------------------------------------------
def _detect(project_dir: str) -> dict:
    p = _expand(project_dir)
    found = {"frontend": None, "backend": None, "evidence": []}
    if not p.exists():
        return {"error": f"path not found: {p}"}
    names = {f.name for f in p.iterdir()} if p.is_dir() else set()
    # frontend (Next.js priority)
    if any(n.startswith("next.config") for n in names):
        found["frontend"] = "Next.js"; found["evidence"].append("next.config.*")
    elif "nuxt.config.ts" in names or "nuxt.config.js" in names:
        found["frontend"] = "Nuxt"
    elif "astro.config.mjs" in names:
        found["frontend"] = "Astro"
    elif "angular.json" in names:
        found["frontend"] = "Angular"
    elif "svelte.config.js" in names:
        found["frontend"] = "SvelteKit"
    # package.json deps fallback
    pkg = p / "package.json"
    if pkg.exists() and not found["frontend"]:
        try:
            deps = json.loads(pkg.read_text()).get("dependencies", {})
            for fw, key in [("Next.js", "next"), ("React", "react"), ("Vue", "vue"), ("Solid", "solid-js")]:
                if key in deps:
                    found["frontend"] = fw; found["evidence"].append(f"dep:{key}"); break
        except Exception:
            pass
    # backend
    if (p / "pyproject.toml").exists() or (p / "requirements.txt").exists():
        found["backend"] = "Python"
    elif (p / "go.mod").exists():
        found["backend"] = "Go"
    elif (p / "Cargo.toml").exists():
        found["backend"] = "Rust"
    elif any(n.endswith(".csproj") for n in names):
        found["backend"] = ".NET"
    elif pkg.exists():
        found["backend"] = "Node"
    return found


# ===========================================================================
# MCP TOOLS (apex_*)
# ===========================================================================

@mcp.tool()
def apex_status() -> str:
    """Show what the APEX v2.5 intelligence layer has loaded: skill catalogs
    detected, personas available, prompt cache size, optimizer state."""
    idx = _build_skill_index()
    ag = sum(1 for m in idx.values() if m["lib"] == "AG")
    cs = sum(1 for m in idx.values() if m["lib"] == "CS")
    state = tc._load()
    cache = len(state.get("apex_cache", {}))
    lines = [
        "=== APEX v2.5 layer ===",
        f"Antigravity skills: {ag}  (dir: {ANTIGRAVITY_DIR}{'' if ANTIGRAVITY_DIR.exists() else '  [MISSING -> fallback]'})",
        f"Cybersecurity skills: {cs}  (dir: {CYBERSEC_DIR}{'' if CYBERSEC_DIR.exists() else '  [MISSING -> fallback]'})",
        f"Personas available: {len(set(_PERSONAS.values()))}",
        f"Prompt-engineer: {'ON' if PROMPT_ENGINEER_ON else 'OFF'} · cache entries: {cache} (TTL {PROMPT_CACHE_TTL}s)",
        "Tools: apex_persona, apex_recommend_skills, apex_build_prompt, apex_detect_stack, apex_token_budget",
    ]
    return "\n".join(lines)


@mcp.tool()
def apex_persona(role: str) -> str:
    """Return the v2.5 specialized persona body for a role, with its assigned
    prompting framework. Use right after join_team so the agent adopts the
    correct specialist behavior.

    Args:
        role: e.g. architect, backend, frontend, dba, tester, security-auditor,
              pen-tester, dfir-analyst, reviewer, perf-tuner, writer, devops, team-lead.
    """
    r = role.lower().strip()
    body = _PERSONAS.get(r)
    if not body:
        return (f"No persona '{role}'. Available: " + ", ".join(sorted(set(_PERSONAS) - {'pm','frontend-react','security'})))
    fw = _FRAMEWORK.get(r, "RTF")
    return f"=== PERSONA: {role} ===\nframework: {fw}\n{body}"


@mcp.tool()
def apex_recommend_skills(role: str, task: str, max_skills: int = 5) -> str:
    """L2 skill routing. Scan the Antigravity (1,441+) and Cybersecurity (754)
    catalogs and recommend the most relevant skills for this role+task. Falls
    back to a built-in keyword map if the libraries are not installed.

    Args:
        role: agent role, e.g. backend.
        task: the task text.
        max_skills: cap (default 5).
    """
    recs = _recommend(role, task, max_skills)
    if not recs:
        return f"No skill matches for {role}. (Install skill libs or use apex_build_prompt --no skills.)"
    out = [f"Recommended skills for {role}:"]
    for r in recs:
        out.append(f"  [{r['lib']}] {r['slug']} — {r['desc']}")
    return "\n".join(out)


@mcp.tool()
def apex_build_prompt(role: str, task: str, use_skills: bool = True,
                      optimize: bool = True, pull_context: bool = True) -> str:
    """THE core tool. Runs the full v2.5 pipeline and returns one optimized,
    skill-loaded, framework-correct prompt for a downstream agent:

      L0  token budget directive
      L1  pull shared context (latest summary + facts)  <- the token saver
      L2  recommend skills -> load SKILL.md snippets -> assemble
          -> prompt-engineer rewrite (strip padding) -> cache by hash

    An agent that just picked up a board task should call this, then act on the
    returned prompt. Result is cached (TTL) so repeats are free.

    Args:
        role: agent role.
        task: task text.
        use_skills: include recommended skills (default True).
        optimize: run the prompt-engineer padding strip (default True).
        pull_context: include shared summary+facts instead of full history (default True).
    """
    skills = _recommend(role, task, 5) if use_skills else []
    cache_key = hashlib.sha256(
        f"{role}|{task}|{[s['slug'] for s in skills]}|{optimize}|{pull_context}".encode()
    ).hexdigest()[:16]
    cached = _cache_get(cache_key)
    if cached:
        return cached + "\n\n[apex: cache hit — 0 build tokens]"

    parts = ["--- BUDGET ---", _budget(task)]

    if pull_context:
        # L1: cheap shared context, NOT full message history
        try:
            summary = tc.load_summary("latest")
        except Exception:
            summary = ""
        try:
            facts = tc.get_facts("")
        except Exception:
            facts = ""
        if summary and "no summar" not in summary.lower():
            parts += ["--- SHARED SUMMARY (reuse, do not re-derive) ---", summary[:900]]
        if facts and "no facts" not in facts.lower():
            parts += ["--- SHARED FACTS ---", facts[:500]]

    fw = _FRAMEWORK.get(role.lower(), "RTF")
    persona = _PERSONAS.get(role.lower(), f"Specialist: {role}.")
    parts += [f"--- PERSONA ({fw}) ---", persona]

    if skills:
        parts.append("--- SKILLS PRELOADED ---")
        for s in skills:
            snip = _load_skill_snippet(s["slug"])
            parts.append(f"[{s['lib']}] {s['slug']}: {snip or s['desc']}")

    parts += ["--- TASK ---", task,
              "--- RULES ---",
              "Coordinate via team tools (post_message/update_task). "
              "On milestone call save_summary + set_fact. Stay in your file scope."]

    raw = "\n".join(parts)
    final = _optimize(raw) if optimize else raw
    _cache_put(cache_key, final)
    saved = max(0, len(raw) - len(final))
    return final + f"\n\n[apex: built · ~{saved} chars trimmed · cache key {cache_key}]"


@mcp.tool()
def apex_detect_stack(project_dir: str) -> str:
    """Polyglot detection: inspect a project dir and report the frontend
    framework (Next.js priority) and backend language, with evidence. Use this
    before assigning build tasks so backend/frontend agents target the right stack.

    Args:
        project_dir: path to the project root.
    """
    d = _detect(project_dir)
    if "error" in d:
        return d["error"]
    ev = ", ".join(d["evidence"]) or "deps/config"
    return (f"Stack detected:\n  frontend: {d['frontend'] or 'none'}\n"
            f"  backend:  {d['backend'] or 'none'}\n  evidence: {ev}")


@mcp.tool()
def apex_token_budget(task: str) -> str:
    """L0 token discipline — return the budget directive for a task based on its
    size/complexity. Prepend it to any prompt to keep agents concise.

    Args:
        task: the task text.
    """
    return _budget(task)


# ============================================================================
# AUTONOMOUS TEAM BUILDING — spawn teammate terminals from one conversation
# ============================================================================
# Spawn modes:
#   "same" : every worker terminal launches the given `cli` (the one you started)
#   "ask"  : every worker terminal ASKS the user which service to use for it
# Per-role override: pass `clis` aligned with `roles`, e.g. "claude,codex,cursor".

_DEFAULT_ROLES = ["Backend", "Frontend", "QA"]


@mcp.tool()
def apex_spawn(role: str, project_dir: str, cli: str = "ask", count: int = 1) -> str:
    """Open NEW OS terminal(s) for a role, each auto-joining the team.
    Cross-platform (Windows Terminal / macOS Terminal / Linux).

    Args:
        role: role for the new teammate, e.g. Backend, Frontend, QA, DevOps.
        project_dir: project root the agent should work in.
        cli: "ask" (the new terminal asks the user which service), or a fixed
             service: claude | codex | gemini | cursor.
        count: how many copies of this role to spawn (default 1).
    """
    results = []
    for i in range(max(1, count)):
        title = f"APEX-{role}" + (f"-{i+1}" if count > 1 else "")
        if sys.platform == "win32":
            results.append(spawn_util.open_terminal_boot(title, role, project_dir, cli=cli))
        else:
            boot = spawn_util.agent_boot_command(role, project_dir, cli=cli)
            results.append(spawn_util.open_terminal(title, boot, cwd=project_dir))
    label = "ask-on-open" if (cli or "ask").lower() == "ask" else cli
    tc._mutate(lambda s: tc._log(s, "PM", f"spawned {count}x {role} ({label})"))
    return "\n".join(results)


@mcp.tool()
def apex_orchestrate(goal: str, project_dir: str, roles: str = "Backend,Frontend,QA",
                     cli: str = "claude", clis: str = "", mode: str = "same") -> str:
    """ONE-CALL team builder. Records the goal into shared memory, then opens a
    terminal per role, each auto-joining the team. After this, the PM plans
    tasks (add_task) and assigns them (assign_work).

    Args:
        goal: the project goal in plain language.
        project_dir: project root for all agents.
        roles: comma-separated roles, e.g. "Backend,Frontend,QA".
        cli: service used for ALL workers when mode="same" (claude|codex|gemini|cursor).
        clis: optional per-role override, comma-aligned with roles
              (e.g. "claude,codex,cursor"); overrides cli/mode for those slots.
        mode: "same" -> all workers use `cli`; "ask" -> each terminal asks the
              user which service to use for that agent.
    """
    role_list = spawn_util.normalize_roles(
        [r.strip() for r in roles.split(",") if r.strip()] or _DEFAULT_ROLES
    )

    def op(state):
        state.setdefault("facts", {})["project.goal"] = {"value": goal, "by": "PM", "time": tc._now()}
        tc._log(state, "PM", f"orchestrate[{mode}]: goal set, spawning {len(role_list)} agents")
    tc._mutate(op)
    try:
        tc.save_summary(f"GOAL: {goal}\nROLES: {', '.join(role_list)}\nDIR: {project_dir}", by_role="PM")
    except Exception:
        pass

    out = [f"Goal recorded. Mode='{mode}'. Spawning {len(role_list)} teammates in {project_dir}:"]
    for item in spawn_util.spawn_team_workers(role_list, project_dir, mode=mode, cli=cli, clis=clis):
        out.append(f"  • {item['role']} [{item['cli']}] → {item['message']}")
    out.append("\nNext: add_task for each piece of work, assign_work to roles, "
               "then post_message to kick off. Monitor with view_board.")
    return "\n".join(out)


if __name__ == "__main__":
    # Combined run: base coordination + apex intelligence + autonomy tools.
    mcp.run()
