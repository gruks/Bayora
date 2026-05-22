"""Append-only storage layer for audit entries."""

from __future__ import annotations

import abc
import os
from datetime import datetime, timezone

from centinela.models import AuditEntry

from .chain import GENESIS_HASH


class AppendOnlyStorage(abc.ABC):
    """Abstract base for append-only audit storage.

    Guarantees: entries can only be appended (no UPDATE, no DELETE).
    """

    @abc.abstractmethod
    async def initialize(self) -> None:
        """Create tables if they don't exist. Idempotent."""
        ...

    @abc.abstractmethod
    async def append(self, entry: AuditEntry) -> None:
        """Append a single entry."""
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
    """Append-only storage using PostgreSQL via asyncpg."""

    def __init__(self, dsn: str | None = None) -> None:
        self._dsn = dsn or os.environ.get("AUDIT_DATABASE_URL", "")
        self._pool: object = None

    async def initialize(self) -> None:
        import asyncpg  # type: ignore[import-untyped]

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
                REVOKE UPDATE, DELETE ON audit_entries FROM PUBLIC;
                CREATE INDEX IF NOT EXISTS idx_audit_correlation_id ON audit_entries(correlation_id);
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_entries(timestamp);
            """)

    async def append(self, entry: AuditEntry) -> None:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO audit_entries
                   (timestamp, actor, event_type, payload_hash, prev_hash,
                    correlation_id, entry_hash, signature)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                entry.timestamp,
                entry.actor,
                entry.event_type,
                entry.payload_hash,
                entry.prev_hash,
                entry.correlation_id,
                entry.entry_hash,
                entry.signature,
            )

    async def append_batch(self, entries: list[AuditEntry]) -> None:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                for entry in entries:
                    await conn.execute(
                        """INSERT INTO audit_entries
                           (timestamp, actor, event_type, payload_hash, prev_hash,
                            correlation_id, entry_hash, signature)
                           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                        entry.timestamp,
                        entry.actor,
                        entry.event_type,
                        entry.payload_hash,
                        entry.prev_hash,
                        entry.correlation_id,
                        entry.entry_hash,
                        entry.signature,
                    )

    async def get_chain_head(self) -> str:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT entry_hash FROM audit_entries ORDER BY id DESC LIMIT 1"
            )
            return str(row["entry_hash"]) if row else GENESIS_HASH

    async def get_entries(
        self,
        correlation_id: str | None = None,
        event_type: str | None = None,
        actor: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEntry]:
        assert self._pool is not None
        query = "SELECT * FROM audit_entries WHERE 1=1"
        params: list[object] = []
        idx = 1

        if correlation_id:
            query += f" AND correlation_id = ${idx}"
            params.append(correlation_id)
            idx += 1
        if event_type:
            query += f" AND event_type = ${idx}"
            params.append(event_type)
            idx += 1
        if actor:
            query += f" AND actor = ${idx}"
            params.append(actor)
            idx += 1

        query += f" ORDER BY timestamp ASC LIMIT ${idx} OFFSET ${idx + 1}"
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
            await self._pool.close()  # type: ignore[union-attr]


class SQLiteStorage(AppendOnlyStorage):
    """Append-only storage using SQLite (for development/testing) via aiosqlite."""

    def __init__(self, path: str = ":memory:") -> None:
        self._path = path
        self._db: object = None

    async def initialize(self) -> None:
        import aiosqlite  # type: ignore[import-untyped]

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
        assert self._db is not None
        await self._db.execute(
            """INSERT INTO audit_entries
               (timestamp, actor, event_type, payload_hash, prev_hash,
                correlation_id, entry_hash, signature)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.timestamp.isoformat(),
                entry.actor,
                entry.event_type,
                entry.payload_hash,
                entry.prev_hash,
                entry.correlation_id,
                entry.entry_hash,
                entry.signature,
            ),
        )
        await self._db.commit()

    async def append_batch(self, entries: list[AuditEntry]) -> None:
        assert self._db is not None
        await self._db.executemany(
            """INSERT INTO audit_entries
               (timestamp, actor, event_type, payload_hash, prev_hash,
                correlation_id, entry_hash, signature)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    e.timestamp.isoformat(),
                    e.actor,
                    e.event_type,
                    e.payload_hash,
                    e.prev_hash,
                    e.correlation_id,
                    e.entry_hash,
                    e.signature,
                )
                for e in entries
            ],
        )
        await self._db.commit()

    async def get_chain_head(self) -> str:
        assert self._db is not None
        async with self._db.execute(
            "SELECT entry_hash FROM audit_entries ORDER BY id DESC LIMIT 1"
        ) as cursor:
            row = await cursor.fetchone()
            return str(row[0]) if row else GENESIS_HASH

    async def get_entries(
        self,
        correlation_id: str | None = None,
        event_type: str | None = None,
        actor: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEntry]:
        assert self._db is not None
        query = "SELECT * FROM audit_entries WHERE 1=1"
        params: list[object] = []

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
            return [self._row_to_entry(row) for row in rows]

    async def get_all_entries(self) -> list[AuditEntry]:
        assert self._db is not None
        async with self._db.execute(
            "SELECT * FROM audit_entries ORDER BY id ASC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_entry(row) for row in rows]

    def _row_to_entry(self, row: tuple) -> AuditEntry:  # type: ignore[type-arg]
        # columns: id, timestamp, actor, event_type, payload_hash,
        #          prev_hash, correlation_id, entry_hash, signature
        ts_raw = row[1]
        if isinstance(ts_raw, str):
            ts = datetime.fromisoformat(ts_raw)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        else:
            ts = ts_raw
        return AuditEntry(
            timestamp=ts,
            actor=row[2],
            event_type=row[3],
            payload_hash=row[4],
            prev_hash=row[5],
            correlation_id=row[6],
            entry_hash=row[7],
            signature=row[8] or "",
        )

    async def close(self) -> None:
        if self._db:
            await self._db.close()  # type: ignore[union-attr]
