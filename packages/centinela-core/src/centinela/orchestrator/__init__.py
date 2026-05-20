"""Orchestrator and session management module."""

from abc import ABC, abstractmethod
from uuid import UUID

from prometheus_client import Counter, Gauge

from centinela.models.types import Session

from .session import PlatformConfig, SessionManager

session_count = Gauge(
    "centinela_session_count", "Current number of sessions", ["state"]
)
session_duration = Gauge(
    "centinela_session_duration_seconds", "Duration of session"
)
session_termination_reason = Counter(
    "centinela_session_termination_total", "Terminated sessions", ["reason"]
)


class SessionLifecycle(ABC):
    """Abstract interface for session lifecycle management."""

    @abstractmethod
    def start_session(self, session_id: UUID) -> Session:
        pass

    @abstractmethod
    def complete_session(self, session_id: UUID) -> Session:
        pass


__all__ = [
    "PlatformConfig",
    "Session",
    "SessionLifecycle",
    "SessionManager",
    "session_count",
    "session_duration",
    "session_termination_reason",
]
