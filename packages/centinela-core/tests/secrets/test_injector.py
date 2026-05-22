"""Tests for SecretInjector using a local temp directory to simulate tmpfs."""

import os
import platform
import stat
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from centinela.secrets import SecretRef
from centinela.secrets.injector import SecretInjectionError, SecretInjector


@pytest.fixture
def mock_store():
    store = MagicMock()
    store.get_secret.return_value = b"my-secret-value"
    return store


@pytest.fixture
def injector(mock_store, tmp_path):
    return SecretInjector(store=mock_store, base_path=tmp_path / "secrets")


@pytest.fixture
def secret_ref():
    return SecretRef(name="api_key")


def test_inject_creates_file(injector, secret_ref, tmp_path):
    path = injector.inject(secret_ref)
    assert path.exists()
    assert path.read_bytes() == b"my-secret-value"


def test_inject_sets_0400_permissions(injector, secret_ref):
    path = injector.inject(secret_ref)
    mode = stat.S_IMODE(os.stat(str(path)).st_mode)
    if platform.system() == "Windows":
        # Windows maps read-only to 0o444 (no per-user bits)
        assert mode & stat.S_IWRITE == 0, "File should not be writable"
    else:
        assert mode == 0o400


def test_inject_creates_parent_dirs(mock_store, tmp_path):
    nested_ref = SecretRef(name="nested/deep/key")
    inj = SecretInjector(store=mock_store, base_path=tmp_path / "secrets")
    path = inj.inject(nested_ref)
    assert path.exists()


def test_inject_raises_when_secret_not_found(injector, tmp_path):
    store = MagicMock()
    store.get_secret.return_value = None
    inj = SecretInjector(store=store, base_path=tmp_path / "secrets")
    ref = SecretRef(name="missing")
    with pytest.raises(SecretInjectionError, match="not found"):
        inj.inject(ref)


def test_cleanup_removes_file(injector, secret_ref):
    injector.inject(secret_ref)
    injector.cleanup(secret_ref)
    path = injector._secret_path(secret_ref)
    assert not path.exists()


def test_cleanup_nonexistent_is_noop(injector, secret_ref):
    # Should not raise even if file doesn't exist
    injector.cleanup(secret_ref)


def test_inject_uses_ref_path_when_provided(mock_store, tmp_path):
    custom_path = str(tmp_path / "custom" / "secret.txt")
    ref = SecretRef(name="api_key", path=custom_path)
    inj = SecretInjector(store=mock_store, base_path=tmp_path / "secrets")
    path = inj.inject(ref)
    assert str(path) == custom_path
    assert path.read_bytes() == b"my-secret-value"
