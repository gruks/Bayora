---
phase: 09-audit-log-service
plan: 03
type: execute
wave: 2
depends_on: ["01"]
files_modified:
  - services/audit/pyproject.toml
  - services/audit/src/audit/__init__.py
  - services/audit/src/audit/api.py
  - services/audit/src/audit/auth.py
  - services/audit/tests/test_api.py
  - services/audit/tests/test_auth.py
autonomous: true
user_setup: []

must_haves:
  truths:
    - "Query API exposes read-only access to audit entries"
    - "RBAC middleware enforces role-based access — only authorized roles can query"
    - "API returns entries filtered by correlation_id, event_type, or actor"
    - "API does NOT expose any write endpoints (read-only)"
  artifacts:
    - path: "services/audit/src/audit/api.py"
      provides: "FastAPI-based read-only query API with /entries, /entries/{correlation_id}, /health endpoints"
      exports: ["create_app"]
    - path: "services/audit/src/audit/auth.py"
      provides: "RBAC middleware — role-based access control for API endpoints"
      exports: ["RBACMiddleware", "Role", "require_role"]
    - path: "services/audit/tests/test_api.py"
      provides: "API endpoint tests — query, filter, RBAC enforcement"
    - path: "services/audit/tests/test_auth.py"
      provides: "RBAC unit tests — role checks, denied access"
  key_links:
    - from: "services/audit/src/audit/api.py"
      to: "services/audit/src/audit/storage.py"
      via: "import AppendOnlyStorage for read queries"
      pattern: "from .storage import"
    - from: "services/audit/src/audit/api.py"
      to: "services/audit/src/audit/auth.py"
      via: "import RBACMiddleware"
      pattern: "from .auth import"
    - from: "services/audit/src/audit/auth.py"
      to: "fastapi"
      via: "FastAPI middleware / dependency injection"
      pattern: "from fastapi import"
---

<objective>
Implement a read-only query API for audit entries with RBAC middleware, exposing filtered access by correlation_id, event_type, and actor.

Purpose: Provides the programmatic interface for other services (orchestrator, certificate generator) to query audit entries without direct database access. RBAC ensures only authorized roles can read audit data.

Output: 6 files — API module, auth module, 2 test files, pyproject.toml update, __init__.py update.
</objective>

<execution_context>
@C:/Users/HP/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/HP/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/09-audit-log-service/09-audit-log-service-01-PLAN.md
@.planning/phases/09-audit-log-service/09-audit-log-service-01-SUMMARY.md

User decisions from context (LOCKED):
- Add query API for read-only access with RBAC
- Red, blue, and LLM containers have zero network access to audit container

Dependencies from Plan 01:
- AppendOnlyStorage with get_entries and get_all_entries methods
- AuditEntry model with all 8 fields
- AuditEntryQuery for query parameters

Project conventions:
- Python 3.12+ with `from __future__ import annotations`
- FastAPI for API services (from roadmap Phase 19, but audit service can use it independently)
- pydantic BaseModel with frozen=True for response types
- pytest for testing
</context>

<tasks>

