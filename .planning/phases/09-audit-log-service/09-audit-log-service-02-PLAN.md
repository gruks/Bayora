---
phase: 09-audit-log-service
plan: 02
type: execute
wave: 2
depends_on: ["01"]
files_modified:
  - services/audit/src/audit/verify.py
  - services/audit/verify_audit.py
  - services/audit/tests/test_verify.py
autonomous: true
user_setup: []

must_haves:
  truths:
    - "Running verify_audit.py recomputes every hash and confirms chain integrity"
    - "Verification detects any single-byte modification in any entry"
    - "Verification of 10K entries completes in <1s"
    - "Correlation ID query returns all related events in chronological order"
  artifacts:
    - path: "services/audit/src/audit/verify.py"
      provides: "AuditVerifier class — chain verification, tamper detection, performance metrics"
      exports: ["AuditVerifier", "VerificationResult"]
    - path: "services/audit/verify_audit.py"
      provides: "CLI script entry point — argparse-based CLI for verification"
      exports: ["main"]
    - path: "services/audit/tests/test_verify.py"
      provides: "Verification tests — chain integrity, tamper detection, performance"
  key_links:
    - from: "services/audit/verify_audit.py"
      to: "services/audit/src/audit/verify.py"
      via: "import AuditVerifier"
      pattern: "from audit.verify import"
    - from: "services/audit/src/audit/verify.py"
      to: "services/audit/src/audit/chain.py"
      via: "import compute_entry_hash, GENESIS_HASH, MerkleChain"
      pattern: "from .chain import"
    - from: "services/audit/src/audit/verify.py"
      to: "services/audit/src/audit/storage.py"
      via: "import AppendOnlyStorage"
      pattern: "from .storage import"
---

<objective>
Implement the verify_audit.py CLI script and AuditVerifier class that recomputes every hash and confirms chain integrity, with correlation ID query support.

Purpose: Provides the forensic verification tool that proves the audit chain has not been tampered with. This is the primary deliverable for compliance auditors who need to verify audit integrity.

Output: 3 files — verifier module, CLI script, test file.
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

Requirements from ROADMAP.md:
- AUDT-07: verify_audit.py script recomputes every hash and confirms chain integrity

User decisions from context (LOCKED):
- verify_audit.py CLI script that recomputes every hash and confirms chain integrity
- Correlation ID links all events in a test run for forensic reconstruction
- Verification of 10K entries completes in <1s
- Correlation ID query returns all related events in chronological order
- Verification script detects any single-byte modification in any entry

Dependencies from Plan 01:
- MerkleChain class with verify_chain method
- compute_entry_hash function
- AppendOnlyStorage with get_all_entries and get_entries methods
- AuditEntry model with all 8 fields

Project conventions:
- Python 3.12+ with `from __future__ import annotations`
- argparse for CLI scripts
- pydantic BaseModel with frozen=True for result types
</context>

<tasks>

