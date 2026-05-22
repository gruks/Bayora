"""Base models for CENTINELA — session config and audit entries."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SessionConfig(BaseModel):
    max_api_calls: int = 50
    max_budget_usd: float = 5.0


class AuditEntry(BaseModel):
    """Tamper-evident audit log entry with SHA-256 Merkle chain linkage.

    The entry_hash field is computed from all other fields and becomes
    the prev_hash of the next entry in the chain.
    """

    model_config = {"frozen": True}

    timestamp: datetime
    actor: str
    event_type: str
    payload_hash: str
    prev_hash: str
    correlation_id: str
    entry_hash: str = ""  # Computed after construction
    signature: str = ""  # Ed25519 signature (added in batch signing)