<task type="auto">
  <name>Task 1: RBAC middleware and role-based access control</name>
  <files>
    services/audit/pyproject.toml
    services/audit/src/audit/auth.py
    services/audit/tests/test_auth.py
  </files>
  <action>
    **1. Update `services/audit/pyproject.toml`:**

    Add FastAPI and uvicorn dependencies:

    ```toml
    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"

    [project]
    name = "audit"
    version = "0.1.0"
    description = "Audit service — tamper-evident cryptographic logging and certificate generation"
    requires-python = ">=3.12"
    dependencies = [
        "centinela-core",
        "asyncpg>=0.30.0",
        "aiosqlite>=0.20.0",
        "fastapi>=0.115.0",
        "uvicorn>=0.30.0",
    ]
    ```

    **2. Create `services/audit/src/audit/auth.py`:**

    ```python
    from __future__ import annotations

    import os
    from enum import Enum

    from fastapi import HTTPException, Request, status


    class Role(str, Enum):
        """RBAC roles for the audit API.

        - admin: Full read access to all entries
        - auditor: Read access for verification and compliance
        - orchestrator: Read access for certificate generation
        """
        ADMIN = "admin"
        AUDITOR = "auditor"
        ORCHESTRATOR = "orchestrator"


    # Role definitions — what each role can do
    ROLE_PERMISSIONS: dict[Role, list[str]] = {
        Role.ADMIN: ["read:all", "read:correlation", "read:health"],
        Role.AUDITOR: ["read:correlation", "read:health"],
        Role.ORCHESTRATOR: ["read:correlation", "read:health"],
    }


    class RBACMiddleware:
        """Role-based access control for the audit API.

        Validates API tokens and enforces role-based permissions.
        Tokens are passed via the X-API-Key header.

        Configuration via environment variables:
            AUDIT_API_KEYS: Comma-separated list of "role:api_key" pairs.
                Example: "admin:secret123,auditor:audit456,orchestrator:orch789"
        """

        def __init__(self) -> None:
            self._api_keys: dict[str, Role] = {}
            self._load_keys()

        def _load_keys(self) -> None:
            """Load API keys from environment variable."""
            keys_str = os.environ.get("AUDIT_API_KEYS", "")
            if not keys_str:
                # Dev mode: allow all with test keys
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
                        pass  # Skip invalid role

        def get_role(self, api_key: str) -> Role | None:
            """Return the role for the given API key, or None if invalid."""
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


    def require_role(*allowed_roles: Role):
        """FastAPI dependency factory: require one of the specified roles.

        Usage:
            @app.get("/entries", dependencies=[Depends(require_role(Role.ADMIN, Role.AUDITOR))])
            async def get_entries(request: Request):
                ...
        """
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
    ```

    IMPORTANT:
    - `Role` is a string enum — values are used in API responses and logs
    - `AUDIT_API_KEYS` env var format: `"role:api_key,role:api_key"`
    - Dev mode provides test keys when env var is not set (for development only)
    - `RBACMiddleware` is a FastAPI dependency — called on every request
    - `require_role` is a dependency factory — creates role-specific checkers
    - API keys are stored in memory — never logged or written to disk
    - The middleware does NOT use JWT or OAuth — simple API key authentication

    **3. Create `services/audit/tests/test_auth.py`:**

    ```python
    from __future__ import annotations

    import os

    import pytest

    from audit.auth import RBACMiddleware, Role, require_role


    def test_rbac_dev_keys():
        """Test default dev keys are loaded when no env var is set."""
        middleware = RBACMiddleware()
        assert middleware.get_role("dev-admin-key") == Role.ADMIN
        assert middleware.get_role("dev-auditor-key") == Role.AUDITOR
        assert middleware.get_role("dev-orchestrator-key") == Role.ORCHESTRATOR
        assert middleware.get_role("invalid-key") is None


    def test_rbac_env_keys():
        """Test API keys loaded from environment variable."""
        os.environ["AUDIT_API_KEYS"] = "admin:prod-admin-key,auditor:prod-audit-key"
        try:
            middleware = RBACMiddleware()
            assert middleware.get_role("prod-admin-key") == Role.ADMIN
            assert middleware.get_role("prod-audit-key") == Role.AUDITOR
            assert middleware.get_role("dev-admin-key") is None  # Dev keys not loaded
        finally:
            del os.environ["AUDIT_API_KEYS"]


    def test_rbac_invalid_role_in_env():
        """Test that invalid roles in env var are skipped."""
        os.environ["AUDIT_API_KEYS"] = "invalid_role:key1,admin:key2"
        try:
            middleware = RBACMiddleware()
            assert middleware.get_role("key1") is None  # Invalid role skipped
            assert middleware.get_role("key2") == Role.ADMIN
        finally:
            del os.environ["AUDIT_API_KEYS"]


    def test_role_permissions():
        """Test role permission definitions."""
        from audit.auth import ROLE_PERMISSIONS

        assert "read:all" in ROLE_PERMISSIONS[Role.ADMIN]
        assert "read:all" not in ROLE_PERMISSIONS[Role.AUDITOR]
        assert "read:correlation" in ROLE_PERMISSIONS[Role.AUDITOR]
        assert "read:health" in ROLE_PERMISSIONS[Role.ORCHESTRATOR]
    ```

    IMPORTANT:
    - Tests verify dev keys, env keys, and invalid role handling
    - Environment variable cleanup in finally blocks prevents test pollution
  </action>
  <verify>
    # 1. Verify auth imports
    python -c "
    from audit.auth import RBACMiddleware, Role, require_role, ROLE_PERMISSIONS
    print('Auth imports OK')
    "

    # 2. Run auth tests
    uv run pytest services/audit/tests/test_auth.py -v
  </verify>
  <done>
    RBACMiddleware validates API keys from AUDIT_API_KEYS env var (or dev keys). Role enum defines admin, auditor, orchestrator. require_role dependency factory enforces role-based access. ROLE_PERMISSIONS maps roles to permission strings. All auth tests pass.
  </done>
</task>

