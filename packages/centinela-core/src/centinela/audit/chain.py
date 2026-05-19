"""Audit chain module for tamper-evident logging."""

import hashlib
import json
from typing import Any
from uuid import uuid4

from centinela.enums import EventType
from centinela.models.types import AuditRecord


class AuditChain:
    """Tamper-evident audit chain using SHA-256 hash chaining."""

    def __init__(self) -> None:
        """Initialize an empty audit chain."""
        self._entries: list[AuditRecord] = []

    def append(
        self,
        event_type: EventType | str,
        actor: str | None = None,
        resource: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> AuditRecord:
        """Append a new record to the audit chain."""
        entry_id = str(uuid4())
        payload_dict = payload or {}
        prev_hash = self.get_root_hash() if self._entries else None

        record = AuditRecord(
            entry_id=entry_id,
            event_type=str(event_type),
            actor=actor,
            resource=resource,
            payload=payload_dict,
            prev_hash=prev_hash,
        )
        self._entries.append(record)
        return record

    def get_root_hash(self) -> str:
        """Get the hash of the last entry in the chain."""
        if not self._entries:
            return ""
        return self._compute_hash(self._entries[-1])

    def _compute_hash(self, record: AuditRecord) -> str:
        """Compute the SHA-256 hash of an audit record."""
        payload_str = json.dumps(record.payload, sort_keys=True)
        data = (
            f"{record.entry_id}{record.timestamp.isoformat()}"
            f"{record.event_type}{record.actor or ''}{payload_str}"
            f"{record.prev_hash or ''}"
        )
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def verify(self) -> bool:
        """Verify the cryptographic integrity of the audit chain."""
        if not self._entries:
            return True

        expected_prev_hash = None
        for record in self._entries:
            if record.prev_hash != expected_prev_hash:
                return False
            expected_prev_hash = self._compute_hash(record)
        return True
