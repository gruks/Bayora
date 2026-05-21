"""Session lifecycle management."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel

from centinela.enums import SessionState
from centinela.models.types import Session


class PlatformConfig(BaseModel):
    """Basic platform configuration."""

    tenant_id: str
    max_duration_seconds: int = 3600


class SessionManager:
    """Manages scoring session lifecycles."""

    def __init__(self) -> None:
        self._sessions: dict[UUID, Session] = {}

    def create_session(self, config: PlatformConfig, tenant_id: str) -> Session:
        """Generate session with UUID v4 in CREATED state."""
        session_id = uuid4()
        session = Session(
            id=session_id,
            state=SessionState.CREATED,
            metadata={"tenant_id": tenant_id, "config": config.model_dump()},
        )
        self._sessions[session_id] = session
        return session

    def start_session(self, session_id: UUID) -> Session:
        """Transitions CREATED->RUNNING."""
        if session_id not in self._sessions:
            raise ValueError("Session not found")

        session = self._sessions[session_id]
        if session.state != SessionState.CREATED:
            raise ValueError(f"Cannot start session from state {session.state}")

        updated_session = session.model_copy(
            update={"state": SessionState.RUNNING, "updated_at": datetime.now()}
        )
        self._sessions[session_id] = updated_session
        return updated_session

    def complete_session(self, session_id: UUID) -> Session:
        """Transitions RUNNING->COMPLETED."""
        if session_id not in self._sessions:
            raise ValueError("Session not found")

        session = self._sessions[session_id]
        if session.state != SessionState.RUNNING:
            raise ValueError(f"Cannot complete session from state {session.state}")

        updated_session = session.model_copy(
            update={"state": SessionState.COMPLETED, "updated_at": datetime.now()}
        )
        self._sessions[session_id] = updated_session
        return updated_session

    def terminate_session(self, session_id: UUID, reason: str) -> Session:
        """Transitions to TERMINATED and triggers cleanup."""
        if session_id not in self._sessions:
            raise ValueError("Session not found")

        session = self._sessions[session_id]

        metadata = dict(session.metadata)
        metadata["termination_reason"] = reason

        updated_session = session.model_copy(
            update={
                "state": SessionState.TERMINATED,
                "metadata": metadata,
                "updated_at": datetime.now(),
            }
        )
        self._sessions[session_id] = updated_session
        return updated_session

    def timeout_session(self, session_id: UUID) -> Session:
        """Auto-timeout after 3600s max."""
        if session_id not in self._sessions:
            raise ValueError("Session not found")

        session = self._sessions[session_id]
        if session.state not in (SessionState.CREATED, SessionState.RUNNING):
            return session

        # check max duration (ROADMAP specified 3600 max)
        config_dict = session.metadata.get("config", {})
        max_dur = config_dict.get("max_duration_seconds", 3600)

        elapsed = (datetime.now() - session.created_at).total_seconds()
        if elapsed > max_dur or elapsed > 3600:
            return self.terminate_session(session_id, "TIMEOUT")

        return session

    def get_session(self, session_id: UUID) -> Session | None:
        """Get session by ID."""
        return self._sessions.get(session_id)

    def list_sessions(
        self, tenant_id: str, state: SessionState | None = None
    ) -> list[Session]:
        """List sessions by tenant and optionally state."""
        sessions = [
            s for s in self._sessions.values() if s.metadata.get("tenant_id") == tenant_id
        ]
        if state:
            sessions = [s for s in sessions if s.state == state]
        return sessions
