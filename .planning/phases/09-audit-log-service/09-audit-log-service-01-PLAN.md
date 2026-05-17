---
phase: 09-audit-log-service
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - packages/centinela-core/src/centinela/models.py
  - packages/centinela-core/pyproject.toml
  - services/audit/pyproject.toml
  - services/audit/src/audit/__init__.py
  - services/audit/src/audit/main.py
  - services/audit/src/audit/models.py
  - services/audit/src/audit/storage.py
  - services/audit/src/audit/chain.py
  - services/audit/src/audit/writer.py
  - services/audit/tests/test_storage.py
  - services/audit/tests/test_chain.py
  - services/audit/tests/test_writer.py
autonomous: true
user_setup: []

must_haves:
  truths:
    - "Audit entries can be appended with automatic SHA-256 hash chaining"
    - "Each entry includes hash of previous entry (prev_hash) forming an unbroken chain"
    - "Storage is append-only — no update or delete operations exposed"
    - "Writes are non-blocking — failures do not raise exceptions to callers"
    - "PostgreSQL and SQLite backends both work with identical interface"
  artifacts:
    - path: "packages/centinela-core/src/centinela/models.py"
      provides: "Extended AuditEntry model with actor, correlation_id, signature, entry_hash"
      contains: "class AuditEntry"
    - path: "services/audit/src/audit/models.py"
      provides: "AuditEntryCreate, AuditEntryQuery, AuditEvent types"
      exports: ["AuditEntryCreate", "AuditEntryQuery", "AuditEvent"]
    - path: "services/audit/src/audit/storage.py"
      provides: "AppendOnlyStorage ABC + PostgreSQLStorage + SQLiteStorage implementations"
      exports: ["AppendOnlyStorage", "PostgreSQLStorage", "SQLiteStorage"]
    - path: "services/audit/src/audit/chain.py"
      provides: "MerkleChain class — SHA-256 hash computation and verification"
      exports: ["MerkleChain", "compute_entry_hash", "GENESIS_HASH"]
    - path: "services/audit/src/audit/writer.py"
      provides: "AsyncAuditWriter — non-blocking write interface with error logging"
      exports: ["AsyncAuditWriter"]
  key_links:
    - from: "services/audit/src/audit/chain.py"
      to: "hashlib.sha256"
      via: "SHA-256 hash computation"
      pattern: "hashlib\\.sha256"
    - from: "services/audit/src/audit/storage.py"
      to: "services/audit/src/audit/chain.py"
      via: "import compute_entry_hash, GENESIS_HASH"
      pattern: "from .chain import"
    - from: "services/audit/src/audit/writer.py"
      to: "services/audit/src/audit/storage.py"
      via: "import AppendOnlyStorage"
      pattern: "from .storage import"
    - from: "services/audit/src/audit/writer.py"
      to: "asyncio"
      via: "asyncio.Queue for non-blocking writes"
      pattern: "asyncio\\.Queue"
---

<objective>
Implement the core audit log infrastructure: extended entry schema, SHA-256 Merkle hash chaining, append-only storage layer (PostgreSQL + SQLite), and non-blocking async writer.

Purpose: Establishes the foundational data model, cryptographic chain integrity, persistent storage, and fire-and-forget write interface that all subsequent audit features depend on.

Output: 12 files — 2 modified (models.py, pyproject.toml), 10 created.
</objective>

<execution_context>
@C:/Users/HP/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/HP/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md

Requirements from ROADMAP.md:
- AUDT-01: Write-only Merkle-chained log in isolated audit container
- AUDT-03: Every event includes timestamp and actor
- AUDT-04: Every event includes SHA-256 hash of event payload (never the payload itself for red prompts)
- AUDT-05: Every event includes hash of previous entry (prev_hash)
- AUDT-06: Full entry hash becomes next entry's prev_hash (chain integrity)

Existing code:
- `packages/centinela-core/src/centinela/models.py` has a stub AuditEntry with {timestamp, event_type, payload_hash, prev_hash}
- `services/audit/src/audit/main.py` is a placeholder ("Hello from centinela-audit!")
- `services/audit/pyproject.toml` only depends on centinela-core

User decisions from context (LOCKED):
- Audit entry schema: {timestamp, actor, event_type, payload_hash, prev_hash, correlation_id, signature}
- SHA-256 hash chaining where each entry includes hash of previous entry
- Append-only storage with PostgreSQL (or SQLite for dev)
- Every event includes SHA-256 hash of event payload (never the payload itself for red prompts)
- Audit is non-blocking — failures do not halt test execution
- Writing 1M entries takes <10s with PostgreSQL backend

Project conventions (from Phase 1-2):
- Python 3.12+ with `from __future__ import annotations`
- pydantic BaseModel with `frozen=True` for security-sensitive types
- `uv sync --all-packages --all-extras` for workspace dependencies
- pytest for testing, ruff for linting, mypy for type checking
</context>

