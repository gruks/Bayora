"""Audit chain implementation with SHA-256 hash chaining."""

import hashlib
import json
from datetime import datetime
from uuid import UUID, uuid4

from centinela.enums import EventType


class AuditEntry:
    """A single entry in the audit chain."""

    def __init__(
        self,
        entry_id: UUID,
        timestamp: datetime,
        event_type: EventType,
        actor: str,
        resource: str,
        payload: dict,
        prev_hash: str | None,
    ):
        self.entry_id = entry_id
        self.timestamp = timestamp
        self.event_type = event_type
        self.actor = actor
        self.resource = resource
        self.payload = payload
        self.prev_hash = prev_hash
        self._hash: str | None = None

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of this entry."""
        payload_str = json.dumps(self.payload, sort_keys=True, default=str)
        hash_input = (
            str(self.entry_id)
            + self.timestamp.isoformat()
            + str(self.event_type.value)
            + self.actor
            + self.resource
            + payload_str
            + (self.prev_hash or "")
        )
        return hashlib.sha256(hash_input.encode()).hexdigest()

    @property
    def hash(self) -> str:
        """Get the hash of this entry, computing if necessary."""
        if self._hash is None:
            self._hash = self.compute_hash()
        return self._hash

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "entry_id": str(self.entry_id),
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "actor": self.actor,
            "resource": self.resource,
            "payload": self.payload,
            "prev_hash": self.prev_hash,
            "hash": self.hash,
        }


class AuditChain:
    """Tamper-evident audit log with SHA-256 hash chaining."""

    def __init__(self):
        self._entries: list[AuditEntry] = []
        self._root_hash: str | None = None

    def append(
        self,
        event_type: EventType,
        actor: str,
        resource: str,
        payload: dict | None = None,
    ) -> AuditEntry:
        """Append a new entry to the audit chain."""
        if payload is None:
            payload = {}

        prev_hash = self._entries[-1].hash if self._entries else None

        entry = AuditEntry(
            entry_id=uuid4(),
            timestamp=datetime.now(),
            event_type=event_type,
            actor=actor,
            resource=resource,
            payload=payload,
            prev_hash=prev_hash,
        )

        self._entries.append(entry)

        # Update root hash
        self._root_hash = entry.hash

        return entry

    def verify(self) -> bool:
        """Verify the integrity of the entire chain."""
        if not self._entries:
            return True

        # Verify first entry has no prev_hash
        if self._entries[0].prev_hash is not None:
            return False

        # Verify each entry's hash and prev_hash link
        for i, entry in enumerate(self._entries):
            computed_hash = entry.compute_hash()
            if entry.hash != computed_hash:
                return False

            if i > 0:
                if entry.prev_hash != self._entries[i - 1].hash:
                    return False

        return True

    def get_root_hash(self) -> str:
        """Get the hash of the last entry in the chain."""
        if not self._entries:
            return ""
        return self._entries[-1].hash

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self):
        return iter(self._entries)

    def __getitem__(self, index: int) -> AuditEntry:
        return self._entries[index]


__all__ = ["AuditChain", "AuditEntry"]
