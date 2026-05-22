"""Tests for AuditVerifier — chain verification and forensic queries."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import pytest_asyncio

from audit.chain import GENESIS_HASH, compute_entry_hash
from audit.storage import SQLiteStorage
from audit.verify import AuditVerifier
from centinela.models import AuditEntry


def _make_entry(i: int, prev_hash: str, correlation_id: str = "corr-001") -> AuditEntry:
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
    for i in range(10):
        e = _make_entry(i, prev)
        entries.append(e)
        prev = e.entry_hash
    await storage.append_batch(entries)
    return storage


@pytest.mark.asyncio
async def test_verify_empty_chain(storage: SQLiteStorage) -> None:
    verifier = AuditVerifier(storage)
    result = await verifier.verify()
    assert result.is_valid is True
    assert result.total_entries == 0
    assert result.chain_head == GENESIS_HASH


@pytest.mark.asyncio
async def test_verify_valid_chain(populated_storage: SQLiteStorage) -> None:
    verifier = AuditVerifier(populated_storage)
    result = await verifier.verify()
    assert result.is_valid is True
    assert result.total_entries == 10
    assert result.verified_entries == 10
    assert result.first_invalid_index is None


@pytest.mark.asyncio
async def test_verify_tampered_chain(populated_storage: SQLiteStorage) -> None:
    # Tamper with entry 6 (id=6, 1-indexed)
    await populated_storage._db.execute(
        "UPDATE audit_entries SET payload_hash = 'TAMPERED' WHERE id = 6"
    )
    await populated_storage._db.commit()

    verifier = AuditVerifier(populated_storage)
    result = await verifier.verify()
    assert result.is_valid is False
    assert result.first_invalid_index is not None


@pytest.mark.asyncio
async def test_verify_by_correlation_id(populated_storage: SQLiteStorage) -> None:
    verifier = AuditVerifier(populated_storage)
    result = await verifier.verify_by_correlation_id("corr-001")
    assert result.is_valid is True
    assert result.total_entries == 10


@pytest.mark.asyncio
async def test_verify_nonexistent_correlation_id(populated_storage: SQLiteStorage) -> None:
    verifier = AuditVerifier(populated_storage)
    result = await verifier.verify_by_correlation_id("nonexistent")
    assert result.is_valid is False
    assert result.error_message is not None


@pytest.mark.asyncio
async def test_get_correlation_events(populated_storage: SQLiteStorage) -> None:
    verifier = AuditVerifier(populated_storage)
    events = await verifier.get_correlation_events("corr-001")
    assert len(events) == 10
    for i in range(len(events) - 1):
        assert events[i].timestamp <= events[i + 1].timestamp


@pytest.mark.asyncio
async def test_verification_performance(storage: SQLiteStorage) -> None:
    """Verify 10K entries completes in <1s."""
    entries = []
    prev = GENESIS_HASH
    for i in range(10_000):
        ts = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        ts_str = ts.isoformat()
        eh = compute_entry_hash(ts_str, "perf-test", "perf-event", f"hash-{i}", prev, "perf-corr")
        entries.append(
            AuditEntry(
                timestamp=ts,
                actor="perf-test",
                event_type="perf-event",
                payload_hash=f"hash-{i}",
                prev_hash=prev,
                correlation_id="perf-corr",
                entry_hash=eh,
            )
        )
        prev = eh

    for i in range(0, len(entries), 1000):
        await storage.append_batch(entries[i : i + 1000])

    verifier = AuditVerifier(storage)
    result = await verifier.verify()

    assert result.is_valid is True
    assert result.total_entries == 10_000
    assert result.duration_ms < 1000, f"Took {result.duration_ms}ms (limit: 1000ms)"