<tasks>

<task type="auto">
  <name>Task 1: Extend AuditEntry model and create service-level types</name>
  <files>
    packages/centinela-core/src/centinela/models.py
    services/audit/src/audit/models.py
  </files>
  <action>
    **1. Extend `packages/centinela-core/src/centinela/models.py`:**

    Replace the existing stub AuditEntry with the full schema per user decision:

    ```python
    from datetime import datetime, timezone

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
        signature: str = ""   # Ed25519 signature (added in batch signing)
    ```

    Key changes from stub:
    - Added `actor: str` — identifies who/what triggered the event (per AUDT-03)
    - Added `correlation_id: str` — links all events in a test run
    - Added `entry_hash: str` — the SHA-256 hash of this complete entry
    - Added `signature: str` — Ed25519 signature (empty until batch-signed)
    - `prev_hash` is now required (not optional) — genesis entry uses GENESIS_HASH constant
    - `timestamp` uses explicit `datetime` type (no default — caller must provide)
    - `frozen=True` for immutability

    **2. Create `services/audit/src/audit/models.py`:**

    Service-level types for creating and querying audit entries:

    ```python
    from __future__ import annotations

    from datetime import datetime, timezone

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
    ```

    IMPORTANT:
    - `AuditEntryCreate.payload_hash` is the SHA-256 hash of the actual payload — the payload is NEVER stored
    - `AuditEntryQuery` supports filtering by correlation_id (for forensic reconstruction), event_type, and actor
    - All models use `frozen=True` for immutability
    - Use `from __future__ import annotations` for forward reference support
  </action>
  <verify>
    python -c "
    from centinela.models import AuditEntry
    from datetime import datetime, timezone
    entry = AuditEntry(
        timestamp=datetime.now(timezone.utc),
        actor='red-agent',
        event_type='prompt_sent',
        payload_hash='abc123',
        prev_hash='genesis',
        correlation_id='test-001'
    )
    assert entry.actor == 'red-agent'
    assert entry.correlation_id == 'test-001'
    print('AuditEntry model OK')
    "

    python -c "
    from audit.models import AuditEntryCreate, AuditEntryQuery, AuditEvent
    create = AuditEntryCreate(actor='blue-agent', event_type='classification', payload_hash='def456', correlation_id='test-002')
    assert create.actor == 'blue-agent'
    query = AuditEntryQuery(correlation_id='test-002', limit=50)
    assert query.limit == 50
    print('Service models OK')
    "
  </verify>
  <done>
    AuditEntry model in centinela-core has all 8 fields (timestamp, actor, event_type, payload_hash, prev_hash, correlation_id, entry_hash, signature). Service models (AuditEntryCreate, AuditEntryQuery, AuditEvent) are defined and importable. All models are frozen (immutable).
  </done>
</task>

