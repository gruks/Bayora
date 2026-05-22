"""Audit chain verifier — recomputes every hash and confirms chain integrity."""

from __future__ import annotations

import time
from dataclasses import dataclass

from centinela.models import AuditEntry

from .chain import GENESIS_HASH, MerkleChain
from .storage import AppendOnlyStorage


@dataclass(frozen=True)
class VerificationResult:
    """Result of an audit chain verification."""

    is_valid: bool
    total_entries: int
    verified_entries: int
    first_invalid_index: int | None
    duration_ms: float
    chain_head: str
    error_message: str | None = None


class AuditVerifier:
    """Verifies the integrity of an audit chain.

    Recomputes every hash from scratch and confirms the chain is unbroken.
    Any single-byte modification in any entry will be detected.
    """

    def __init__(self, storage: AppendOnlyStorage) -> None:
        self._storage = storage

    async def verify(self) -> VerificationResult:
        """Verify the entire audit chain."""
        start = time.perf_counter()
        entries = await self._storage.get_all_entries()
        total = len(entries)

        if total == 0:
            elapsed = (time.perf_counter() - start) * 1000
            return VerificationResult(
                is_valid=True,
                total_entries=0,
                verified_entries=0,
                first_invalid_index=None,
                duration_ms=round(elapsed, 2),
                chain_head=GENESIS_HASH,
            )

        entry_dicts = [
            {
                "timestamp": e.timestamp.isoformat(),
                "actor": e.actor,
                "event_type": e.event_type,
                "payload_hash": e.payload_hash,
                "prev_hash": e.prev_hash,
                "correlation_id": e.correlation_id,
                "entry_hash": e.entry_hash,
            }
            for e in entries
        ]

        chain = MerkleChain()
        is_valid, first_invalid = chain.verify_chain(entry_dicts)
        elapsed = (time.perf_counter() - start) * 1000
        verified = total if is_valid else (first_invalid or 0)

        return VerificationResult(
            is_valid=is_valid,
            total_entries=total,
            verified_entries=verified,
            first_invalid_index=first_invalid,
            duration_ms=round(elapsed, 2),
            chain_head=entries[-1].entry_hash,
            error_message=None if is_valid else f"Chain broken at entry {first_invalid}",
        )

    async def verify_by_correlation_id(self, correlation_id: str) -> VerificationResult:
        """Verify only entries matching a specific correlation ID."""
        start = time.perf_counter()
        entries = await self._storage.get_entries(correlation_id=correlation_id)
        total = len(entries)

        if total == 0:
            elapsed = (time.perf_counter() - start) * 1000
            return VerificationResult(
                is_valid=False,
                total_entries=0,
                verified_entries=0,
                first_invalid_index=None,
                duration_ms=round(elapsed, 2),
                chain_head=GENESIS_HASH,
                error_message=f"No entries found for correlation_id: {correlation_id}",
            )

        entry_dicts = [
            {
                "timestamp": e.timestamp.isoformat(),
                "actor": e.actor,
                "event_type": e.event_type,
                "payload_hash": e.payload_hash,
                "prev_hash": e.prev_hash,
                "correlation_id": e.correlation_id,
                "entry_hash": e.entry_hash,
            }
            for e in entries
        ]

        chain = MerkleChain()
        is_valid, first_invalid = chain.verify_chain(entry_dicts)
        elapsed = (time.perf_counter() - start) * 1000
        verified = total if is_valid else (first_invalid or 0)

        return VerificationResult(
            is_valid=is_valid,
            total_entries=total,
            verified_entries=verified,
            first_invalid_index=first_invalid,
            duration_ms=round(elapsed, 2),
            chain_head=entries[-1].entry_hash,
            error_message=None if is_valid else f"Chain broken at entry {first_invalid}",
        )

    async def get_correlation_events(self, correlation_id: str) -> list[AuditEntry]:
        """Get all events for a correlation ID in chronological order."""
        return await self._storage.get_entries(
            correlation_id=correlation_id,
            limit=100_000,
        )