<task type="auto">
  <name>Task 1: AuditVerifier class with chain verification and correlation queries</name>
  <files>
    services/audit/src/audit/verify.py
    services/audit/tests/test_verify.py
  </files>
  <action>
    **1. Create `services/audit/src/audit/verify.py`:**

    ```python
    from __future__ import annotations

    import time
    from dataclasses import dataclass

    from centinela.models import AuditEntry

    from .chain import GENESIS_HASH, MerkleChain
    from .storage import AppendOnlyStorage


    @dataclass(frozen=True)
    class VerificationResult:
        """Result of an audit chain verification."""
        is_valid: bool
        total_entries: int
        verified_entries: int
        first_invalid_index: int | None
        duration_ms: float
        chain_head: str
        error_message: str | None = None


    class AuditVerifier:
        """Verifies the integrity of an audit chain.

        Recomputes every hash from scratch and confirms the chain is unbroken.
        Any single-byte modification in any entry will be detected.
        """

        def __init__(self, storage: AppendOnlyStorage) -> None:
            self._storage = storage

        async def verify(self) -> VerificationResult:
            """Verify the entire audit chain.

            Returns:
                VerificationResult with validity status, entry counts, and timing.
            """
            start = time.perf_counter()

            entries = await self._storage.get_all_entries()
            total = len(entries)

            if total == 0:
                elapsed = (time.perf_counter() - start) * 1000
                return VerificationResult(
                    is_valid=True,
                    total_entries=0,
                    verified_entries=0,
                    first_invalid_index=None,
                    duration_ms=round(elapsed, 2),
                    chain_head=GENESIS_HASH,
                )

            # Convert to dicts for MerkleChain.verify_chain
            entry_dicts = [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "actor": e.actor,
                    "event_type": e.event_type,
                    "payload_hash": e.payload_hash,
                    "prev_hash": e.prev_hash,
                    "correlation_id": e.correlation_id,
                    "entry_hash": e.entry_hash,
                }
                for e in entries
            ]

            chain = MerkleChain()
            is_valid, first_invalid = chain.verify_chain(entry_dicts)

            elapsed = (time.perf_counter() - start) * 1000
            verified = total if is_valid else (first_invalid or 0)

            return VerificationResult(
                is_valid=is_valid,
                total_entries=total,
                verified_entries=verified,
                first_invalid_index=first_invalid,
                duration_ms=round(elapsed, 2),
                chain_head=entries[-1].entry_hash if entries else GENESIS_HASH,
                error_message=None if is_valid else f"Chain broken at entry {first_invalid}",
            )

        async def verify_by_correlation_id(self, correlation_id: str) -> VerificationResult:
            """Verify only entries matching a specific correlation ID.

            Useful for forensic reconstruction of a single test run.

            Args:
                correlation_id: The correlation ID to verify.

            Returns:
                VerificationResult for the subset of entries.
            """
            start = time.perf_counter()

            entries = await self._storage.get_entries(correlation_id=correlation_id)
            total = len(entries)

            if total == 0:
                elapsed = (time.perf_counter() - start) * 1000
                return VerificationResult(
                    is_valid=False,
                    total_entries=0,
                    verified_entries=0,
                    first_invalid_index=None,
                    duration_ms=round(elapsed, 2),
                    chain_head=GENESIS_HASH,
                    error_message=f"No entries found for correlation_id: {correlation_id}",
                )

            entry_dicts = [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "actor": e.actor,
                    "event_type": e.event_type,
                    "payload_hash": e.payload_hash,
                    "prev_hash": e.prev_hash,
                    "correlation_id": e.correlation_id,
                    "entry_hash": e.entry_hash,
                }
                for e in entries
            ]

            chain = MerkleChain()
            is_valid, first_invalid = chain.verify_chain(entry_dicts)

            elapsed = (time.perf_counter() - start) * 1000
            verified = total if is_valid else (first_invalid or 0)

            return VerificationResult(
                is_valid=is_valid,
                total_entries=total,
                verified_entries=verified,
                first_invalid_index=first_invalid,
                duration_ms=round(elapsed, 2),
                chain_head=entries[-1].entry_hash if entries else GENESIS_HASH,
                error_message=None if is_valid else f"Chain broken at entry {first_invalid}",
            )

        async def get_correlation_events(self, correlation_id: str) -> list[AuditEntry]:
            """Get all events for a correlation ID in chronological order.

            Used for forensic reconstruction of a test run.

            Args:
                correlation_id: The correlation ID to query.

            Returns:
                List of AuditEntry objects ordered by timestamp ascending.
            """
            return await self._storage.get_entries(
                correlation_id=correlation_id,
                limit=100000,  # Large limit for forensic queries
            )
    ```

    IMPORTANT:
    - `VerificationResult` is a frozen dataclass — immutable result object
    - `verify()` fetches ALL entries and recomputes every hash from scratch
    - `verify_by_correlation_id()` verifies only a subset — useful for targeted forensic analysis
    - `get_correlation_events()` returns entries in chronological order (ORDER BY timestamp ASC)
    - Timing uses `time.perf_counter()` for high-resolution measurement
    - The verifier does NOT modify any data — read-only operations only

    **2. Create `services/audit/tests/test_verify.py`:**

    ```python
    from __future__ import annotations

    import asyncio
    from datetime import datetime, timezone

    import pytest

    from audit.chain import GENESIS_HASH, compute_entry_hash
    from audit.storage import SQLiteStorage
    from audit.verify import AuditVerifier, VerificationResult
    from centinela.models import AuditEntry


    @pytest.fixture
    async def storage():
        s = SQLiteStorage(":memory:")
        await s.initialize()
        yield s
        await s.close()


    @pytest.fixture
    async def populated_storage(storage):
        """Storage with 10 chained entries."""
        entries = []
        prev_hash = GENESIS_HASH
        for i in range(10):
            ts = datetime(2024, 1, 1, 0, 0, i, tzinfo=timezone.utc).isoformat()
            eh = compute_entry_hash(
                ts, f"actor-{i}", f"event-{i}", f"hash-{i}", prev_hash, "corr-001"
            )
            entry = AuditEntry(
                timestamp=datetime(2024, 1, 1, 0, 0, i, tzinfo=timezone.utc),
                actor=f"actor-{i}",
                event_type=f"event-{i}",
                payload_hash=f"hash-{i}",
                prev_hash=prev_hash,
                correlation_id="corr-001",
                entry_hash=eh,
            )
            entries.append(entry)
            prev_hash = eh

        await storage.append_batch(entries)
        return storage


    @pytest.mark.asyncio
    async def test_verify_empty_chain(storage):
        verifier = AuditVerifier(storage)
        result = await verifier.verify()
        assert result.is_valid is True
        assert result.total_entries == 0
        assert result.chain_head == GENESIS_HASH


    @pytest.mark.asyncio
    async def test_verify_valid_chain(populated_storage):
        verifier = AuditVerifier(populated_storage)
        result = await verifier.verify()
        assert result.is_valid is True
        assert result.total_entries == 10
        assert result.verified_entries == 10
        assert result.first_invalid_index is None


    @pytest.mark.asyncio
    async def test_verify_tampered_chain(populated_storage):
        # Tamper with entry 5
        from audit.storage import SQLiteStorage
        import aiosqlite

        async with populated_storage._db.execute(
            "UPDATE audit_entries SET payload_hash = 'TAMPERED' WHERE id = 6"
        ) as cursor:
            await populated_storage._db.commit()

        verifier = AuditVerifier(populated_storage)
        result = await verifier.verify()
        assert result.is_valid is False
        assert result.first_invalid_index is not None


    @pytest.mark.asyncio
    async def test_verify_by_correlation_id(populated_storage):
        verifier = AuditVerifier(populated_storage)
        result = await verifier.verify_by_correlation_id("corr-001")
        assert result.is_valid is True
        assert result.total_entries == 10


    @pytest.mark.asyncio
    async def test_verify_nonexistent_correlation_id(populated_storage):
        verifier = AuditVerifier(populated_storage)
        result = await verifier.verify_by_correlation_id("nonexistent")
        assert result.is_valid is False
        assert result.error_message is not None


    @pytest.mark.asyncio
    async def test_get_correlation_events(populated_storage):
        verifier = AuditVerifier(populated_storage)
        events = await verifier.get_correlation_events("corr-001")
        assert len(events) == 10
        # Verify chronological order
        for i in range(len(events) - 1):
            assert events[i].timestamp <= events[i + 1].timestamp


    @pytest.mark.asyncio
    async def test_verification_performance(storage):
        """Verify 10K entries completes in <1s."""
        # Create 10K entries
        entries = []
        prev_hash = GENESIS_HASH
        for i in range(10000):
            ts = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat()
            eh = compute_entry_hash(
                ts, "perf-test", "perf-event", f"hash-{i}", prev_hash, "perf-corr"
            )
            entry = AuditEntry(
                timestamp=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                actor="perf-test",
                event_type="perf-event",
                payload_hash=f"hash-{i}",
                prev_hash=prev_hash,
                correlation_id="perf-corr",
                entry_hash=eh,
            )
            entries.append(entry)
            prev_hash = eh

        # Batch insert in chunks of 1000
        for i in range(0, len(entries), 1000):
            await storage.append_batch(entries[i : i + 1000])

        verifier = AuditVerifier(storage)
        result = await verifier.verify()

        assert result.is_valid is True
        assert result.total_entries == 10000
        assert result.duration_ms < 1000, f"Verification took {result.duration_ms}ms (limit: 1000ms)"
    ```

    IMPORTANT:
    - Tests use `@pytest.mark.asyncio` for async test support
    - Performance test creates 10K entries and verifies completion in <1s
    - Tamper test modifies a single field and verifies detection
    - All tests use in-memory SQLite — no external dependencies
  </action>
  <verify>
    # 1. Verify verifier module imports
    python -c "
    from audit.verify import AuditVerifier, VerificationResult
    print('Verifier imports OK')
    "

    # 2. Run verification tests
    uv run pytest services/audit/tests/test_verify.py -v

    # 3. Verify performance (10K entries < 1s)
    uv run pytest services/audit/tests/test_verify.py::test_verification_performance -v -s
  </verify>
  <done>
    AuditVerifier class verifies entire chain by recomputing every hash. verify_by_correlation_id verifies subset. get_correlation_events returns entries in chronological order. VerificationResult is immutable frozen dataclass. All tests pass including performance test (10K entries < 1s).
  </done>