<task type="auto">
  <name>Task 2: SHA-256 Merkle hash chain implementation</name>
  <files>
    services/audit/src/audit/chain.py
  </files>
  <action>
    Create `services/audit/src/audit/chain.py`:

    This module implements the cryptographic hash chain. Each entry's hash includes all fields, and that hash becomes the prev_hash of the next entry.

    ```python
    from __future__ import annotations

    import hashlib
    import json


    # The "genesis" hash — used as prev_hash for the very first entry.
    # This is a fixed constant so the chain always starts from the same point.
    GENESIS_HASH = "0" * 64  # SHA-256 produces 64 hex characters


    def compute_entry_hash(
        timestamp: str,
        actor: str,
        event_type: str,
        payload_hash: str,
        prev_hash: str,
        correlation_id: str,
    ) -> str:
        """Compute SHA-256 hash of an audit entry.

        The hash covers ALL fields (timestamp, actor, event_type, payload_hash,
        prev_hash, correlation_id) in a deterministic JSON serialization.
        This ensures any single-byte modification to any field breaks the chain.

        Args:
            timestamp: ISO 8601 timestamp string.
            actor: Event source identifier.
            event_type: Event category.
            payload_hash: SHA-256 hash of the actual payload (payload never stored).
            prev_hash: Hash of the previous entry (or GENESIS_HASH for first entry).
            correlation_id: Test run correlation identifier.

        Returns:
            64-character hex string (SHA-256 digest).
        """
        # Deterministic JSON serialization (sorted keys, no whitespace)
        data = json.dumps(
            {
                "timestamp": timestamp,
                "actor": actor,
                "event_type": event_type,
                "payload_hash": payload_hash,
                "prev_hash": prev_hash,
                "correlation_id": correlation_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(data).hexdigest()


    class MerkleChain:
        """Manages a Merkle-chained audit log.

        Tracks the current chain head (hash of the most recent entry) and
        computes new entry hashes that link to the chain.
        """

        def __init__(self, head: str = GENESIS_HASH) -> None:
            """Initialize with the current chain head.

            Args:
                head: Hash of the most recent entry. Defaults to GENESIS_HASH for a new chain.
            """
            self._head = head

        @property
        def head(self) -> str:
            """Hash of the most recent entry in the chain."""
            return self._head

        def append(
            self,
            timestamp: str,
            actor: str,
            event_type: str,
            payload_hash: str,
            correlation_id: str,
        ) -> str:
            """Compute the hash for a new entry and update the chain head.

            Args:
                timestamp: ISO 8601 timestamp.
                actor: Event source.
                event_type: Event category.
                payload_hash: SHA-256 hash of the payload.
                correlation_id: Test run identifier.

            Returns:
                The new entry's hash (which becomes the next entry's prev_hash).
            """
            entry_hash = compute_entry_hash(
                timestamp=timestamp,
                actor=actor,
                event_type=event_type,
                payload_hash=payload_hash,
                prev_hash=self._head,
                correlation_id=correlation_id,
            )
            self._head = entry_hash
            return entry_hash

        def verify_chain(self, entries: list[dict]) -> tuple[bool, int | None]:
            """Verify the integrity of a chain of entries.

            Recomputes every hash and confirms chain integrity.
            Detects any single-byte modification in any entry.

            Args:
                entries: List of entry dicts with keys matching AuditEntry fields.

            Returns:
                Tuple of (is_valid, first_invalid_index).
                If valid: (True, None)
                If invalid: (False, index_of_first_broken_link)
            """
            if not entries:
                return True, None

            current_hash = GENESIS_HASH

            for i, entry in enumerate(entries):
                computed = compute_entry_hash(
                    timestamp=entry["timestamp"],
                    actor=entry["actor"],
                    event_type=entry["event_type"],
                    payload_hash=entry["payload_hash"],
                    prev_hash=current_hash,
                    correlation_id=entry["correlation_id"],
                )

                if computed != entry["entry_hash"]:
                    return False, i

                current_hash = entry["entry_hash"]

            return True, None
    ```

    IMPORTANT:
    - `json.dumps` with `sort_keys=True` and `separators=(",", ":")` ensures deterministic serialization — same inputs always produce same hash
    - The hash covers ALL six fields — modifying any single byte in any field breaks the chain
    - `GENESIS_HASH` is 64 zeros (SHA-256 hex length) — a well-known starting point
    - `verify_chain` returns the index of the first broken link for forensic analysis
    - Do NOT use pickle or any non-deterministic serialization
    - The `prev_hash` parameter in `compute_entry_hash` is the hash of the PREVIOUS entry, creating the chain
  </action>
  <verify>
    python -c "
    from audit.chain import compute_entry_hash, MerkleChain, GENESIS_HASH

    # Test deterministic hashing
    h1 = compute_entry_hash('2024-01-01T00:00:00Z', 'red-agent', 'prompt_sent', 'abc123', GENESIS_HASH, 'corr-001')
    h2 = compute_entry_hash('2024-01-01T00:00:00Z', 'red-agent', 'prompt_sent', 'abc123', GENESIS_HASH, 'corr-001')
    assert h1 == h2, 'Hash should be deterministic'
    assert len(h1) == 64, 'SHA-256 hex should be 64 chars'

    # Test single-byte modification detection
    h3 = compute_entry_hash('2024-01-01T00:00:00Z', 'red-agent', 'prompt_sent', 'abc124', GENESIS_HASH, 'corr-001')
    assert h1 != h3, 'Different payload_hash should produce different hash'

    # Test chain append
    chain = MerkleChain()
    assert chain.head == GENESIS_HASH
    hash1 = chain.append('2024-01-01T00:00:00Z', 'red-agent', 'prompt_sent', 'abc123', 'corr-001')
    assert chain.head == hash1
    hash2 = chain.append('2024-01-01T00:00:01Z', 'blue-agent', 'classification', 'def456', 'corr-001')
    assert chain.head == hash2
    assert hash1 != hash2

    # Test chain verification
    entries = [
        {'timestamp': '2024-01-01T00:00:00Z', 'actor': 'red-agent', 'event_type': 'prompt_sent', 'payload_hash': 'abc123', 'correlation_id': 'corr-001', 'entry_hash': hash1},
        {'timestamp': '2024-01-01T00:00:01Z', 'actor': 'blue-agent', 'event_type': 'classification', 'payload_hash': 'def456', 'correlation_id': 'corr-001', 'entry_hash': hash2},
    ]
    valid, idx = MerkleChain().verify_chain(entries)
    assert valid is True
    assert idx is None

    # Test tamper detection
    tampered = entries.copy()
    tampered[1] = dict(tampered[1])
    tampered[1]['payload_hash'] = 'TAMPERED'
    valid, idx = MerkleChain().verify_chain(tampered)
    assert valid is False
    assert idx == 1

    print('MerkleChain all tests passed')
    "
  </verify>
  <done>
    compute_entry_hash produces deterministic SHA-256 hashes covering all 6 fields. MerkleChain tracks head hash, appends entries with correct prev_hash linkage, and verify_chain detects any single-byte modification with index of first broken link. GENESIS_HASH is 64 zeros.
  </done>
