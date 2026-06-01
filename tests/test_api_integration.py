"""
Integration tests for api_server.py — all REST endpoints and WebSocket /ws/updates.

Each test runs against a fresh temporary state file so the production
shared_state.json is never touched.
"""

import json
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import team_coordinator as tc
import api_server


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_STATE = {
    "agents": {},
    "messages": [],
    "tasks": [],
    "notes": [],
    "facts": {},
    "summaries": [],
    "activity_log": [],
    "findings": [],
    "debate": None,
    "_write_count": 0,
}


@pytest.fixture()
def tmp_state(tmp_path, monkeypatch):
    """Point team_coordinator at a fresh temporary state file for each test."""
    state_file = tmp_path / "test_state.json"
    state_file.write_text(json.dumps(MINIMAL_STATE, indent=2), encoding="utf-8")

    lock_file = tmp_path / "test_state.json.lock"

    monkeypatch.setattr(tc, "STATE_FILE", state_file)
    monkeypatch.setattr(tc, "LOCK_FILE", lock_file)
    return state_file


@pytest.fixture()
def client(tmp_state):
    """FastAPI TestClient wired to a fresh state file."""
    with TestClient(api_server.app, raise_server_exceptions=True) as c:
        yield c


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _read_state(tmp_state: Path) -> dict:
    return json.loads(tmp_state.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# GET /api/state
# ---------------------------------------------------------------------------

class TestGetState:
    def test_returns_200(self, client):
        r = client.get("/api/state")
        assert r.status_code == 200

    def test_top_level_keys(self, client):
        data = client.get("/api/state").json()
        for key in ("metrics", "agents", "tasks", "messages", "debate", "timeline", "facts", "findings"):
            assert key in data, f"missing key: {key}"

    def test_metrics_shape(self, client):
        m = client.get("/api/state").json()["metrics"]
        for key in ("agents_total", "agents_online", "messages", "tasks_total", "tasks_done"):
            assert key in m, f"missing metrics key: {key}"

    def test_empty_initial_state(self, client):
        data = client.get("/api/state").json()
        assert data["agents"] == {}
        assert data["tasks"] == []
        assert data["messages"] == []


# ---------------------------------------------------------------------------
# GET /api/agents
# ---------------------------------------------------------------------------

class TestGetAgents:
    def test_empty(self, client):
        r = client.get("/api/agents")
        assert r.status_code == 200
        assert r.json() == {}

    def test_after_join(self, client):
        client.post("/api/agents/join", json={"role": "Backend", "name": "BackendAgent"})
        agents = client.get("/api/agents").json()
        assert "Backend" in agents
        assert agents["Backend"]["role"] == "Backend"


# ---------------------------------------------------------------------------
# GET /api/tasks
# ---------------------------------------------------------------------------

class TestGetTasks:
    def test_empty(self, client):
        r = client.get("/api/tasks")
        assert r.status_code == 200
        assert r.json() == []

    def test_after_add(self, client):
        client.post("/api/agents/join", json={"role": "PM"})
        client.post("/api/tasks", json={"title": "Task Alpha", "created_by": "PM"})
        tasks = client.get("/api/tasks").json()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Task Alpha"


# ---------------------------------------------------------------------------
# GET /api/messages
# ---------------------------------------------------------------------------

class TestGetMessages:
    def test_empty(self, client):
        r = client.get("/api/messages")
        assert r.status_code == 200
        data = r.json()
        assert "messages" in data
        assert "next_index" in data
        assert data["messages"] == []
        assert data["next_index"] == 0

    def test_since_param(self, client):
        client.post("/api/agents/join", json={"role": "PM"})
        client.post("/api/messages", json={"sender_role": "PM", "text": "msg1"})
        client.post("/api/messages", json={"sender_role": "PM", "text": "msg2"})
        client.post("/api/messages", json={"sender_role": "PM", "text": "msg3"})

        all_msgs = client.get("/api/messages").json()
        total = all_msgs["next_index"]
        assert total >= 3

        tail = client.get(f"/api/messages?since={total - 1}").json()
        assert len(tail["messages"]) == 1

    def test_since_beyond_end_returns_empty(self, client):
        data = client.get("/api/messages?since=9999").json()
        assert data["messages"] == []

    def test_messages_have_required_fields(self, client):
        client.post("/api/agents/join", json={"role": "QA"})
        client.post("/api/messages", json={"sender_role": "QA", "text": "hello", "mention": "PM"})
        msgs = client.get("/api/messages").json()["messages"]
        msg = [m for m in msgs if m.get("from") == "QA" and "hello" in m.get("text", "")]
        assert msg, "posted message not found in channel"
        assert "time" in msg[0]


# ---------------------------------------------------------------------------
# GET /api/metrics
# ---------------------------------------------------------------------------

class TestGetMetrics:
    def test_returns_dict(self, client):
        r = client.get("/api/metrics")
        assert r.status_code == 200
        assert isinstance(r.json(), dict)

    def test_counts_reflect_state(self, client):
        client.post("/api/agents/join", json={"role": "PM"})
        client.post("/api/tasks", json={"title": "T1", "created_by": "PM"})
        m = client.get("/api/metrics").json()
        assert m["agents_total"] >= 1
        assert m["tasks_total"] >= 1


# ---------------------------------------------------------------------------
# GET /api/facts
# ---------------------------------------------------------------------------

class TestGetFacts:
    def test_empty(self, client):
        r = client.get("/api/facts")
        assert r.status_code == 200
        assert r.json() == {}

    def test_after_set(self, client):
        client.post("/api/facts", json={"key": "project.name", "value": "APEX", "by_role": "PM"})
        facts = client.get("/api/facts").json()
        assert "project.name" in facts
        assert facts["project.name"] == "APEX"


# ---------------------------------------------------------------------------
# GET /api/debate
# ---------------------------------------------------------------------------

class TestGetDebate:
    def test_null_when_no_debate(self, client):
        r = client.get("/api/debate")
        assert r.status_code == 200
        assert r.json() is None


# ---------------------------------------------------------------------------
# GET /api/findings
# ---------------------------------------------------------------------------

class TestGetFindings:
    def test_empty(self, client):
        r = client.get("/api/findings")
        assert r.status_code == 200
        assert r.json() == []


# ---------------------------------------------------------------------------
# POST /api/tasks
# ---------------------------------------------------------------------------

class TestAddTask:
    def test_creates_task(self, client):
        client.post("/api/agents/join", json={"role": "PM"})
        r = client.post("/api/tasks", json={"title": "Build API", "created_by": "PM", "priority": "high"})
        assert r.status_code == 201
        assert "message" in r.json()

    def test_task_appears_on_board(self, client):
        client.post("/api/agents/join", json={"role": "PM"})
        client.post("/api/tasks", json={"title": "Build API", "created_by": "PM"})
        tasks = client.get("/api/tasks").json()
        titles = [t["title"] for t in tasks]
        assert "Build API" in titles

    def test_task_has_id(self, client):
        client.post("/api/agents/join", json={"role": "PM"})
        client.post("/api/tasks", json={"title": "T1", "created_by": "PM"})
        tasks = client.get("/api/tasks").json()
        assert all("id" in t for t in tasks)

    def test_missing_title_returns_422(self, client):
        r = client.post("/api/tasks", json={})
        assert r.status_code == 422

    def test_priority_stored(self, client):
        client.post("/api/agents/join", json={"role": "PM"})
        client.post("/api/tasks", json={"title": "Urgent", "created_by": "PM", "priority": "high"})
        tasks = client.get("/api/tasks").json()
        t = next(t for t in tasks if t["title"] == "Urgent")
        assert t.get("priority") == "high"


# ---------------------------------------------------------------------------
# PATCH /api/tasks/{id}
# ---------------------------------------------------------------------------

class TestUpdateTask:
    def _create_task(self, client) -> int:
        client.post("/api/agents/join", json={"role": "PM"})
        client.post("/api/tasks", json={"title": "Patchable Task", "created_by": "PM"})
        tasks = client.get("/api/tasks").json()
        return tasks[0]["id"]

    def test_update_status(self, client):
        tid = self._create_task(client)
        r = client.patch(f"/api/tasks/{tid}", json={"status": "in_progress", "by_role": "Backend"})
        assert r.status_code == 200
        tasks = client.get("/api/tasks").json()
        t = next(t for t in tasks if t["id"] == tid)
        assert t["status"] == "in_progress"

    def test_update_assignee(self, client):
        tid = self._create_task(client)
        client.patch(f"/api/tasks/{tid}", json={"assignee": "Frontend"})
        tasks = client.get("/api/tasks").json()
        t = next(t for t in tasks if t["id"] == tid)
        assert t["assignee"] == "Frontend"

    def test_nonexistent_task_returns_404(self, client):
        r = client.patch("/api/tasks/99999", json={"status": "done"})
        assert r.status_code == 404

    def test_mark_done(self, client):
        tid = self._create_task(client)
        r = client.patch(f"/api/tasks/{tid}", json={"status": "done", "by_role": "Backend"})
        assert r.status_code == 200
        tasks = client.get("/api/tasks").json()
        t = next(t for t in tasks if t["id"] == tid)
        assert t["status"] == "done"


# ---------------------------------------------------------------------------
# POST /api/messages
# ---------------------------------------------------------------------------

class TestPostMessage:
    def test_creates_message(self, client):
        client.post("/api/agents/join", json={"role": "QA"})
        r = client.post("/api/messages", json={"sender_role": "QA", "text": "Tests passing"})
        assert r.status_code == 201

    def test_message_in_channel(self, client):
        client.post("/api/agents/join", json={"role": "QA"})
        client.post("/api/messages", json={"sender_role": "QA", "text": "unique-msg-xyz"})
        msgs = client.get("/api/messages").json()["messages"]
        found = any("unique-msg-xyz" in m.get("text", "") for m in msgs)
        assert found

    def test_mention_stored(self, client):
        client.post("/api/agents/join", json={"role": "QA"})
        client.post("/api/messages", json={"sender_role": "QA", "text": "@PM hi", "mention": "PM"})
        msgs = client.get("/api/messages").json()["messages"]
        with_mention = [m for m in msgs if m.get("mention") == "PM"]
        assert with_mention

    def test_missing_sender_role_returns_422(self, client):
        r = client.post("/api/messages", json={"text": "oops"})
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/agents/join
# ---------------------------------------------------------------------------

class TestJoinTeam:
    def test_join_creates_agent(self, client):
        r = client.post("/api/agents/join", json={"role": "Backend", "name": "BackendBot"})
        assert r.status_code == 201
        agents = client.get("/api/agents").json()
        assert "Backend" in agents

    def test_join_missing_role_returns_422(self, client):
        r = client.post("/api/agents/join", json={"name": "NoRole"})
        assert r.status_code == 422

    def test_join_multiple_roles(self, client):
        for role in ("PM", "Backend", "Frontend", "QA"):
            client.post("/api/agents/join", json={"role": role})
        agents = client.get("/api/agents").json()
        assert set(agents.keys()) >= {"PM", "Backend", "Frontend", "QA"}


# ---------------------------------------------------------------------------
# PATCH /api/agents/{role}/status
# ---------------------------------------------------------------------------

class TestSetStatus:
    def test_set_valid_status(self, client):
        client.post("/api/agents/join", json={"role": "QA"})
        r = client.patch("/api/agents/QA/status", json={"status": "idle"})
        assert r.status_code == 200

    def test_invalid_status_returns_400(self, client):
        client.post("/api/agents/join", json={"role": "QA"})
        r = client.patch("/api/agents/QA/status", json={"status": "flying"})
        assert r.status_code == 400

    def test_status_values(self, client):
        client.post("/api/agents/join", json={"role": "Backend"})
        for status in ("idle", "busy", "online", "offline"):
            r = client.patch("/api/agents/Backend/status", json={"status": status})
            assert r.status_code == 200, f"status '{status}' should be valid"


# ---------------------------------------------------------------------------
# POST /api/facts
# ---------------------------------------------------------------------------

class TestSetFact:
    def test_set_and_retrieve(self, client):
        r = client.post("/api/facts", json={"key": "build.version", "value": "2.5", "by_role": "PM"})
        assert r.status_code == 200
        facts = client.get("/api/facts").json()
        assert facts.get("build.version") == "2.5"

    def test_overwrite_fact(self, client):
        client.post("/api/facts", json={"key": "k", "value": "v1"})
        client.post("/api/facts", json={"key": "k", "value": "v2"})
        assert client.get("/api/facts").json()["k"] == "v2"

    def test_missing_key_returns_422(self, client):
        r = client.post("/api/facts", json={"value": "oops"})
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/recovery
# ---------------------------------------------------------------------------

class TestRecovery:
    def test_recovery_returns_200(self, client):
        r = client.post("/api/recovery", json={"stale_seconds": 0, "by_role": "PM"})
        assert r.status_code == 200
        assert "message" in r.json()

    def test_recovery_empty_body_uses_defaults(self, client):
        r = client.post("/api/recovery")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# WebSocket /ws/updates
# ---------------------------------------------------------------------------

class TestWebSocket:
    def test_connect_receives_initial_state(self, client):
        with client.websocket_connect("/ws/updates") as ws:
            data = json.loads(ws.receive_text())
            assert "agents" in data
            assert "tasks" in data
            assert "messages" in data
            assert "metrics" in data

    def test_initial_state_matches_rest(self, client):
        rest_state = client.get("/api/state").json()
        with client.websocket_connect("/ws/updates") as ws:
            ws_state = json.loads(ws.receive_text())
        assert rest_state["agents"] == ws_state["agents"]
        assert rest_state["tasks"] == ws_state["tasks"]

    def test_multiple_clients_can_connect(self, client):
        with client.websocket_connect("/ws/updates") as ws1:
            with client.websocket_connect("/ws/updates") as ws2:
                d1 = json.loads(ws1.receive_text())
                d2 = json.loads(ws2.receive_text())
                assert "metrics" in d1
                assert "metrics" in d2


# ---------------------------------------------------------------------------
# Cross-cutting / integration flow
# ---------------------------------------------------------------------------

class TestEndToEndFlow:
    def test_full_task_lifecycle(self, client):
        """PM creates a task, Backend claims it, finishes it — all via REST."""
        client.post("/api/agents/join", json={"role": "PM"})
        client.post("/api/agents/join", json={"role": "Backend"})

        client.post("/api/tasks", json={"title": "Integrate payment", "created_by": "PM", "priority": "high"})
        tasks = client.get("/api/tasks").json()
        tid = tasks[0]["id"]

        client.patch(f"/api/tasks/{tid}", json={"assignee": "Backend", "by_role": "PM"})
        client.patch(f"/api/tasks/{tid}", json={"status": "in_progress", "by_role": "Backend"})

        metrics_mid = client.get("/api/metrics").json()
        assert metrics_mid["tasks_in_progress"] >= 1

        client.patch(f"/api/tasks/{tid}", json={"status": "done", "by_role": "Backend"})

        tasks_after = client.get("/api/tasks").json()
        done_task = next(t for t in tasks_after if t["id"] == tid)
        assert done_task["status"] == "done"

        metrics_end = client.get("/api/metrics").json()
        assert metrics_end["tasks_done"] >= 1

    def test_message_flow(self, client):
        """Join, post a message with mention, verify it appears in channel."""
        client.post("/api/agents/join", json={"role": "PM"})
        client.post("/api/agents/join", json={"role": "QA"})

        client.post("/api/messages", json={
            "sender_role": "QA", "text": "@PM tests green", "mention": "PM"
        })

        msgs = client.get("/api/messages").json()["messages"]
        pm_mentions = [m for m in msgs if m.get("mention") == "PM"]
        assert pm_mentions

    def test_fact_survives_subsequent_reads(self, client):
        """Facts set in one request persist for later readers."""
        client.post("/api/facts", json={"key": "stack", "value": "Python+FastAPI"})
        for _ in range(3):
            facts = client.get("/api/facts").json()
            assert facts.get("stack") == "Python+FastAPI"

    def test_metrics_increment_on_task_completion(self, client):
        client.post("/api/agents/join", json={"role": "PM"})
        before = client.get("/api/metrics").json()["tasks_done"]

        client.post("/api/tasks", json={"title": "Task X", "created_by": "PM"})
        tasks = client.get("/api/tasks").json()
        tid = tasks[-1]["id"]
        client.patch(f"/api/tasks/{tid}", json={"status": "done"})

        after = client.get("/api/metrics").json()["tasks_done"]
        assert after == before + 1
