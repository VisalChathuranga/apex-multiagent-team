"""
Shared pytest fixtures for the APEX Team API integration test suite.

Run with: python -m pytest tests/ -v
(Use the Python environment that has mcp, fastapi, httpx installed)
"""

import json
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import team_coordinator as tc
import api_server


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
    """Isolate each test to a fresh temporary state file."""
    state_file = tmp_path / "test_state.json"
    state_file.write_text(json.dumps(MINIMAL_STATE, indent=2), encoding="utf-8")
    lock_file = tmp_path / "test_state.json.lock"
    monkeypatch.setattr(tc, "STATE_FILE", state_file)
    monkeypatch.setattr(tc, "LOCK_FILE", lock_file)
    return state_file


@pytest.fixture()
def client(tmp_state):
    """FastAPI TestClient with isolated state for each test."""
    with TestClient(api_server.app, raise_server_exceptions=True) as c:
        yield c