<task type="auto">
  <name>Task 2: Read-only query API with FastAPI</name>
  <files>
    services/audit/src/audit/api.py
    services/audit/src/audit/__init__.py
    services/audit/tests/test_api.py
  </files>
  <action>
    **1. Update `services/audit/src/audit/__init__.py`:**

    ```python
    """Audit service for CENTINELA."""
    from .api import create_app

    __all__ = ["create_app"]
    ```

    **2. Create `services/audit/src/audit/api.py`:**

    ```python
    from __future__ import annotations

    from datetime import datetime
    from typing import Any

    from fastapi import Depends, FastAPI, HTTPException, Query, Request, status

    from .auth import RBACMiddleware, Role, require_role
    from .models import AuditEntryQuery
    from .storage import AppendOnlyStorage


    def create_app(storage: AppendOnlyStorage) -> FastAPI:
        """Create the read-only audit query API.

        Args:
            storage: AppendOnlyStorage instance for reading audit entries.

        Returns:
            Configured FastAPI application with read-only endpoints.
        """
        app = FastAPI(
            title="CENTINELA Audit API",
            description="Read-only query API for tamper-evident audit log entries",
            version="0.1.0",
        )

        rbac = RBACMiddleware()

        # ── Health endpoint (no auth required) ──────────────────────────

        @app.get("/health")
        async def health() -> dict[str, str]:
            """Health check endpoint."""
            return {"status": "ok"}

        # ── Query endpoints (auth required) ─────────────────────────────

        @app.get("/entries")
        async def get_entries(
            request: Request,
            correlation_id: str | None = Query(None),
            event_type: str | None = Query(None),
            actor: str | None = Query(None),
            limit: int = Query(100, ge=1, le=1000),
            offset: int = Query(0, ge=0),
            _role: None = Depends(require_role(Role.ADMIN, Role.AUDITOR, Role.ORCHESTRATOR)),
        ) -> dict[str, Any]:
            """Query audit entries with optional filters.

            All roles can query entries. Results are returned in chronological order.
            """
            try:
                entries = await storage.get_entries(
                    correlation_id=correlation_id,
                    event_type=event_type,
                    actor=actor,
                    limit=limit,
                    offset=offset,
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Query failed: {str(e)}",
                )

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
            _role: None = Depends(require_role(Role.ADMIN, Role.AUDITOR, Role.ORCHESTRATOR)),
        ) -> dict[str, Any]:
            """Get all entries for a specific correlation ID.

            Used for forensic reconstruction of a test run.
            Returns all matching entries in chronological order (no pagination).
            """
            try:
                entries = await storage.get_entries(
                    correlation_id=correlation_id,
                    limit=100000,  # Large limit for forensic queries
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Query failed: {str(e)}",
                )

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
            _role: None = Depends(require_role(Role.ADMIN)),
        ) -> dict[str, str]:
            """Get the current chain head hash.

            Only admin role can access this endpoint.
            """
            head = await storage.get_chain_head()
            return {"chain_head": head}

        return app
    ```

    IMPORTANT:
    - API is READ-ONLY — no POST, PUT, PATCH, or DELETE endpoints
    - `/health` requires no authentication (for load balancer health checks)
    - `/entries` supports filtering by correlation_id, event_type, actor with pagination
    - `/entries/{correlation_id}` returns ALL entries for a correlation ID (forensic reconstruction)
    - `/chain/head` is admin-only — returns the current chain head hash
    - All query endpoints require authentication via `X-API-Key` header
    - Response format is consistent JSON with entry fields
    - The API does NOT expose payload data — only payload_hash
    - Error responses use standard HTTP status codes (401, 403, 404, 500)

    **3. Create `services/audit/tests/test_api.py`:**

    ```python
    from __future__ import annotations

    import asyncio
    from datetime import datetime, timezone

    import pytest
    from fastapi.testclient import TestClient

    from audit.api import create_app
    from audit.chain import GENESIS_HASH, compute_entry_hash
    from audit.storage import SQLiteStorage
    from centinela.models import AuditEntry


    @pytest.fixture
    async def storage():
        s = SQLiteStorage(":memory:")
        await s.initialize()
        yield s
        await s.close()


    @pytest.fixture
    async def populated_storage(storage):
        """Storage with 5 chained entries."""
        entries = []
        prev_hash = GENESIS_HASH
        for i in range(5):
            ts = datetime(2024, 1, 1, 0, 0, i, tzinfo=timezone.utc).isoformat()
            eh = compute_entry_hash(
                ts, f"actor-{i}", f"event-{i}", f"hash-{i}", prev_hash, f"corr-{i % 2}"
            )
            entry = AuditEntry(
                timestamp=datetime(2024, 1, 1, 0, 0, i, tzinfo=timezone.utc),
                actor=f"actor-{i}",
                event_type=f"event-{i}",
                payload_hash=f"hash-{i}",
                prev_hash=prev_hash,
                correlation_id=f"corr-{i % 2}",
                entry_hash=eh,
            )
            entries.append(entry)
            prev_hash = eh

        await storage.append_batch(entries)
        return storage


    @pytest.fixture
    def client(storage):
        app = create_app(storage)
        return TestClient(app)


    @pytest.fixture
    def populated_client(populated_storage):
        app = create_app(populated_storage)
        return TestClient(app)


    def test_health_no_auth(client):
        """Health endpoint requires no authentication."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


    def test_entries_requires_auth(client):
        """Query endpoints require X-API-Key header."""
        response = client.get("/entries")
        assert response.status_code == 401


    def test_entries_invalid_key(client):
        """Invalid API key returns 403."""
        response = client.get("/entries", headers={"X-API-Key": "invalid"})
        assert response.status_code == 403


    def test_entries_with_auth(populated_client):
        """Authenticated request returns entries."""
        response = populated_client.get(
            "/entries",
            headers={"X-API-Key": "dev-admin-key"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["entries"]) == 5


    def test_entries_filter_by_correlation_id(populated_client):
        """Filter by correlation_id returns matching entries."""
        response = populated_client.get(
            "/entries?correlation_id=corr-0",
            headers={"X-API-Key": "dev-admin-key"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3  # entries 0, 2, 4 have corr-0
        for entry in data["entries"]:
            assert entry["correlation_id"] == "corr-0"


    def test_entries_pagination(populated_client):
        """Pagination works correctly."""
        response = populated_client.get(
            "/entries?limit=2&offset=1",
            headers={"X-API-Key": "dev-admin-key"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["limit"] == 2
        assert data["offset"] == 1


    def test_entries_by_correlation_id(populated_client):
        """Get all entries for a correlation ID."""
        response = populated_client.get(
            "/entries/corr-0",
            headers={"X-API-Key": "dev-auditor-key"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["correlation_id"] == "corr-0"
        assert data["total"] == 3


    def test_entries_by_correlation_id_not_found(populated_client):
        """Non-existent correlation ID returns 404."""
        response = populated_client.get(
            "/entries/nonexistent",
            headers={"X-API-Key": "dev-auditor-key"},
        )
        assert response.status_code == 404


    def test_chain_head_admin_only(populated_client):
        """Chain head endpoint requires admin role."""
        # Admin can access
        response = populated_client.get(
            "/chain/head",
            headers={"X-API-Key": "dev-admin-key"},
        )
        assert response.status_code == 200
        assert "chain_head" in response.json()

        # Auditor cannot access
        response = populated_client.get(
            "/chain/head",
            headers={"X-API-Key": "dev-auditor-key"},
        )
        assert response.status_code == 403
    ```

    IMPORTANT:
    - Tests use FastAPI's TestClient for synchronous testing of async endpoints
    - Health endpoint requires no auth — all other endpoints require X-API-Key
    - Tests verify RBAC: admin can access all, auditor limited to correlation queries
    - Tests verify filtering, pagination, and 404 for non-existent correlation IDs
    - All tests use in-memory SQLite — no external dependencies
  </action>
  <verify>
    # 1. Verify API imports
    python -c "
    from audit.api import create_app
    from audit.auth import RBACMiddleware, Role, require_role
    print('API imports OK')
    "

    # 2. Run API tests
    uv run pytest services/audit/tests/test_api.py -v

    # 3. Run all audit tests
    uv run pytest services/audit/tests/ -v
  </verify>
  <done>
    FastAPI read-only query API with /health, /entries, /entries/{correlation_id}, /chain/head endpoints. RBACMiddleware enforces X-API-Key authentication. Role enum defines admin, auditor, orchestrator with appropriate permissions. All API tests pass. No write endpoints exposed.
  </done>
