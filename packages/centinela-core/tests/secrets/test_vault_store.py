"""Tests for VaultSecretStore using a mocked hvac client."""

from unittest.mock import MagicMock

import pytest

from centinela.secrets import VaultSecretStore


@pytest.fixture
def mock_client():
    client = MagicMock()
    # Set up KV v2 read response
    client.secrets.kv.v2.read_secret_version.return_value = {
        "data": {"data": {"value": "secret-value"}}
    }
    client.secrets.kv.v2.list_secrets.return_value = {
        "data": {"keys": ["centinela/key_a", "centinela/key_b"]}
    }
    return client


@pytest.fixture
def store(mock_client):
    return VaultSecretStore(mock_client, mount_point="secret", path_prefix="centinela")


def test_get_secret(store, mock_client):
    result = store.get_secret("api_key")
    assert result == b"secret-value"
    mock_client.secrets.kv.v2.read_secret_version.assert_called_once_with(
        path="centinela/api_key",
        mount_point="secret",
    )


def test_get_secret_not_found(store, mock_client):
    mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception("not found")
    assert store.get_secret("missing") is None


def test_set_secret(store, mock_client):
    store.set_secret("new_key", b"new-value")
    mock_client.secrets.kv.v2.create_or_update_secret.assert_called_once_with(
        path="centinela/new_key",
        secret={"value": "new-value"},
        mount_point="secret",
    )


def test_delete_secret(store, mock_client):
    result = store.delete_secret("old_key")
    assert result is True
    mock_client.secrets.kv.v2.delete_metadata_and_all_versions.assert_called_once()


def test_delete_secret_failure(store, mock_client):
    mock_client.secrets.kv.v2.delete_metadata_and_all_versions.side_effect = Exception("error")
    assert store.delete_secret("key") is False


def test_list_secrets(store, mock_client):
    names = store.list_secrets()
    # Keys are returned with trailing slash stripped
    assert len(names) == 2
    assert "centinela/key_a" in names
    assert "centinela/key_b" in names


def test_list_secrets_empty_on_error(store, mock_client):
    mock_client.secrets.kv.v2.list_secrets.side_effect = Exception("error")
    assert store.list_secrets() == []
