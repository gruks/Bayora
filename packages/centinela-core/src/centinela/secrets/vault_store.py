"""HashiCorp Vault-backed secret store using hvac KV v2."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import hvac

from .manager import SecretStore


class VaultSecretStore(SecretStore):
    """Stores secrets in HashiCorp Vault KV v2 secrets engine.

    Secrets are stored as plaintext in Vault (Vault handles its own
    encryption at rest). Use SecureSecretStore wrapper for ABAC.
    """

    def __init__(
        self,
        client: hvac.Client,
        mount_point: str = "secret",
        path_prefix: str = "centinela",
    ) -> None:
        self._client = client
        self._mount_point = mount_point
        self._path_prefix = path_prefix

    def _full_path(self, name: str) -> str:
        return f"{self._path_prefix}/{name}"

    def get_secret(self, name: str) -> bytes | None:
        try:
            response = self._client.secrets.kv.v2.read_secret_version(
                path=self._full_path(name),
                mount_point=self._mount_point,
            )
            value = response["data"]["data"].get("value")
            if value is None:
                return None
            return value.encode("utf-8") if isinstance(value, str) else value
        except Exception:
            return None

    def set_secret(self, name: str, value: bytes) -> None:
        self._client.secrets.kv.v2.create_or_update_secret(
            path=self._full_path(name),
            secret={"value": value.decode("utf-8")},
            mount_point=self._mount_point,
        )

    def delete_secret(self, name: str) -> bool:
        try:
            self._client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=self._full_path(name),
                mount_point=self._mount_point,
            )
            return True
        except Exception:
            return False

    def list_secrets(self) -> list[str]:
        try:
            response = self._client.secrets.kv.v2.list_secrets(
                path=self._path_prefix,
                mount_point=self._mount_point,
            )
            keys = response["data"]["keys"]
            return [k.rstrip("/") for k in keys]
        except Exception:
            return []