</task>

</tasks>

<verification>
Run these in sequence after `uv sync --all-packages --all-extras`:

```bash
# 1. Verify all imports
python -c "
from audit.api import create_app
from audit.auth import RBACMiddleware, Role, require_role
from audit.storage import AppendOnlyStorage, PostgreSQLStorage, SQLiteStorage
from audit.writer import AsyncAuditWriter
from audit.verify import AuditVerifier, VerificationResult
from audit.chain import compute_entry_hash, MerkleChain, GENESIS_HASH
from audit.models import AuditEntryCreate, AuditEntryQuery, AuditEvent
from centinela.models import AuditEntry
print('All imports OK')
"

# 2. Run all audit tests
uv run pytest services/audit/tests/ -v

# 3. Verify CLI
python services/audit/verify_audit.py --help
```
</verification>

<success_criteria>
- FastAPI app created with read-only endpoints: /health, /entries, /entries/{correlation_id}, /chain/head
- RBACMiddleware enforces X-API-Key authentication on all query endpoints
- Role enum defines admin, auditor, orchestrator with appropriate permissions
- /health requires no authentication (for load balancer health checks)
- /chain/head is admin-only
- All entries returned in chronological order (ORDER BY timestamp ASC)
- No write endpoints (POST, PUT, PATCH, DELETE) exist in the API
- All pytest tests pass with zero failures
</success_criteria>

<output>
After completion, create `.planning/phases/09-audit-log-service/09-audit-log-service-03-SUMMARY.md`
</output>
