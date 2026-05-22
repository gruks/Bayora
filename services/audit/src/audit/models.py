"""Service-level types for creating and querying audit entries."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AuditEntryCreate(BaseModel):
    """Input for creating a new audit entry.

    The caller provides the SHA-256 hash of the payload (never the payload itself).
    For red-agent prompts, this is the hash of the prompt text — the prompt is never stored.
    """

    model_config = {"frozen": True}

    actor: str
    event_type: str
    payload_hash: str
    correlation_id: str


class AuditEntryQuery(BaseModel):
    """Query parameters for reading audit entries."""

    model_config = {"frozen": True}

    correlation_id: str | None = None
    event_type: str | None = None
    actor: str | None = None
    limit: int = 100
    offset: int = 0


class AuditEvent(BaseModel):
    """Internal event representation before hashing.

    Used by the writer to construct entries before they are hashed and stored.
    """

    model_config = {"frozen": True}

    timestamp: datetime
    actor: str
    event_type: str
    payload_hash: str
    prev_hash: str
    correlation_id: str
