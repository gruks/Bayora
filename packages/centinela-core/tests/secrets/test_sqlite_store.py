"""Tests for SQLiteSecretStore."""

import sqlite3

import pytest

from centinela.secrets import SQLiteSecretStore, SecretManager, derive_key, generate_salt


@pytest.fixture
def manager():
    salt = generate_salt()
    key = derive_key("test-password", salt)
    return SecretManager(key)


@pytest.fixture
def store(manager, tmp_path):
    db_path = tmp_path / "test_secrets.db"
    return SQLiteSecretStore(db_path, manager)


def test_set_and_get_secret(store):
    store.set_secret("api_key", b"super-secret-value")
    result = store.get_secret("api_key")
    assert result == b"super-secret-value"


def test_get_nonexistent_returns_none(store):
    assert store.get_secret("nonexistent") is None


def test_delete_secret(store):
    store.set_secret("to_delete", b"value")
    assert store.delete_secret("to_delete") is True
    assert store.get_secret("to_delete") is None


def test_delete_nonexistent_returns_false(store):
    assert store.delete_secret("nonexistent") is False


def test_list_secrets(store):
    store.set_secret("key_a", b"val_a")
    store.set_secret("key_b", b"val_b")
    names = store.list_secrets()
    assert "key_a" in names
    assert "key_b" in names


def test_overwrite_secret(store):
    store.set_secret("key", b"original")
    store.set_secret("key", b"updated")
    assert store.get_secret("key") == b"updated"


def test_payload_is_encrypted_in_db(tmp_path, manager):
    """Verify the DB does not contain plaintext."""
    db_path = tmp_path / "test_secrets.db"
    s = SQLiteSecretStore(db_path, manager)
    s.set_secret("sensitive", b"plaintext-secret")
    with sqlite3.connect(str(db_path)) as conn:
        row = conn.execute("SELECT ciphertext FROM secrets WHERE name='sensitive'").fetchone()
    assert row is not None
    assert b"plaintext-secret" not in row[0].encode("utf-8")
