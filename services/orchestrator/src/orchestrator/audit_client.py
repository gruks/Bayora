"""Audit client for orchestrator to log events to audit service."""

from __future__ import annotations

import httpx
from typing import Any
from pydantic import BaseModel


class AuditEvent(BaseModel):
    """Audit event to log."""

    session_id: str
    event_type: str
    data: dict[str, Any]


class AuditClient:
    """HTTP client for audit service."""

    def __init__(self, base_url: str = "http://audit:8081"):
        self.base_url = base_url
        self._client = httpx.Client(timeout=30.0)

    def log_event(self, session_id: str, event_type: str, data: dict[str, Any]) -> bool:
        """Log event to audit service."""
        try:
            response = self._client.post(
                f"{self.base_url}/audit/log",
                json={"session_id": session_id, "event_type": event_type, "data": data},
            )
            return response.status_code == 200
        except httpx.RequestError:
            return False

    def verify_session(self, session_id: str) -> dict[str, Any]:
        """Verify audit chain for session."""
        response = self._client.get(f"{self.base_url}/audit/verify/{session_id}")
        return response.json() if response.status_code == 200 else {"valid": False}

    def get_merkle_root(self, session_id: str) -> str:
        """Get Merkle root for session."""
        response = self._client.get(f"{self.base_url}/audit/merkle/{session_id}")
        return response.json().get("root", "") if response.status_code == 200 else ""

    def close(self):
        self._client.close()
