"""Audit module for tamper-evident logging."""

import asyncio
from typing import Any

from .chain import AuditChain, AuditEntry


class AuditClient:
    """Async wrapper for audit chain operations."""

    def __init__(self, chain: AuditChain | None = None):
        self._chain = chain or AuditChain()

    @property
    def chain(self) -> AuditChain:
        """Get the underlying audit chain."""
        return self._chain

    async def append(
        self,
        event_type: Any,
        actor: str,
        resource: str,
        payload: dict | None = None,
    ) -> AuditEntry:
        """Asynchronously append an entry to the audit chain."""
        return await asyncio.to_thread(self._chain.append, event_type, actor, resource, payload)

    async def verify(self) -> bool:
        """Asynchronously verify chain integrity."""
        return await asyncio.to_thread(self._chain.verify)

    async def get_root_hash(self) -> str:
        """Asynchronously get the root hash."""
        return await asyncio.to_thread(self._chain.get_root_hash)


__all__ = ["AuditChain", "AuditEntry", "AuditClient"]
