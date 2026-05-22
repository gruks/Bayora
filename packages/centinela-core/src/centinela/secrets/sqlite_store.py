"""SQLite-backed secret store with application-level AES-256-GCM encryption."""

import sqlite3
from pathlib import Path

from .manager import SecretManager, SecretStore


class SQLiteSecretStore(SecretStore):
    """Stores secrets in SQLite with app-level AES-256-GCM encryption.

    Payloads are encrypted by SecretManager before insertion — the DB
    never contains plaintext secrets.
    """

    def __init__(self, db_path: str | Path, manager: SecretManager) -> None:
        self._db_path = str(db_path)
        self._manager = manager
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self._db_path)
        try:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS secrets (
                    name TEXT PRIMARY KEY,
                    ciphertext TEXT NOT NULL,
                    nonce TEXT NOT NULL
                )"""
            )
            conn.commit()
        finally:
            conn.close()

    def get_secret(self, name: str) -> bytes | None:
        conn = sqlite3.connect(self._db_path)
        try:
            row = conn.execute(
                "SELECT ciphertext, nonce FROM secrets WHERE name = ?", (name,)
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return None
        ciphertext_b64, nonce_b64 = row
        return self._manager.decrypt_string(ciphertext_b64, nonce_b64).encode("utf-8")

    def set_secret(self, name: str, value: bytes) -> None:
        ciphertext_b64, nonce_b64 = self._manager.encrypt_string(value.decode("utf-8"))
        conn = sqlite3.connect(self._db_path)
        try:
            conn.execute(
                """INSERT INTO secrets (name, ciphertext, nonce)
                   VALUES (?, ?, ?)
                   ON CONFLICT(name) DO UPDATE SET
                       ciphertext = excluded.ciphertext,
                       nonce = excluded.nonce""",
                (name, ciphertext_b64, nonce_b64),
            )
            conn.commit()
        finally:
            conn.close()

    def delete_secret(self, name: str) -> bool:
        conn = sqlite3.connect(self._db_path)
        try:
            cursor = conn.execute("DELETE FROM secrets WHERE name = ?", (name,))
            conn.commit()
            rowcount = cursor.rowcount
        finally:
            conn.close()
        return rowcount > 0

    def list_secrets(self) -> list[str]:
        conn = sqlite3.connect(self._db_path)
        try:
            rows = conn.execute("SELECT name FROM secrets ORDER BY name").fetchall()
        finally:
            conn.close()
        return [row[0] for row in rows]
