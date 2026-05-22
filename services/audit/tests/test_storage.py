"""Tests for append-only SQLite storage."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import pytest_asyncio

from audit.chain import GENESIS_HASH, compute_entry_hash
from audit.storage import SQLiteStorage
from centinela.models import AuditEntry


def _make_entry(
    i: int,
    prev_hash: str,
    correlation_id: str = "corr-001",
    actor: str = "red-agent",
    event_type: str = "prompt_sent",
) -> AuditEntry:
    ts = datetime(2024, 1, 1, 0, 0, i, tzinfo=timezone.utc)
    ts_str = ts.isoformat()
    eh = compute_entry_hash(ts_str, actor, event_type, f"hash-{i}", prev_hash, correlation_id)
    return AuditEntry(
        timestamp=ts,
        actor=actor,
        event_type=event_type,
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


@pytest.mark.asyncio
async def test_empty_chain_head(storage: SQLiteStorage) -> None:
    head = await storage.get_chain_head()
    assert head == GENESIS_HASH


@pytest.mark.asyncio
async def test_append_single(storage: SQLiteStorage) -> None:
    entry = _make_entry(0, GENESIS_HASH)
    await storage.append(entry)
    head = await storage.get_chain_head()
    assert head == entry.entry_hash


@pytest.mark.asyncio
async def test_append_batch(storage: SQLiteStorage) -> None:
    entries = []
    prev = GENESIS_HASH
    for i in range(5):
        e = _make_entry(i, prev)
        entries.append(e)
        prev = e.entry_hash

    await storage.append_batch(entries)
    all_entries = await storage.get_all_entries()
    assert len(all_entries) == 5


@pytest.mark.asyncio
async def test_get_entries_filter_correlation(storage: SQLiteStorage) -> None:
    entries = []
    prev = GENESIS_HASH
    for i in range(4):
        corr = "corr-A" if i % 2 == 0 else "corr-B"
        e = _make_entry(i, prev, correlation_id=corr)
        entries.append(e)
        prev = e.entry_hash

    await storage.append_batch(entries)

    a_entries = await storage.get_entries(correlation_id="corr-A")
    assert len(a_entries) == 2
    for e in a_entries:
        assert e.correlation_id == "corr-A"


@pytest.mark.asyncio
async def test_get_entries_pagination(storage: SQLiteStorage) -> None:
    entries = []
    prev = GENESIS_HASH
    for i in range(10):
        e = _make_entry(i, prev)
        entries.append(e)
        prev = e.entry_hash

    await storage.append_batch(entries)

    page = await storage.get_entries(limit=3, offset=2)
    assert len(page) == 3


@pytest.mark.asyncio
async def test_get_all_entries_ordered(storage: SQLiteStorage) -> None:
    entries = []
    prev = GENESIS_HASH
    for i in range(5):
        e = _make_entry(i, prev)
        entries.append(e)
        prev = e.entry_hash

    await storage.append_batch(entries)
    all_entries = await storage.get_all_entries()
    assert len(all_entries) == 5
    for i in range(len(all_entries) - 1):
        assert all_entries[i].timestamp <= all_entries[i + 1].timestamp
