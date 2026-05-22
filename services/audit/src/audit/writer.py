"""Non-blocking async audit writer — fire-and-forget write interface."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from centinela.models import AuditEntry

from .chain import MerkleChain, compute_entry_hash
from .models import AuditEntryCreate
from .storage import AppendOnlyStorage

logger = logging.getLogger(__name__)


class AsyncAuditWriter:
    """Non-blocking write interface for the audit log.

    Writes are enqueued and processed asynchronously.
    Failures are logged but never raised to callers — audit failures
    must not halt test execution.
    """

    def __init__(self, storage: AppendOnlyStorage, queue_size: int = 10_000) -> None:
        self._storage = storage
        self._queue: asyncio.Queue[AuditEntryCreate | None] = asyncio.Queue(
            maxsize=queue_size
        )
        self._chain = MerkleChain()
        self._task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Initialize storage and start the background writer task."""
        await self._storage.initialize()
        # Restore chain head from storage
        head = await self._storage.get_chain_head()
        self._chain = MerkleChain(head=head)
        self._task = asyncio.create_task(self._process_queue())

    async def stop(self) -> None:
        """Drain the queue and stop the background writer."""
        await self._queue.put(None)  # sentinel
        if self._task:
            await self._task
        await self._storage.close()

    def write(self, create: AuditEntryCreate) -> None:
        """Enqueue an entry for writing. Non-blocking, never raises.

        If the queue is full, the entry is dropped and a warning is logged.
        """
        try:
            self._queue.put_nowait(create)
        except asyncio.QueueFull:
            logger.warning(
                "Audit queue full — dropping entry actor=%s event_type=%s",
                create.actor,
                create.event_type,
            )

    async def write_async(self, create: AuditEntryCreate) -> None:
        """Enqueue an entry, waiting if the queue is full."""
        await self._queue.put(create)

    async def _process_queue(self) -> None:
        """Background task: drain the queue and persist entries."""
        while True:
            item = await self._queue.get()
            if item is None:
                break
            try:
                await self._persist(item)
            except Exception:
                logger.exception(
                    "Failed to persist audit entry actor=%s event_type=%s",
                    item.actor,
                    item.event_type,
                )
            finally:
                self._queue.task_done()

    async def _persist(self, create: AuditEntryCreate) -> None:
        """Build a chained AuditEntry and append it to storage."""
        async with self._lock:
            ts = datetime.now(timezone.utc)
            ts_str = ts.isoformat()
            prev_hash = self._chain.head

            entry_hash = compute_entry_hash(
                timestamp=ts_str,
                actor=create.actor,
                event_type=create.event_type,
                payload_hash=create.payload_hash,
                prev_hash=prev_hash,
                correlation_id=create.correlation_id,
            )

            entry = AuditEntry(
                timestamp=ts,
                actor=create.actor,
                event_type=create.event_type,
                payload_hash=create.payload_hash,
                prev_hash=prev_hash,
                correlation_id=create.correlation_id,
                entry_hash=entry_hash,
            )

            await self._storage.append(entry)
            # Update chain head only after successful persist
            self._chain = MerkleChain(head=entry_hash)