</task>

<task type="auto">
  <name>Task 2: verify_audit.py CLI script</name>
  <files>
    services/audit/verify_audit.py
  </files>
  <action>
    Create `services/audit/verify_audit.py` — the CLI entry point:

    ```python
    #!/usr/bin/env python3
    """verify_audit.py — Audit chain verification CLI.

    Recomputes every hash and confirms chain integrity.
    Detects any single-byte modification in any entry.

    Usage:
        # Verify entire chain
        python verify_audit.py --database-url "postgresql://..."

        # Verify by correlation ID
        python verify_audit.py --database-url "postgresql://..." --correlation-id "test-001"

        # Use SQLite (dev)
        python verify_audit.py --sqlite-path audit.db

        # Get events for forensic reconstruction
        python verify_audit.py --database-url "postgresql://..." --events "test-001"
    """
    from __future__ import annotations

    import argparse
    import asyncio
    import json
    import sys

    from audit.storage import PostgreSQLStorage, SQLiteStorage
    from audit.verify import AuditVerifier


    def parse_args() -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description="Verify audit chain integrity",
        )
        parser.add_argument(
            "--database-url",
            help="PostgreSQL connection URL (e.g. postgresql://user:pass@host/db)",
        )
        parser.add_argument(
            "--sqlite-path",
            default="audit.db",
            help="SQLite database path (default: audit.db)",
        )
        parser.add_argument(
            "--correlation-id",
            help="Verify only entries matching this correlation ID",
        )
        parser.add_argument(
            "--events",
            metavar="CORRELATION_ID",
            help="Print all events for a correlation ID (forensic reconstruction)",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output results as JSON",
        )
        return parser.parse_args()


    async def main() -> int:
        args = parse_args()

        # Initialize storage
        if args.database_url:
            storage = PostgreSQLStorage(dsn=args.database_url)
        else:
            storage = SQLiteStorage(path=args.sqlite_path)

        await storage.initialize()

        try:
            verifier = AuditVerifier(storage)

            if args.events:
                # Forensic reconstruction mode
                events = await verifier.get_correlation_events(args.events)
                if not events:
                    print(f"No events found for correlation_id: {args.events}")
                    return 1

                if args.json:
                    print(json.dumps(
                        [
                            {
                                "timestamp": e.timestamp.isoformat(),
                                "actor": e.actor,
                                "event_type": e.event_type,
                                "payload_hash": e.payload_hash,
                                "prev_hash": e.prev_hash,
                                "correlation_id": e.correlation_id,
                                "entry_hash": e.entry_hash,
                            }
                            for e in events
                        ],
                        indent=2,
                    ))
                else:
                    print(f"Events for correlation_id: {args.events}")
                    print(f"Total: {len(events)} events")
                    print("-" * 80)
                    for e in events:
                        print(f"[{e.timestamp.isoformat()}] {e.actor} | {e.event_type}")
                        print(f"  payload_hash: {e.payload_hash}")
                        print(f"  entry_hash:   {e.entry_hash}")
                        print()
                return 0

            if args.correlation_id:
                result = await verifier.verify_by_correlation_id(args.correlation_id)
            else:
                result = await verifier.verify()

            if args.json:
                print(json.dumps(
                    {
                        "is_valid": result.is_valid,
                        "total_entries": result.total_entries,
                        "verified_entries": result.verified_entries,
                        "first_invalid_index": result.first_invalid_index,
                        "duration_ms": result.duration_ms,
                        "chain_head": result.chain_head,
                        "error_message": result.error_message,
                    },
                    indent=2,
                ))
            else:
                print("=" * 60)
                print("AUDIT CHAIN VERIFICATION RESULT")
                print("=" * 60)
                print(f"  Status:       {'VALID ✓' if result.is_valid else 'INVALID ✗'}")
                print(f"  Total entries: {result.total_entries}")
                print(f"  Verified:      {result.verified_entries}")
                print(f"  Duration:      {result.duration_ms}ms")
                print(f"  Chain head:    {result.chain_head[:16]}...")
                if result.error_message:
                    print(f"  Error:         {result.error_message}")
                print("=" * 60)

            return 0 if result.is_valid else 1

        finally:
            await storage.close()


    if __name__ == "__main__":
        sys.exit(asyncio.run(main()))
    ```

    IMPORTANT:
    - Make the file executable with `chmod +x` (on Unix) or add shebang line
    - Exit code 0 = chain valid, exit code 1 = chain invalid or error
    - `--json` flag for machine-readable output (CI/CD integration)
    - `--events` flag for forensic reconstruction — prints all events for a correlation ID
    - `--correlation-id` flag for targeted verification of a single test run
    - Default to SQLite if no `--database-url` provided (dev mode)
    - The CLI does NOT accept any write operations — read-only verification only
  </action>
  <verify>
    # 1. Verify CLI help
    python services/audit/verify_audit.py --help

    # 2. Verify CLI with empty SQLite (should show valid chain with 0 entries)
    python services/audit/verify_audit.py --sqlite-path ":memory:"

    # 3. Verify CLI JSON output
    python services/audit/verify_audit.py --sqlite-path ":memory:" --json
  </verify>
  <done>
    verify_audit.py CLI script accepts --database-url, --sqlite-path, --correlation-id, --events, and --json flags. Exit code 0 for valid chain, 1 for invalid. Human-readable and JSON output modes. Forensic reconstruction via --events flag.
  </done>
</task>

</tasks>

<verification>
Run these in sequence after `uv sync --all-packages --all-extras`:

```bash
# 1. Verify all imports
python -c "
from audit.verify import AuditVerifier, VerificationResult
print('Verifier imports OK')
"

# 2. Run all verification tests
uv run pytest services/audit/tests/test_verify.py -v

# 3. Verify CLI works
python services/audit/verify_audit.py --help
python services/audit/verify_audit.py --sqlite-path ":memory:" --json
```
</verification>

<success_criteria>
- AuditVerifier.verify() recomputes every hash and confirms chain integrity
- Verification detects any single-byte modification (tampered entry fails verification)
- Verification of 10K entries completes in <1s (performance test passes)
- get_correlation_events returns all related events in chronological order
- verify_audit.py CLI accepts --database-url, --sqlite-path, --correlation-id, --events, --json
- CLI exit code 0 = valid, 1 = invalid
- JSON output mode works for CI/CD integration
</success_criteria>

<output>
After completion, create `.planning/phases/09-audit-log-service/09-audit-log-service-02-SUMMARY.md`
</output>
