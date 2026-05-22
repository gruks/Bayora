#!/usr/bin/env python3
"""verify_audit.py — Audit chain verification CLI.

Recomputes every hash and confirms chain integrity.
Detects any single-byte modification in any entry.

Usage:
    python verify_audit.py --sqlite-path audit.db
    python verify_audit.py --database-url "postgresql://user:pass@host/db"
    python verify_audit.py --sqlite-path audit.db --correlation-id "test-001"
    python verify_audit.py --sqlite-path audit.db --events "test-001"
    python verify_audit.py --sqlite-path audit.db --json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from audit.storage import PostgreSQLStorage, SQLiteStorage
from audit.verify import AuditVerifier


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify audit chain integrity")
    parser.add_argument("--database-url", help="PostgreSQL connection URL")
    parser.add_argument(
        "--sqlite-path", default="audit.db", help="SQLite database path (default: audit.db)"
    )
    parser.add_argument("--correlation-id", help="Verify only entries matching this correlation ID")
    parser.add_argument(
        "--events",
        metavar="CORRELATION_ID",
        help="Print all events for a correlation ID (forensic reconstruction)",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    return parser.parse_args()


async def main() -> int:
    args = parse_args()

    if args.database_url:
        storage = PostgreSQLStorage(dsn=args.database_url)
    else:
        storage = SQLiteStorage(path=args.sqlite_path)

    await storage.initialize()

    try:
        verifier = AuditVerifier(storage)

        if args.events:
            events = await verifier.get_correlation_events(args.events)
            if not events:
                print(f"No events found for correlation_id: {args.events}")
                return 1

            if args.json:
                print(
                    json.dumps(
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
                    )
                )
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
            print(
                json.dumps(
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
                )
            )
        else:
            print("=" * 60)
            print("AUDIT CHAIN VERIFICATION RESULT")
            print("=" * 60)
            print(f"  Status:        {'VALID' if result.is_valid else 'INVALID'}")
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
