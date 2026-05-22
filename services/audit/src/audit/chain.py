"""SHA-256 Merkle hash chain for tamper-evident audit logging."""

from __future__ import annotations

import hashlib
import json

# The "genesis" hash — used as prev_hash for the very first entry.
# Fixed constant so the chain always starts from the same point.
GENESIS_HASH = "0" * 64  # SHA-256 produces 64 hex characters


def compute_entry_hash(
    timestamp: str,
    actor: str,
    event_type: str,
    payload_hash: str,
    prev_hash: str,
    correlation_id: str,
) -> str:
    """Compute SHA-256 hash of an audit entry.

    The hash covers ALL fields in a deterministic JSON serialization.
    Any single-byte modification to any field breaks the chain.

    Returns:
        64-character hex string (SHA-256 digest).
    """
    data = json.dumps(
        {
            "timestamp": timestamp,
            "actor": actor,
            "event_type": event_type,
            "payload_hash": payload_hash,
            "prev_hash": prev_hash,
            "correlation_id": correlation_id,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(data).hexdigest()


class MerkleChain:
    """Manages a Merkle-chained audit log.

    Tracks the current chain head (hash of the most recent entry) and
    computes new entry hashes that link to the chain.
    """

    def __init__(self, head: str = GENESIS_HASH) -> None:
        self._head = head

    @property
    def head(self) -> str:
        """Hash of the most recent entry in the chain."""
        return self._head

    def append(
        self,
        timestamp: str,
        actor: str,
        event_type: str,
        payload_hash: str,
        correlation_id: str,
    ) -> str:
        """Compute the hash for a new entry and update the chain head.

        Returns:
            The new entry's hash (which becomes the next entry's prev_hash).
        """
        entry_hash = compute_entry_hash(
            timestamp=timestamp,
            actor=actor,
            event_type=event_type,
            payload_hash=payload_hash,
            prev_hash=self._head,
            correlation_id=correlation_id,
        )
        self._head = entry_hash
        return entry_hash

    def verify_chain(self, entries: list[dict]) -> tuple[bool, int | None]:  # type: ignore[type-arg]
        """Verify the integrity of a chain of entries.

        Recomputes every hash and confirms chain integrity.
        Detects any single-byte modification in any entry.

        Args:
            entries: List of entry dicts with keys matching AuditEntry fields.

        Returns:
            (True, None) if valid; (False, first_invalid_index) if tampered.
        """
        if not entries:
            return True, None

        current_hash = GENESIS_HASH

        for i, entry in enumerate(entries):
            computed = compute_entry_hash(
                timestamp=entry["timestamp"],
                actor=entry["actor"],
                event_type=entry["event_type"],
                payload_hash=entry["payload_hash"],
                prev_hash=current_hash,
                correlation_id=entry["correlation_id"],
            )

            if computed != entry["entry_hash"]:
                return False, i

            current_hash = entry["entry_hash"]

        return True, None
