"""Automatic key rotation for the master encryption key.

Reads all secrets via the old store (decrypts with old key),
then writes them back via a new store instance (encrypts with new key).
Designed to be called on a schedule (e.g., every 24h).
"""

from .manager import SecretStore


class KeyRotationError(Exception):
    """Raised when key rotation fails for one or more secrets."""


class KeyRotator:
    """Rotates the master encryption key and re-encrypts all secrets.

    Reads all secrets via the old store (decrypts with old key),
    then writes them back via a new store instance (encrypts with new key).
    Both stores must point to the same backend (e.g., same SQLite DB path)
    but hold different ``SecretManager`` instances.

    If any secret fails to re-encrypt, the error is collected and rotation
    continues for remaining secrets. A ``KeyRotationError`` is raised at the
    end summarising all failures.

    Args:
        old_store: SecretStore using the current (old) key.
        new_store: SecretStore using the new key (same backend, new manager).
    """

    def __init__(self, old_store: SecretStore, new_store: SecretStore) -> None:
        self._old_store = old_store
        self._new_store = new_store

    def rotate(self) -> None:
        """Re-encrypt all secrets from *old_store* into *new_store*.

        For each secret name returned by ``old_store.list_secrets()``:

        1. Decrypt the value using the old manager (via ``old_store.get_secret``).
        2. Re-encrypt and persist using the new manager (via ``new_store.set_secret``).

        Raises:
            KeyRotationError: If any secrets fail to re-encrypt.
        """
        errors: list[str] = []

        for name in self._old_store.list_secrets():
            try:
                value = self._old_store.get_secret(name)
                if value is None:
                    continue
                self._new_store.set_secret(name, value)
            except Exception as exc:
                errors.append(f"{name}: {exc}")

        if errors:
            raise KeyRotationError(
                f"Key rotation failed for {len(errors)} secret(s): {'; '.join(errors)}"
            )


__all__ = ["KeyRotationError", "KeyRotator"]
