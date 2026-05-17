"""Audit chain module with hash chain and Merkle tree for tamper-evident logging."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class AuditEntry:
    """Single audit log entry with hash chain linkage."""

    entry_id: str
    timestamp: str
    session_id: str
    event_type: str
    data: dict[str, Any]
    prev_hash: str
    hash: str


class AuditChain:
    """Hash chain with Merkle tree for audit log."""

    def __init__(self, db_path: str = "/data/audit.db"):
        self.db_path = db_path
        self._entries: list[AuditEntry] = []

    def log_event(self, session_id: str, event_type: str, data: dict[str, Any]) -> AuditEntry:
        """Log an event to the audit chain."""
        # Compute previous hash
        prev_hash = self._entries[-1].hash if self._entries else "0" * 64

        # Create entry
        entry = AuditEntry(
            entry_id=self._generate_id(),
            timestamp=datetime.utcnow().isoformat(),
            session_id=session_id,
            event_type=event_type,
            data=data,
            prev_hash=prev_hash,
            hash="",
        )

        # Compute hash (includes prev_hash for chain integrity)
        entry.hash = self._compute_hash(entry)
        self._entries.append(entry)
        return entry

    def _compute_hash(self, entry: AuditEntry) -> str:
        """Compute SHA-256 hash of entry."""
        content = f"{entry.entry_id}{entry.timestamp}{entry.session_id}{entry.event_type}{json.dumps(entry.data, sort_keys=True)}{entry.prev_hash}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _generate_id(self) -> str:
        return uuid.uuid4().hex

    def verify_chain(self, session_id: str) -> bool:
        """Verify hash chain integrity for a session."""
        session_entries = [e for e in self._entries if e.session_id == session_id]
        for i in range(1, len(session_entries)):
            if session_entries[i].prev_hash != session_entries[i - 1].hash:
                return False
            if session_entries[i].hash != self._compute_hash(session_entries[i]):
                return False
        return True

    def get_merkle_root(self, session_id: str) -> str:
        """Get Merkle root hash for session (CERT-07)."""
        session_entries = [e for e in self._entries if e.session_id == session_id]
        if not session_entries:
            return ""

        # Build Merkle tree
        hashes = [e.hash for e in session_entries]
        while len(hashes) > 1:
            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])
            new_level = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i + 1]
                new_level.append(hashlib.sha256(combined.encode()).hexdigest())
            hashes = new_level
        return hashes[0] if hashes else ""

    def get_entries(self, session_id: str) -> list[AuditEntry]:
        """Get all entries for a session."""
        return [e for e in self._entries if e.session_id == session_id]
