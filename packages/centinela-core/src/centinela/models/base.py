"""Base models for CENTINELA — session config and audit entries."""

from datetime import datetime

from pydantic import BaseModel


class SessionConfig(BaseModel):
    max_api_calls: int = 50
    max_budget_usd: float = 5.0


class AuditEntry(BaseModel):
    timestamp: datetime = datetime.now()
    event_type: str
    payload_hash: str
    prev_hash: str | None = None
