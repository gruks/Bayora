"""tmpfs-based secret injection for container environments.

Writes decrypted secrets to a tmpfs-mounted path with strict permissions
so secrets never touch persistent disk storage.
"""

import contextlib
import os
import stat
from pathlib import Path

from .manager import SecretRef, SecretStore


class SecretInjectionError(Exception):
    """Raised when secret injection or cleanup fails."""


class SecretInjector:
    """Injects secrets from a SecretStore into a tmpfs-mounted directory.

    Secrets are written with 0o400 permissions (owner read-only).
    Cleanup zeroes the file content before unlinking.

    Args:
        store: SecretStore backend to retrieve secrets from
        base_path: Base directory for secret files (should be a tmpfs mount,
                   e.g. /dev/shm/secrets or /var/run/secrets)
    """

    def __init__(self, store: SecretStore, base_path: str | Path = "/dev/shm/secrets") -> None:
        self._store = store
        self._base_path = Path(base_path)

    def _secret_path(self, secret_ref: SecretRef) -> Path:
        """Return the file path for a given SecretRef."""
        # Use ref.path if provided, otherwise derive from name
        if secret_ref.path:
            return Path(secret_ref.path)
        return self._base_path / secret_ref.name

    def inject(self, secret_ref: SecretRef) -> Path:
        """Retrieve a secret and write it to the tmpfs path.

        Creates parent directories if needed. Sets file permissions to 0o400.

        Args:
            secret_ref: Reference identifying the secret to inject

        Returns:
            Path where the secret was written

        Raises:
            SecretInjectionError: If the secret is not found or write fails
        """
        value = self._store.get_secret(secret_ref.name)
        if value is None:
            raise SecretInjectionError(f"Secret '{secret_ref.name}' not found in store")

        dest = self._secret_path(secret_ref)
        dest.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Write with restrictive permissions from the start
            fd = os.open(str(dest), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o400)
            try:
                os.write(fd, value)
            finally:
                os.close(fd)
        except OSError as exc:
            raise SecretInjectionError(f"Failed to write secret '{secret_ref.name}': {exc}") from exc

        # Enforce 0o400 even if umask interfered
        os.chmod(str(dest), stat.S_IRUSR)
        return dest

    def cleanup(self, secret_ref: SecretRef) -> None:
        """Zero out and remove the injected secret file.

        Overwrites the file content with null bytes before unlinking
        to reduce the window for memory-mapped file recovery.

        Args:
            secret_ref: Reference identifying the secret to clean up
        """
        dest = self._secret_path(secret_ref)
        if not dest.exists():
            return

        try:
            # Zero out content before unlinking
            size = dest.stat().st_size
            if size > 0:
                # Temporarily make writable to overwrite
                os.chmod(str(dest), stat.S_IRUSR | stat.S_IWUSR)
                with open(dest, "r+b") as f:
                    f.write(b"\x00" * size)
                    f.flush()
                    os.fsync(f.fileno())
            dest.unlink()
        except OSError:
            # Best-effort cleanup — still attempt unlink
            with contextlib.suppress(OSError):
                dest.unlink(missing_ok=True)
