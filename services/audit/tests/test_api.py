"""Tests for the read-only audit query API."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from audit.api import create_app
from audit.chain import GENESIS_HASH, compute_entry_hash
from audit.storage import SQLiteStorage
from centinela.models import AuditEntry


def _make_entry(i: int, prev_hash: str, correlation_id: str = "corr-0") -> AuditEntry:
    ts = datetime(2024, 1, 1, 0, 0, i, tzinfo=timezone.utc)
    ts_str = ts.isoformat()
    eh = compute_entry_hash(ts_str, f"actor-{i}", f"event-{i}", f"hash-{i}", prev_hash, correlation_id)
    return AuditEntry(
        timestamp=ts,
        actor=f"actor-{i}",
        event_type=f"event-{i}",
        payload_hash=f"hash-{i}",
        prev_hash=prev_hash,
        correlation_id=correlation_id,
        entry_hash=eh,
    )


@pytest_asyncio.fixture
async def storage() -> SQLiteStorage:
    s = SQLiteStorage(":memory:")
    await s.initialize()
    yield s
    await s.close()


@pytest_asyncio.fixture
async def populated_storage(storage: SQLiteStorage) -> SQLiteStorage:
    entries = []
    prev = GENESIS_HASH
    for i in range(5):
        corr = f"corr-{i % 2}"
        e = _make_entry(i, prev, correlation_id=corr)
        entries.append(e)
        prev = e.entry_hash
    await storage.append_batch(entries)
    return storage


@pytest.fixture
def client(storage: SQLiteStorage) -> TestClient:
    app = create_app(storage)
    return TestClient(app)


@pytest.fixture
def populated_client(populated_storage: SQLiteStorage) -> TestClient:
    app = create_app(populated_storage)
    return TestClient(app)


def test_health_no_auth(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_entries_requires_auth(client: TestClient) -> None:
    response = client.get("/entries")
    assert response.status_code == 401


def test_entries_invalid_key(client: TestClient) -> None:
    response = client.get("/entries", headers={"X-API-Key": "invalid"})
    assert response.status_code == 403


def test_entries_with_auth(populated_client: TestClient) -> None:
    response = populated_client.get("/entries", headers={"X-API-Key": "dev-admin-key"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["entries"]) == 5


def test_entries_filter_by_correlation_id(populated_client: TestClient) -> None:
    response = populated_client.get(
        "/entries?correlation_id=corr-0", headers={"X-API-Key": "dev-admin-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3  # entries 0, 2, 4
    for entry in data["entries"]:
        assert entry["correlation_id"] == "corr-0"


def test_entries_pagination(populated_client: TestClient) -> None:
    response = populated_client.get(
        "/entries?limit=2&offset=1", headers={"X-API-Key": "dev-admin-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["limit"] == 2
    assert data["offset"] == 1


def test_entries_by_correlation_id(populated_client: TestClient) -> None:
    response = populated_client.get(
        "/entries/corr-0", headers={"X-API-Key": "dev-auditor-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["correlation_id"] == "corr-0"
    assert data["total"] == 3


def test_entries_by_correlation_id_not_found(populated_client: TestClient) -> None:
    response = populated_client.get(
        "/entries/nonexistent", headers={"X-API-Key": "dev-auditor-key"}
    )
    assert response.status_code == 404


def test_chain_head_admin_only(populated_client: TestClient) -> None:
    response = populated_client.get("/chain/head", headers={"X-API-Key": "dev-admin-key"})
    assert response.status_code == 200
    assert "chain_head" in response.json()

    response = populated_client.get("/chain/head", headers={"X-API-Key": "dev-auditor-key"})
    assert response.status_code == 403
