"""RBAC middleware for the audit query API."""

from __future__ import annotations

import os
from enum import Enum

from fastapi import HTTPException, Request, status


class Role(str, Enum):
    """RBAC roles for the audit API."""

    ADMIN = "admin"
    AUDITOR = "auditor"
    ORCHESTRATOR = "orchestrator"


ROLE_PERMISSIONS: dict[Role, list[str]] = {
    Role.ADMIN: ["read:all", "read:correlation", "read:health"],
    Role.AUDITOR: ["read:correlation", "read:health"],
    Role.ORCHESTRATOR: ["read:correlation", "read:health"],
}


class RBACMiddleware:
    """Validates API tokens and enforces role-based permissions.

    Tokens are passed via the X-API-Key header.
    Configuration via AUDIT_API_KEYS env var: "role:key,role:key"
    """

    def __init__(self) -> None:
        self._api_keys: dict[str, Role] = {}
        self._load_keys()

    def _load_keys(self) -> None:
        keys_str = os.environ.get("AUDIT_API_KEYS", "")
        if not keys_str:
            # Dev mode defaults
            self._api_keys = {
                "dev-admin-key": Role.ADMIN,
                "dev-auditor-key": Role.AUDITOR,
                "dev-orchestrator-key": Role.ORCHESTRATOR,
            }
            return

        for pair in keys_str.split(","):
            pair = pair.strip()
            if ":" in pair:
                role_str, key = pair.split(":", 1)
                try:
                    role = Role(role_str.strip())
                    self._api_keys[key.strip()] = role
                except ValueError:
                    pass  # skip invalid roles

    def get_role(self, api_key: str) -> Role | None:
        return self._api_keys.get(api_key)

    async def __call__(self, request: Request) -> None:
        """FastAPI dependency: validate API key and attach role to request state."""
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-API-Key header",
            )
        role = self.get_role(api_key)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key",
            )
        request.state.role = role


def require_role(*allowed_roles: Role):  # type: ignore[no-untyped-def]
    """FastAPI dependency factory: require one of the specified roles."""

    async def checker(request: Request) -> None:
        role = getattr(request.state, "role", None)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role.value}' is not authorized for this endpoint",
            )

    return checker
