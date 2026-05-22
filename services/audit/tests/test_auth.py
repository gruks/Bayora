"""Tests for RBAC middleware."""

from __future__ import annotations

import os

from audit.auth import ROLE_PERMISSIONS, RBACMiddleware, Role


def test_rbac_dev_keys() -> None:
    middleware = RBACMiddleware()
    assert middleware.get_role("dev-admin-key") == Role.ADMIN
    assert middleware.get_role("dev-auditor-key") == Role.AUDITOR
    assert middleware.get_role("dev-orchestrator-key") == Role.ORCHESTRATOR
    assert middleware.get_role("invalid-key") is None


def test_rbac_env_keys() -> None:
    os.environ["AUDIT_API_KEYS"] = "admin:prod-admin-key,auditor:prod-audit-key"
    try:
        middleware = RBACMiddleware()
        assert middleware.get_role("prod-admin-key") == Role.ADMIN
        assert middleware.get_role("prod-audit-key") == Role.AUDITOR
        assert middleware.get_role("dev-admin-key") is None
    finally:
        del os.environ["AUDIT_API_KEYS"]


def test_rbac_invalid_role_in_env() -> None:
    os.environ["AUDIT_API_KEYS"] = "invalid_role:key1,admin:key2"
    try:
        middleware = RBACMiddleware()
        assert middleware.get_role("key1") is None
        assert middleware.get_role("key2") == Role.ADMIN
    finally:
        del os.environ["AUDIT_API_KEYS"]


def test_role_permissions() -> None:
    assert "read:all" in ROLE_PERMISSIONS[Role.ADMIN]
    assert "read:all" not in ROLE_PERMISSIONS[Role.AUDITOR]
    assert "read:correlation" in ROLE_PERMISSIONS[Role.AUDITOR]
    assert "read:health" in ROLE_PERMISSIONS[Role.ORCHESTRATOR]
