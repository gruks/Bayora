"""Read-only FastAPI query API for audit entries."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status

from .auth import RBACMiddleware, Role
from .storage import AppendOnlyStorage

_rbac = RBACMiddleware()


def _require_role(*allowed_roles: Role):  # type: ignore[no-untyped-def]
    """Dependency: authenticate via X-API-Key and enforce role."""

    async def checker(request: Request) -> None:
        await _rbac(request)  # sets request.state.role or raises 401/403
        role = request.state.role
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role.value}' is not authorized for this endpoint",
            )

    return checker


def create_app(storage: AppendOnlyStorage) -> FastAPI:
    """Create the read-only audit query API."""
    app = FastAPI(
        title="CENTINELA Audit API",
        description="Read-only query API for tamper-evident audit log entries",
        version="0.1.0",
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/entries")
    async def get_entries(
        request: Request,
        correlation_id: str | None = Query(None),
        event_type: str | None = Query(None),
        actor: str | None = Query(None),
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        _role: None = Depends(
            _require_role(Role.ADMIN, Role.AUDITOR, Role.ORCHESTRATOR)
        ),
    ) -> dict[str, Any]:
        try:
            entries = await storage.get_entries(
                correlation_id=correlation_id,
                event_type=event_type,
                actor=actor,
                limit=limit,
                offset=offset,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Query failed: {exc}",
            ) from exc

        return {
            "entries": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "actor": e.actor,
                    "event_type": e.event_type,
                    "payload_hash": e.payload_hash,
                    "prev_hash": e.prev_hash,
                    "correlation_id": e.correlation_id,
                    "entry_hash": e.entry_hash,
                    "signature": e.signature,
                }
                for e in entries
            ],
            "total": len(entries),
            "limit": limit,
            "offset": offset,
        }

    @app.get("/entries/{correlation_id}")
    async def get_entries_by_correlation(
        request: Request,
        correlation_id: str,
        _role: None = Depends(
            _require_role(Role.ADMIN, Role.AUDITOR, Role.ORCHESTRATOR)
        ),
    ) -> dict[str, Any]:
        try:
            entries = await storage.get_entries(
                correlation_id=correlation_id,
                limit=100_000,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Query failed: {exc}",
            ) from exc

        if not entries:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No entries found for correlation_id: {correlation_id}",
            )

        return {
            "correlation_id": correlation_id,
            "entries": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "actor": e.actor,
                    "event_type": e.event_type,
                    "payload_hash": e.payload_hash,
                    "prev_hash": e.prev_hash,
                    "entry_hash": e.entry_hash,
                    "signature": e.signature,
                }
                for e in entries
            ],
            "total": len(entries),
        }

    @app.get("/chain/head")
    async def get_chain_head(
        request: Request,
        _role: None = Depends(_require_role(Role.ADMIN)),
    ) -> dict[str, str]:
        head = await storage.get_chain_head()
        return {"chain_head": head}

    return app
