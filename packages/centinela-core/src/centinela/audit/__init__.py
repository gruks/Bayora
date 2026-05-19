"""Audit logging module for centinela."""

import asyncio
from typing import Any

from centinela.enums import EventType
from centinela.models.types import AuditRecord

from .chain import AuditChain


class AuditClient:
    """Asynchronous client for audit operations."""

    def __init__(self) -> None:
        """Initialize the audit client."""
        self.chain = AuditChain()

    async def append(
        self,
        event_type: EventType | str,
        actor: str | None = None,
        resource: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> AuditRecord:
        """Asynchronously append an entry to the audit chain."""
        return await asyncio.to_thread(
            self.chain.append, event_type, actor, resource, payload
        )


__all__ = ["AuditChain", "AuditClient", "AuditRecord"]
