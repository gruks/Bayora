---
phase: 09-audit-log-service
plan: 01
status: complete
completed: "2026-05-22"
---

# Summary: Plan 01 — Core Audit Log Infrastructure

## What was built

- Extended `AuditEntry` model in `centinela-core/models/base.py` — added `actor`, `correlation_id`, `entry_hash`, `signature` fields; `frozen=True`
- `services/audit/src/audit/models.py` — `AuditEntryCreate`, `AuditEntryQuery`, `AuditEvent` frozen pydantic models
- `services/audit/src/audit/chain.py` — `compute_entry_hash` (deterministic SHA-256 over 6 fields), `MerkleChain` (tracks head, appends, verifies), `GENESIS_HASH = "0" * 64`
- `services/audit/src/audit/storage.py` — `AppendOnlyStorage` ABC, `PostgreSQLStorage` (asyncpg), `SQLiteStorage` (aiosqlite) — no UPDATE/DELETE exposed
- `services/audit/src/audit/writer.py` — `AsyncAuditWriter` with `asyncio.Queue`, background task, fire-and-forget `write()`, chain linkage via `MerkleChain`
- Updated `services/audit/pyproject.toml` — added asyncpg, aiosqlite, fastapi, uvicorn, httpx

## Tests

17 tests passing: `test_chain.py` (8), `test_storage.py` (6), `test_writer.py` (3)

## Key decisions

- `compute_entry_hash` uses `json.dumps(sort_keys=True, separators=(",", ":"))` for deterministic serialization
- `AsyncAuditWriter.write()` uses `put_nowait` — drops entry and logs warning if queue full (never raises)
- SQLite stores timestamps as ISO 8601 strings; `_row_to_entry` parses them back with UTC tzinfo
