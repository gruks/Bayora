"""Tests for SecureKeyStore — memoryview-backed RAM-only API key storage.

These tests verify the security contract:
- Key is stored in mutable bytearray (not immutable str/bytes)
- memoryview wraps for zero-copy access
- .clear() zeroes ALL bytes deterministically
- Context manager guarantees cleanup on scope exit
- Double clear is safe (idempotent)
- __del__ provides safety net if context manager forgotten
"""

from __future__ import annotations

import gc

from centinela.core.llm import SecureKeyStore


class TestSecureKeyStoreLifecycle:
    """Full lifecycle: create → use → clear → verify zeroed."""

    def test_store_and_retrieve(self) -> None:
        ks = SecureKeyStore("sk-test-key-12345")
        assert ks.is_active
        assert ks.get_str() == "sk-test-key-12345"
        assert len(ks.get_view()) == len("sk-test-key-12345")
        ks.clear()
        assert ks.is_zeroed

    def test_get_str_after_clear_returns_empty(self) -> None:
        ks = SecureKeyStore("sk-secret")
        ks.clear()
        assert ks.get_str() == ""

    def test_get_view_after_clear_raises(self) -> None:
        ks = SecureKeyStore("sk-secret")
        ks.clear()
        import pytest

        with pytest.raises(RuntimeError, match="SecureKeyStore has already been cleared"):
            ks.get_view()

    def test_cannot_instantiate_with_non_string(self) -> None:
        import pytest

        with pytest.raises(TypeError, match="API key must be a string"):
            SecureKeyStore(123)  # type: ignore[arg-type]


class TestSecureKeyStoreZeroing:
    """Memory zeroing verification — this is a security test."""

    def test_all_bytes_zeroed_after_clear(self) -> None:
        ks = SecureKeyStore("sk-this-is-a-test-key-with-enough-length")
        original_len = len(ks.get_str())
        ks.clear()
        # After clear, the underlying bytearray should be all zeros
        assert ks.is_zeroed
        # Verify the buffer length is preserved (not truncated)
        assert len(ks._buf) == original_len
        # Prove every byte is actually zero
        assert all(b == 0 for b in ks._buf)

    def test_memoryview_released_after_clear(self) -> None:
        ks = SecureKeyStore("sk-test")
        view = ks.get_view()
        ks.clear()
        # memoryview should be released — accessing it raises ValueError
        import pytest

        with pytest.raises(ValueError):
            _ = view[0]  # released memoryview access

    def test_multiple_keys_independent_zeroing(self) -> None:
        """Each SecureKeyStore manages its own buffer independently."""
        ks1 = SecureKeyStore("sk-key-one")
        ks2 = SecureKeyStore("sk-key-two")
        ks1.clear()
        assert ks1.is_zeroed
        assert ks2.is_active  # ks2 should NOT be affected
        assert ks2.get_str() == "sk-key-two"
        ks2.clear()
        assert ks2.is_zeroed


class TestSecureKeyStoreContextManager:
    """Context manager guarantees cleanup on scope exit."""

    def test_context_manager_zeroes_on_exit(self) -> None:
        with SecureKeyStore("sk-context-key") as ks:
            assert ks.get_str() == "sk-context-key"
        assert ks.is_zeroed

    def test_context_manager_zeroes_even_on_error(self) -> None:
        """Even if an exception occurs inside the context, the key is zeroed."""
        try:
            with SecureKeyStore("sk-error-key") as ks:
                assert ks.is_active
                raise ValueError("simulated error")
        except ValueError:
            pass
        assert ks.is_zeroed

    def test_double_clear_is_safe(self) -> None:
        ks = SecureKeyStore("sk-double")
        ks.clear()
        ks.clear()  # Should not raise
        assert ks.is_zeroed

    def test_repr_active(self) -> None:
        ks = SecureKeyStore("sk-repr")
        assert repr(ks) == "<SecureKeyStore: active>"

    def test_repr_zeroed(self) -> None:
        ks = SecureKeyStore("sk-repr")
        ks.clear()
        assert repr(ks) == "<SecureKeyStore: zeroed>"


class TestSecureKeyStoreDel:
    """__del__ safety net — key zeroed if context manager not used.

    NOTE: This tests best-effort behavior. CPython's GC may not call
    __del__ immediately, but when it does, the key must be zeroed.
    """

    def test_del_clears_key(self) -> None:
        ks = SecureKeyStore("sk-del-test")
        ks_ref = ks
        del ks
        gc.collect()
        assert ks_ref.is_zeroed

    def test_del_after_manual_clear_no_double_free(self) -> None:
        """If already cleared, __del__ should be a no-op."""
        ks = SecureKeyStore("sk-del-clear")
        ks.clear()
        del ks  # Should not raise
        gc.collect()