</task>

<task type="auto">
  <name>Task 3: Append-only storage layer and non-blocking async writer</name>
  <files>
    services/audit/pyproject.toml
    services/audit/src/audit/main.py
    services/audit/src/audit/storage.py
    services/audit/src/audit/writer.py
    services/audit/tests/test_storage.py
    services/audit/tests/test_chain.py
    services/audit/tests/test_writer.py
  </files>
  <action>
    **1. Update `services/audit/pyproject.toml`:**

    Add dependencies for PostgreSQL and async support:

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
    ]
    ```

    **2. Create `services/audit/src/audit/storage.py`:**

    Append-only storage with ABC + PostgreSQL + SQLite implementations:

    ```python
    from __future__ import annotations

    import abc
    import os
    from datetime import datetime, timezone

    from centinela.models import AuditEntry

    from .chain import GENESIS_HASH, compute_entry_hash


    class AppendOnlyStorage(abc.ABC):
        """Abstract base for append-only audit storage.

        All implementations guarantee:
        - Entries can only be appended (no UPDATE, no DELETE)
        - Each entry's prev_hash links to the previous entry's entry_hash
        - The chain head is always accessible
        """

        @abc.abstractmethod
        async def initialize(self) -> None:
            """Create tables if they don't exist. Idempotent."""
            ...

        @abc.abstractmethod
        async def append(self, entry: AuditEntry) -> None:
            """Append a single entry. Raises if entry already exists (by entry_hash)."""
            ...

        @abc.abstractmethod
        async def append_batch(self, entries: list[AuditEntry]) -> None:
            """Append multiple entries in a single transaction."""
            ...

        @abc.abstractmethod
        async def get_chain_head(self) -> str:
            """Return the hash of the most recent entry, or GENESIS_HASH if empty."""
            ...

        @abc.abstractmethod
        async def get_entries(
            self,
            correlation_id: str | None = None,
            event_type: str | None = None,
            actor: str | None = None,
            limit: int = 100,
            offset: int = 0,
        ) -> list[AuditEntry]:
            """Query entries with optional filters, ordered by timestamp ascending."""
            ...

        @abc.abstractmethod
        async def get_all_entries(self) -> list[AuditEntry]:
            """Return ALL entries in chronological order (for verification)."""
            ...

        @abc.abstractmethod
        async def close(self) -> None:
            """Release database connections."""
            ...


    class PostgreSQLStorage(AppendOnlyStorage):
        """Append-only storage using PostgreSQL.

        Uses asyncpg for high-performance async access.
        The audit_entries table has NO UPDATE or DELETE grants — append-only at DB level.
        """

        def __init__(self, dsn: str | None = None) -> None:
            self._dsn = dsn or os.environ.get("AUDIT_DATABASE_URL", "")
            self._pool: object = None  # asyncpg.Pool

        async def initialize(self) -> None:
            import asyncpg
            self._pool = await asyncpg.create_pool(dsn=self._dsn)
            async with self._pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS audit_entries (
                        id BIGSERIAL PRIMARY KEY,
                        timestamp TIMESTAMPTZ NOT NULL,
                        actor VARCHAR(255) NOT NULL,
                        event_type VARCHAR(100) NOT NULL,
                        payload_hash CHAR(64) NOT NULL,
                        prev_hash CHAR(64) NOT NULL,
                        correlation_id VARCHAR(255) NOT NULL,
                        entry_hash CHAR(64) NOT NULL UNIQUE,
                        signature TEXT DEFAULT ''
                    );
                    -- Append-only: revoke UPDATE and DELETE
                    REVOKE UPDATE, DELETE ON audit_entries FROM PUBLIC;
                    -- Index for correlation_id queries (forensic reconstruction)
                    CREATE INDEX IF NOT EXISTS idx_audit_correlation_id ON audit_entries(correlation_id);
                    CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_entries(timestamp);
                """)

        async def append(self, entry: AuditEntry) -> None:
            import asyncpg
            assert self._pool is not None
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO audit_entries
                       (timestamp, actor, event_type, payload_hash, prev_hash, correlation_id, entry_hash, signature)
                       VALUES (\$1, \$2, \$3, \$4, \$5, \$6, \$7, \$8)""",
                    entry.timestamp, entry.actor, entry.event_type,
                    entry.payload_hash, entry.prev_hash, entry.correlation_id,
                    entry.entry_hash, entry.signature,
                )

        async def append_batch(self, entries: list[AuditEntry]) -> None:
            import asyncpg
            assert self._pool is not None
            async with self._pool.acquire() as conn:
                async with conn.transaction():
                    for entry in entries:
                        await conn.execute(
                            """INSERT INTO audit_entries
                               (timestamp, actor, event_type, payload_hash, prev_hash, correlation_id, entry_hash, signature)
                               VALUES (\$1, \$2, \$3, \$4, \$5, \$6, \$7, \$8)""",
                            entry.timestamp, entry.actor, entry.event_type,
                            entry.payload_hash, entry.prev_hash, entry.correlation_id,
                            entry.entry_hash, entry.signature,
                        )

        async def get_chain_head(self) -> str:
            import asyncpg
            assert self._pool is not None
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT entry_hash FROM audit_entries ORDER BY id DESC LIMIT 1"
                )
                return row["entry_hash"] if row else GENESIS_HASH

        async def get_entries(
            self,
            correlation_id: str | None = None,
            event_type: str | None = None,
            actor: str | None = None,
            limit: int = 100,
            offset: int = 0,
        ) -> list[AuditEntry]:
            import asyncpg
            assert self._pool is not None
            query = "SELECT * FROM audit_entries WHERE 1=1"
            params: list = []
            param_idx = 1

            if correlation_id:
                query += f" AND correlation_id = \${param_idx}"
                params.append(correlation_id)
                param_idx += 1
            if event_type:
                query += f" AND event_type = \${param_idx}"
                params.append(event_type)
                param_idx += 1
            if actor:
                query += f" AND actor = \${param_idx}"
                params.append(actor)
                param_idx += 1

            query += f" ORDER BY timestamp ASC LIMIT \${param_idx} OFFSET \${param_idx + 1}"
            params.extend([limit, offset])

            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [
                    AuditEntry(
                        timestamp=r["timestamp"],
                        actor=r["actor"],
                        event_type=r["event_type"],
                        payload_hash=r["payload_hash"],
                        prev_hash=r["prev_hash"],
                        correlation_id=r["correlation_id"],
                        entry_hash=r["entry_hash"],
                        signature=r["signature"] or "",
                    )
                    for r in rows
                ]

        async def get_all_entries(self) -> list[AuditEntry]:
            import asyncpg
            assert self._pool is not None
            async with self._pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM audit_entries ORDER BY id ASC")
                return [
                    AuditEntry(
                        timestamp=r["timestamp"],
                        actor=r["actor"],
                        event_type=r["event_type"],
                        payload_hash=r["payload_hash"],
                        prev_hash=r["prev_hash"],
                        correlation_id=r["correlation_id"],
                        entry_hash=r["entry_hash"],
                        signature=r["signature"] or "",
                    )
                    for r in rows
                ]

        async def close(self) -> None:
            if self._pool:
                await self._pool.close()


    class SQLiteStorage(AppendOnlyStorage):
        """Append-only storage using SQLite (for development/testing).

        Uses aiosqlite for async access.
        """

        def __init__(self, path: str = ":memory:") -> None:
            self._path = path
            self._db: object = None  # aiosqlite.Connection

        async def initialize(self) -> None:
            import aiosqlite
            self._db = await aiosqlite.connect(self._path)
            await self._db.execute("""
                CREATE TABLE IF NOT EXISTS audit_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    correlation_id TEXT NOT NULL,
                    entry_hash TEXT NOT NULL UNIQUE,
                    signature TEXT DEFAULT ''
                )
            """)
            await self._db.execute(
                "CREATE INDEX IF NOT EXISTS idx_audit_correlation_id ON audit_entries(correlation_id)"
            )
            await self._db.execute(
                "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_entries(timestamp)"
            )
            await self._db.commit()

        async def append(self, entry: AuditEntry) -> None:
            import aiosqlite
            assert self._db is not None
            await self._db.execute(
                """INSERT INTO audit_entries
                   (timestamp, actor, event_type, payload_hash, prev_hash, correlation_id, entry_hash, signature)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (entry.timestamp.isoformat(), entry.actor, entry.event_type,
                 entry.payload_hash, entry.prev_hash, entry.correlation_id,
                 entry.entry_hash, entry.signature),
            )
            await self._db.commit()

        async def append_batch(self, entries: list[AuditEntry]) -> None:
            import aiosqlite
            assert self._db is not None
            await self._db.executemany(
                """INSERT INTO audit_entries
                   (timestamp, actor, event_type, payload_hash, prev_hash, correlation_id, entry_hash, signature)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (e.timestamp.isoformat(), e.actor, e.event_type,
                     e.payload_hash, e.prev_hash, e.correlation_id,
                     e.entry_hash, e.signature)
                    for e in entries
                ],
            )
            await self._db.commit()

        async def get_chain_head(self) -> str:
            import aiosqlite
            assert self._db is not None
            async with self._db.execute(
                "SELECT entry_hash FROM audit_entries ORDER BY id DESC LIMIT 1"
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else GENESIS_HASH

        async def get_entries(
            self,
            correlation_id: str | None = None,
            event_type: str | None = None,
            actor: str | None = None,
            limit: int = 100,
            offset: int = 0,
        ) -> list[AuditEntry]:
            import aiosqlite
            assert self._db is not None
            query = "SELECT * FROM audit_entries WHERE 1=1"
            params: list = []

            if correlation_id:
                query += " AND correlation_id = ?"
                params.append(correlation_id)
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            if actor:
                query += " AND actor = ?"
                params.append(actor)

            query += " ORDER BY timestamp ASC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            async with self._db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [
                    AuditEntry(
                        timestamp=datetime.fromisoformat(r[1]),
                        actor=r[2],
                        event_type=r[3],
                        payload_hash=r[4],
                        prev_hash=r[5],
                        correlation_id=r[6],
                        entry_hash=r[7],
                        signature=r[8] or "",
                    )
                    for r in rows
                ]

        async def get_all_entries(self) -> list[AuditEntry]:
            import aiosqlite
            assert self._db is not None
            async with self._db.execute("SELECT * FROM audit_entries ORDER BY id ASC") as cursor:
                rows = await cursor.fetchall()
                return [
                    AuditEntry(
                        timestamp=datetime.fromisoformat(r[1]),
                        actor=r[2],
                        event_type=r[3],
                        payload_hash=r[4],
                        prev_hash=r[5],
                        correlation_id=r[6],
                        entry_hash=r[7],
                        signature=r[8] or "",
                    )
                    for r in rows
                ]

        async def close(self) -> None:
            if self._db:
                await self._db.close()
    ```

    **3. Create `services/audit/src/audit/writer.py`:**

    Non-blocking async writer using asyncio.Queue:

    ```python
    from __future__ import annotations

    import asyncio
    import logging
    from datetime import datetime, timezone

    from centinela.models import AuditEntry

    from .chain import MerkleChain
    from .models import AuditEntryCreate
    from .storage import AppendOnlyStorage

    logger = logging.getLogger(__name__)


    class AsyncAuditWriter:
        """Non-blocking audit log writer.

        Entries are queued and written asynchronously. Failures are logged
        but do NOT raise exceptions to callers — audit is fire-and-forget.

        Usage:
            writer = AsyncAuditWriter(storage)
            await writer.start()
            # Later (from any code path):
            writer.write(AuditEntryCreate(...))  # Non-blocking
            # On shutdown:
            await writer.stop()
        """

        def __init__(
            self,
            storage: AppendOnlyStorage,
            queue_size: int = 10000,
            batch_size: int = 100,
            flush_interval: float = 1.0,
        ) -> None:
            self._storage = storage
            self._queue: asyncio.Queue[AuditEntryCreate] = asyncio.Queue(maxsize=queue_size)
            self._batch_size = batch_size
            self._flush_interval = flush_interval
            self._task: asyncio.Task | None = None
            self._chain = MerkleChain()
            self._running = False

        async def start(self) -> None:
            """Start the background writer task."""
            # Initialize chain head from storage
            head = await self._storage.get_chain_head()
            self._chain = MerkleChain(head=head)
            self._running = True
            self._task = asyncio.create_task(self._process_queue())

        def write(self, entry: AuditEntryCreate) -> None:
            """Queue an entry for asynchronous writing. Non-blocking.

            If the queue is full, the entry is dropped and logged.
            Failures during writing are logged but do NOT propagate.
            """
            try:
                self._queue.put_nowait(entry)
            except asyncio.QueueFull:
                logger.warning(
                    "Audit queue full — dropping entry (actor=%s, event=%s)",
                    entry.actor,
                    entry.event_type,
                )

        async def _process_queue(self) -> None:
            """Background task that drains the queue and writes entries in batches."""
            batch: list[AuditEntryCreate] = []

            while self._running:
                try:
                    # Wait for at least one entry or flush interval
                    entry = await asyncio.wait_for(
                        self._queue.get(), timeout=self._flush_interval
                    )
                    batch.append(entry)

                    # Drain remaining items up to batch_size
                    while len(batch) < self._batch_size:
                        try:
                            entry = self._queue.get_nowait()
                            batch.append(entry)
                        except asyncio.QueueEmpty:
                            break

                    if batch:
                        await self._write_batch(batch)
                        batch = []

                except asyncio.TimeoutError:
                    # Flush interval elapsed — write whatever we have
                    if batch:
                        await self._write_batch(batch)
                        batch = []
                except Exception:
                    logger.exception("Unexpected error in audit writer")

            # Final flush on shutdown
            if batch:
                await self._write_batch(batch)

        async def _write_batch(self, entries: list[AuditEntryCreate]) -> None:
            """Write a batch of entries with hash chaining."""
            try:
                audit_entries: list[AuditEntry] = []
                for entry in entries:
                    timestamp = datetime.now(timezone.utc).isoformat()
                    entry_hash = self._chain.append(
                        timestamp=timestamp,
                        actor=entry.actor,
                        event_type=entry.event_type,
                        payload_hash=entry.payload_hash,
                        correlation_id=entry.correlation_id,
                    )
                    audit_entries.append(
                        AuditEntry(
                            timestamp=datetime.fromisoformat(timestamp),
                            actor=entry.actor,
                            event_type=entry.event_type,
                            payload_hash=entry.payload_hash,
                            prev_hash=self._chain.head,  # Will be updated by next append
                            correlation_id=entry.correlation_id,
                            entry_hash=entry_hash,
                        )
                    )

                # Fix prev_hash: each entry's prev_hash should be the PREVIOUS entry's hash
                # The chain.append already updated head, so we need to reconstruct
                # Actually, let me fix this — the chain tracks head, so prev_hash for entry N
                # is the head BEFORE entry N was appended.
                # Let me redo this properly:

                # Rebuild with correct prev_hash
                audit_entries = []
                for entry in entries:
                    prev = self._chain.head  # Current head = prev for this entry
                    timestamp = datetime.now(timezone.utc).isoformat()
                    entry_hash = compute_entry_hash(
                        timestamp=timestamp,
                        actor=entry.actor,
                        event_type=entry.event_type,
                        payload_hash=entry.payload_hash,
                        prev_hash=prev,
                        correlation_id=entry.correlation_id,
                    )
                    self._chain._head = entry_hash  # Update chain head
                    audit_entries.append(
                        AuditEntry(
                            timestamp=datetime.fromisoformat(timestamp),
                            actor=entry.actor,
                            event_type=entry.event_type,
                            payload_hash=entry.payload_hash,
                            prev_hash=prev,
                            correlation_id=entry.correlation_id,
                            entry_hash=entry_hash,
                        )
                    )

                await self._storage.append_batch(audit_entries)

            except Exception:
                logger.exception("Failed to write audit batch — entries lost")

        async def stop(self) -> None:
            """Stop the writer and flush remaining entries."""
            self._running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
    ```

    Wait — the _write_batch method has a bug with the double-processing. Let me provide the corrected version:

    ```python
    async def _write_batch(self, entries: list[AuditEntryCreate]) -> None:
        """Write a batch of entries with hash chaining."""
        try:
            from .chain import compute_entry_hash

            audit_entries: list[AuditEntry] = []
            for entry in entries:
                prev = self._chain.head  # Current head = prev_hash for this entry
                timestamp = datetime.now(timezone.utc).isoformat()
                entry_hash = compute_entry_hash(
                    timestamp=timestamp,
                    actor=entry.actor,
                    event_type=entry.event_type,
                    payload_hash=entry.payload_hash,
                    prev_hash=prev,
                    correlation_id=entry.correlation_id,
                )
                self._chain._head = entry_hash  # Update chain head
                audit_entries.append(
                    AuditEntry(
                        timestamp=datetime.fromisoformat(timestamp),
                        actor=entry.actor,
                        event_type=entry.event_type,
                        payload_hash=entry.payload_hash,
                        prev_hash=prev,
                        correlation_id=entry.correlation_id,
                        entry_hash=entry_hash,
                    )
                )

            await self._storage.append_batch(audit_entries)

        except Exception:
            logger.exception("Failed to write audit batch — entries lost")
    ```

    **4. Update `services/audit/src/audit/main.py`:**

    Replace the placeholder with a proper entry point:

    ```python
    from __future__ import annotations

    import asyncio
    import logging
    import os

    from .storage import PostgreSQLStorage, SQLiteStorage
    from .writer import AsyncAuditWriter

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


    async def main() -> None:
        """Start the audit service."""
        db_url = os.environ.get("AUDIT_DATABASE_URL", "")

        if db_url:
            storage = PostgreSQLStorage(dsn=db_url)
            logger.info("Using PostgreSQL storage")
        else:
            storage = SQLiteStorage(path="audit.db")
            logger.info("Using SQLite storage (dev mode)")

        await storage.initialize()

        writer = AsyncAuditWriter(storage)
        await writer.start()

        logger.info("Audit service started")

        try:
            # Keep running until interrupted
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Shutting down audit service")
            await writer.stop()
            await storage.close()


    if __name__ == "__main__":
        asyncio.run(main())
    ```

    **5. Create test files:**

    `services/audit/tests/test_chain.py` — tests for MerkleChain and compute_entry_hash
    `services/audit/tests/test_storage.py` — tests for SQLiteStorage (in-memory)
    `services/audit/tests/test_writer.py` — tests for AsyncAuditWriter non-blocking behavior

    IMPORTANT guidelines:
    - Use `from __future__ import annotations` in all files
    - SQLiteStorage uses `:memory:` for tests — no file I/O
    - Writer tests verify non-blocking: write() returns immediately, entries appear in storage after await asyncio.sleep()
    - All pydantic models use `frozen=True`
    - The writer's _write_batch catches ALL exceptions and logs — never raises
  </action>
  <verify>
    # 1. Verify imports
    python -c "
    from audit.chain import compute_entry_hash, MerkleChain, GENESIS_HASH
    from audit.storage import AppendOnlyStorage, PostgreSQLStorage, SQLiteStorage
    from audit.writer import AsyncAuditWriter
    from audit.models import AuditEntryCreate, AuditEntryQuery, AuditEvent
    from centinela.models import AuditEntry
    print('All imports OK')
    "

    # 2. Verify SQLite storage + chain integration
    python -c "
    import asyncio
    from audit.storage import SQLiteStorage
    from audit.chain import MerkleChain, GENESIS_HASH, compute_entry_hash
    from centinela.models import AuditEntry
    from datetime import datetime, timezone

    async def test():
        storage = SQLiteStorage(':memory:')
        await storage.initialize()

        # Verify empty chain
        head = await storage.get_chain_head()
        assert head == GENESIS_HASH

        # Append entry
        ts = datetime.now(timezone.utc).isoformat()
        eh = compute_entry_hash(ts, 'red-agent', 'prompt_sent', 'abc123', GENESIS_HASH, 'corr-001')
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            actor='red-agent', event_type='prompt_sent',
            payload_hash='abc123', prev_hash=GENESIS_HASH,
            correlation_id='corr-001', entry_hash=eh
        )
        await storage.append(entry)

        # Verify chain head updated
        head = await storage.get_chain_head()
        assert head == eh

        # Verify query
        entries = await storage.get_entries(correlation_id='corr-001')
        assert len(entries) == 1
        assert entries[0].actor == 'red-agent'

        await storage.close()
        print('SQLite storage + chain integration OK')

    asyncio.run(test())
    "

    # 3. Verify non-blocking writer
    python -c "
    import asyncio
    from audit.storage import SQLiteStorage
    from audit.writer import AsyncAuditWriter
    from audit.models import AuditEntryCreate

    async def test():
        storage = SQLiteStorage(':memory:')
        await storage.initialize()
        writer = AsyncAuditWriter(storage, flush_interval=0.1)
        await writer.start()

        # Write entries (non-blocking)
        for i in range(5):
            writer.write(AuditEntryCreate(
                actor='test', event_type='test_event',
                payload_hash=f'hash_{i}', correlation_id='test-corr'
            ))

        # Wait for flush
        await asyncio.sleep(0.3)

        entries = await storage.get_all_entries()
        assert len(entries) == 5

        await writer.stop()
        await storage.close()
        print('Non-blocking writer OK')

    asyncio.run(test())
    "

    # 4. Run pytest
    uv run pytest services/audit/tests/ -v
  </verify>
  <done>
    AuditEntry model extended with all 8 fields. MerkleChain computes SHA-256 hashes with deterministic JSON serialization. PostgreSQLStorage and SQLiteStorage implement append-only interface with REVOKE UPDATE/DELETE for PostgreSQL. AsyncAuditWriter provides non-blocking fire-and-forget writes via asyncio.Queue. All tests pass.
  </done>
</task>

</tasks>

<verification>
Run these in sequence after `uv sync --all-packages --all-extras`:

```bash
# 1. Verify all imports
python -c "
from audit.chain import compute_entry_hash, MerkleChain, GENESIS_HASH
from audit.storage import AppendOnlyStorage, PostgreSQLStorage, SQLiteStorage
from audit.writer import AsyncAuditWriter
from audit.models import AuditEntryCreate, AuditEntryQuery, AuditEvent
from centinela.models import AuditEntry
print('All imports OK')
"

