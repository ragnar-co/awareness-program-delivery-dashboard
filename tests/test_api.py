import importlib
import io
import os

import pytest
from fastapi.testclient import TestClient

from tests.conftest import SAMPLE_CSV


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHBOARD_DB_PATH", str(tmp_path / "api_test.db"))
    monkeypatch.setenv("DASHBOARD_AS_OF", "2026-10-02")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    from app import db, ingest, analytics, ai_workflow, main
    for mod in (db, ingest, analytics, ai_workflow, main):
        importlib.reload(mod)

    with TestClient(main.app) as test_client:
        test_client.post(
            "/api/ingest",
            files={"file": ("sample.csv", io.BytesIO(SAMPLE_CSV.encode()), "text/csv")},
        )
        yield test_client


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_clients_lists_both(client):
    data = client.get("/api/clients").json()
    assert sorted(data["clients"]) == ["Acme Corp", "Globex Inc"]


def test_summary_endpoint(client):
    data = client.get("/api/summary").json()
    assert data["overall"]["total"] == 5
    assert data["overall"]["overdue"] == 3


def test_summary_filtered_by_client(client):
    data = client.get("/api/summary", params={"client": "Acme Corp"}).json()
    assert data["overall"]["total"] == 3


def test_pending_acceptance_endpoint(client):
    data = client.get("/api/deliverables/pending-acceptance").json()
    ids = {i["deliverable_id"] for i in data["items"]}
    assert ids == {"D002", "D004"}


def test_overdue_endpoint_excludes_accepted(client):
    data = client.get("/api/deliverables/overdue").json()
    ids = {i["deliverable_id"] for i in data["items"]}
    assert "D001" not in ids


def test_ai_draft_without_api_key_returns_503(client):
    res = client.post("/api/ai/draft-update", params={"client": "Acme Corp"})
    assert res.status_code == 503
