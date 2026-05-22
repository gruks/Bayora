"""Tests for AsyncAuditWriter — non-blocking write interface."""

from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio

from audit.chain import GENESIS_HASH
from audit.models import AuditEntryCreate
from audit.storage import SQLiteStorage
from audit.writer import AsyncAuditWriter


@pytest_asyncio.fixture
async def writer() -> AsyncAuditWriter:
    storage = SQLiteStorage(":memory:")
    w = AsyncAuditWriter(storage)
    await w.start()
    yield w
    await w.stop()


@pytest.mark.asyncio
async def test_write_single_entry(writer: AsyncAuditWriter) -> None:
    create = AuditEntryCreate(
        actor="red-agent",
        event_type="prompt_sent",
        payload_hash="abc123",
        correlation_id="corr-001",
    )
    writer.write(create)
    await asyncio.sleep(0.05)  # let background task process

    entries = await writer._storage.get_all_entries()
    assert len(entries) == 1
    assert entries[0].actor == "red-agent"
    assert entries[0].prev_hash == GENESIS_HASH


@pytest.mark.asyncio
async def test_write_chain_linkage(writer: AsyncAuditWriter) -> None:
    for i in range(3):
        create = AuditEntryCreate(
            actor="red-agent",
            event_type="prompt_sent",
            payload_hash=f"hash-{i}",
            correlation_id="corr-001",
        )
        await writer.write_async(create)

    await asyncio.sleep(0.1)

    entries = await writer._storage.get_all_entries()
    assert len(entries) == 3
    # Verify chain linkage
    assert entries[0].prev_hash == GENESIS_HASH
    assert entries[1].prev_hash == entries[0].entry_hash
    assert entries[2].prev_hash == entries[1].entry_hash


@pytest.mark.asyncio
async def test_write_does_not_raise_on_failure() -> None:
    """write() must never raise even if storage fails."""
    storage = SQLiteStorage(":memory:")
    w = AsyncAuditWriter(storage)
    await w.start()

    # Close storage to force failure
    await storage.close()

    create = AuditEntryCreate(
        actor="red-agent",
        event_type="prompt_sent",
        payload_hash="abc123",
        correlation_id="corr-001",
    )
    # Should not raise
    w.write(create)
    await asyncio.sleep(0.05)
    # Stop without error
    w._queue.put_nowait(None)
    if w._task:
        await asyncio.wait_for(w._task, timeout=1.0)