# 2. Verify chain integrity
python -c "
from audit.chain import MerkleChain, GENESIS_HASH
chain = MerkleChain()
h1 = chain.append('2024-01-01T00:00:00Z', 'red-agent', 'prompt_sent', 'abc', 'corr-001')
h2 = chain.append('2024-01-01T00:00:01Z', 'blue-agent', 'classification', 'def', 'corr-001')
assert chain.head == h2
print('Chain integrity OK')
"

# 3. Run all tests
uv run pytest services/audit/tests/ -v
```
</verification>

<success_criteria>
- AuditEntry model in centinela-core has all 8 fields (timestamp, actor, event_type, payload_hash, prev_hash, correlation_id, entry_hash, signature)
- compute_entry_hash produces deterministic SHA-256 hashes — same inputs always produce same hash
- MerkleChain correctly links entries — each entry's prev_hash is the previous entry's entry_hash
- SQLiteStorage and PostgreSQLStorage both implement AppendOnlyStorage ABC
- PostgreSQL table has REVOKE UPDATE, DELETE for append-only enforcement
- AsyncAuditWriter.write() returns immediately (non-blocking) — entries written asynchronously
- Writer failures are logged but do NOT raise exceptions
- All pytest tests pass with zero failures
</success_criteria>

<output>
After completion, create `.planning/phases/09-audit-log-service/09-audit-log-service-01-SUMMARY.md`
</output>
