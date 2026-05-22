"""Tests for KeyRotator — verifies secrets are readable after rotation."""

import pytest

from centinela.secrets import SQLiteSecretStore, SecretManager, derive_key, generate_salt
from centinela.secrets.rotation import KeyRotationError, KeyRotator


@pytest.fixture
def old_manager():
    salt = generate_salt()
    key = derive_key("old-password", salt)
    return SecretManager(key)


@pytest.fixture
def new_manager():
    salt = generate_salt()
    key = derive_key("new-password", salt)
    return SecretManager(key)


def test_rotation_secrets_readable_after(tmp_path, old_manager, new_manager):
    """Secrets written with old key are readable after rotation with new key."""
    db_path = tmp_path / "secrets.db"
    old_store = SQLiteSecretStore(db_path, old_manager)
    new_store = SQLiteSecretStore(db_path, new_manager)

    # Write secrets with old key
    old_store.set_secret("key1", b"value1")
    old_store.set_secret("key2", b"value2")

    # Rotate
    rotator = KeyRotator(old_store, new_store)
    rotator.rotate()

    # New store should be able to read them
    assert new_store.get_secret("key1") == b"value1"
    assert new_store.get_secret("key2") == b"value2"


def test_rotation_all_secrets_migrated(tmp_path, old_manager, new_manager):
    """All secrets in the store are migrated to the new key."""
    db_path = tmp_path / "secrets.db"
    old_store = SQLiteSecretStore(db_path, old_manager)
    new_store = SQLiteSecretStore(db_path, new_manager)

    for i in range(5):
        old_store.set_secret(f"secret_{i}", f"value_{i}".encode())

    rotator = KeyRotator(old_store, new_store)
    rotator.rotate()

    for i in range(5):
        assert new_store.get_secret(f"secret_{i}") == f"value_{i}".encode()


def test_rotation_empty_store_no_error(tmp_path, old_manager, new_manager):
    """Rotating an empty store completes without raising."""
    db_path = tmp_path / "secrets.db"
    old_store = SQLiteSecretStore(db_path, old_manager)
    new_store = SQLiteSecretStore(db_path, new_manager)

    rotator = KeyRotator(old_store, new_store)
    rotator.rotate()  # Should not raise


def test_rotation_old_key_still_readable_before_rotation(tmp_path, old_manager, new_manager):
    """Sanity check: old store can read its own secrets before rotation."""
    db_path = tmp_path / "secrets.db"
    old_store = SQLiteSecretStore(db_path, old_manager)

    old_store.set_secret("mykey", b"myvalue")
    assert old_store.get_secret("mykey") == b"myvalue"


def test_rotation_new_key_cannot_read_before_rotation(tmp_path, old_manager, new_manager):
    """New store cannot decrypt secrets written by old store (different keys)."""
    from cryptography.exceptions import InvalidTag

    db_path = tmp_path / "secrets.db"
    old_store = SQLiteSecretStore(db_path, old_manager)
    new_store = SQLiteSecretStore(db_path, new_manager)

    old_store.set_secret("mykey", b"myvalue")

    with pytest.raises((InvalidTag, Exception)):
        new_store.get_secret("mykey")
