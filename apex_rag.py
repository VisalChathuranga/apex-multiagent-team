"""Agentic RAG (optional vector store) + code-execution sandbox for team APIs."""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import team_coordinator as tc

HERE = Path(__file__).resolve().parent
RAG_INDEX_DIR = HERE / "rag_index"
_CHROMA = None
_COLLECTION = None


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _chunk_text(text: str, size: int = 800) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    return [text[i : i + size] for i in range(0, len(text), size)]


def _keyword_score(query: str, doc: str) -> float:
    q = set(re.findall(r"[a-z0-9]{3,}", query.lower()))
    if not q:
        return 0.0
    d = doc.lower()
    return sum(1 for w in q if w in d) / len(q)


def _get_chroma_collection():
    global _CHROMA, _COLLECTION
    if _COLLECTION is not None:
        return _COLLECTION
    try:
        import chromadb
        from chromadb.config import Settings
    except ImportError:
        return None
    RAG_INDEX_DIR.mkdir(exist_ok=True)
    _CHROMA = chromadb.PersistentClient(
        path=str(RAG_INDEX_DIR),
        settings=Settings(anonymized_telemetry=False),
    )
    _COLLECTION = _CHROMA.get_or_create_collection("apex_brain")
    return _COLLECTION


def index_document(title: str, content: str, tags: str = "") -> str:
    """Index text for semantic search (Chroma if installed, else keyword index in state)."""
    title = (title or "doc").strip()
    chunks = _chunk_text(content)
    if not chunks:
        return "Error: empty content."

    coll = _get_chroma_collection()
    ids_indexed = []

    if coll is not None:
        for i, ch in enumerate(chunks):
            cid = hashlib.sha256(f"{title}:{i}:{ch[:40]}".encode()).hexdigest()[:16]
            coll.upsert(
                ids=[cid],
                documents=[ch],
                metadatas=[{"title": title, "tags": tags, "chunk": i}],
            )
            ids_indexed.append(cid)
        backend = "chromadb"
    else:
        def op(state: dict) -> None:
            idx: List[dict] = state.setdefault("rag_keyword_index", [])
            for i, ch in enumerate(chunks):
                idx.append({
                    "title": title,
                    "tags": tags,
                    "chunk": i,
                    "text": ch,
                    "time": _now(),
                })
            if len(idx) > 2000:
                state["rag_keyword_index"] = idx[-2000:]

        tc._mutate(op)
        backend = "keyword_fallback"
        ids_indexed = [str(i) for i in range(len(chunks))]

    tc.brain_add(title=title, content=content[:4000], category="rag", tags=tags)
    return f"Indexed '{title}': {len(chunks)} chunk(s) via {backend}."


def semantic_search(query: str, limit: int = 5) -> str:
    query = (query or "").strip()
    if not query:
        return "Error: query is required."
    limit = max(1, min(limit, 20))

    coll = _get_chroma_collection()
    if coll is not None:
        try:
            res = coll.query(query_texts=[query], n_results=limit)
            docs = (res.get("documents") or [[]])[0]
            metas = (res.get("metadatas") or [[]])[0]
            lines = [f"Semantic search ({len(docs)} hits, chromadb):"]
            for d, m in zip(docs, metas):
                title = (m or {}).get("title", "?")
                lines.append(f"  • [{title}] {d[:300]}...")
            return "\n".join(lines) if docs else "No semantic hits."
        except Exception as e:
            return f"Chroma query failed: {e}"

    idx = tc._load().get("rag_keyword_index", [])
    scored = sorted(
        (( _keyword_score(query, x.get("text", "")), x) for x in idx),
        key=lambda t: t[0],
        reverse=True,
    )
    hits = [(s, x) for s, x in scored if s > 0][:limit]
    if not hits:
        return "No keyword hits (install chromadb for vector search: pip install chromadb)."
    lines = [f"Keyword search ({len(hits)} hits):"]
    for s, x in hits:
        lines.append(f"  • [{x.get('title')}] (score={s:.2f}) {x.get('text', '')[:300]}...")
    return "\n".join(lines)


def _sandbox_globals() -> Dict[str, Any]:
    import team_coordinator as tc_mod

    def board_tasks():
        return tc_mod._load().get("tasks", [])

    def board_messages(limit=20):
        return tc_mod._load().get("messages", [])[-limit:]

    def post_update(role, text):
        return tc_mod.post_message(sender_role=role, text=text)

    return {
        "__builtins__": {
            "len": len, "str": str, "int": int, "float": float,
            "list": list, "dict": dict, "range": range, "print": print,
            "min": min, "max": max, "sum": sum, "bool": bool,
        },
        "json": json,
        "board_tasks": board_tasks,
        "board_messages": board_messages,
        "post_update": post_update,
    }


def run_tool_script(script: str, by_role: str = "PM") -> str:
    """
    Run a short Python script in a restricted sandbox (code-execution MCP pattern).
    Script can use board_tasks(), board_messages(), post_update().
    """
    script = (script or "").strip()
    if not script:
        return "Error: script is empty."
    if len(script) > 8000:
        return "Error: script too long (max 8000 chars)."

    forbidden = ("subprocess", "os.system", "open(", "__import__", "eval(", "exec(",
                 "shutil.rmtree", "pathlib.Path.write", ".unlink", "spawn")
    for bad in forbidden:
        if bad in script:
            return f"Error: forbidden pattern '{bad}' in sandbox."

    globs = _sandbox_globals()
    locs: Dict[str, Any] = {}
    try:
        exec(script, globs, locs)
        result = locs.get("result", locs.get("output", "OK"))
        out = json.dumps(result, default=str) if not isinstance(result, str) else result
    except Exception as e:
        out = f"Sandbox error: {e}"

    def op(state: dict) -> None:
        runs: List[dict] = state.setdefault("sandbox_runs", [])
        runs.append({"by": by_role, "time": _now(), "preview": script[:200], "result": str(out)[:500]})
        if len(runs) > 50:
            state["sandbox_runs"] = runs[-50:]
        tc._log(state, by_role, "sandbox script run")

    tc._mutate(op)
    return f"Sandbox result:\n{out[:4000]}"
