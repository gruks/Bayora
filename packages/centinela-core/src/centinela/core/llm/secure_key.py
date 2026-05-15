from __future__ import annotations


class SecureKeyStore:
    """RAM-only API key storage using memoryview with deterministic zeroing.

    Usage:
        key = "sk-..."
        with SecureKeyStore(key) as store:
            # key is accessible via store.get_str() or store.get_view()
            api_key_str = store.get_str()
            # ... use api_key_str (e.g. pass to litellm) ...
        # After context exit: key is zeroed, get_str() returns empty string

    Security properties:
    - Key stored as bytearray (mutable, controllable memory)
    - memoryview wraps bytearray for zero-copy access
    - .clear() zeroes all bytes then releases the memoryview
    - __del__ provides safety net if context manager not used
    - is_zeroed property enables verification in tests
    """

    def __init__(self, key: str) -> None:
        if not isinstance(key, str):
            raise TypeError("API key must be a string")
        self._buf = bytearray(key.encode("utf-8"))
        self._view = memoryview(self._buf)
        self._released = False

    def get_view(self) -> memoryview:
        """Return the memoryview for zero-copy access."""
        if self._released:
            raise RuntimeError("SecureKeyStore has already been cleared")
        return self._view

    def get_str(self) -> str:
        """Reconstruct the key string from the bytearray backing store.

        Note: This creates a new str object. The caller is responsible
        for not letting this string persist beyond its useful lifetime.
        """
        if self._released:
            return ""
        return self._buf.decode("utf-8")

    def clear(self) -> None:
        """Zero all key bytes and release the memoryview.

        Safe to call multiple times — subsequent calls are no-ops.
        """
        if self._released:
            return
        # Zero every byte in the buffer
        self._view.cast("B")[:] = b"\x00" * len(self._buf)
        self._view.release()
        self._released = True
        # Also zero the backing bytearray
        self._buf[:] = b"\x00" * len(self._buf)

    @property
    def is_zeroed(self) -> bool:
        """True if memory has been cleared and view released."""
        if not self._released:
            return False
        return all(b == 0 for b in self._buf)

    @property
    def is_active(self) -> bool:
        """True if key is still accessible (not yet cleared)."""
        return not self._released

    def __enter__(self) -> SecureKeyStore:
        return self

    def __exit__(self, *args: object) -> None:
        self.clear()

    def __del__(self) -> None:
        """Safety net: clear if context manager wasn't used."""
        if not self._released:
            self.clear()

    def __repr__(self) -> str:
        status = "active" if self.is_active else "zeroed"
        return f"<SecureKeyStore: {status}>"
