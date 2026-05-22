"""ABAC-enforcing proxy wrapper around SecretStore."""

from typing import Any

from .abac import ABACEngine, AccessDeniedError
from .abac_models import Action
from .manager import SecretStore


class SecureSecretStore(SecretStore):
    """Wraps a SecretStore with ABAC policy enforcement.

    All operations are gated through ABACEngine.evaluate().
    Raises AccessDeniedError if the policy denies access.

    Args:
        store: Underlying SecretStore backend
        engine: ABACEngine with the policy to enforce
        subject_attrs: Attributes of the current caller/tenant
    """

    def __init__(
        self,
        store: SecretStore,
        engine: ABACEngine,
        subject_attrs: dict[str, Any],
    ) -> None:
        self._store = store
        self._engine = engine
        self._subject_attrs = subject_attrs

    def _check(self, name: str, action: Action) -> None:
        if not self._engine.evaluate(self._subject_attrs, name, action):
            raise AccessDeniedError(
                f"Access denied: subject {self._subject_attrs!r} cannot "
                f"perform '{action}' on secret '{name}'"
            )

    def get_secret(self, name: str) -> bytes | None:
        self._check(name, Action.READ)
        return self._store.get_secret(name)

    def set_secret(self, name: str, value: bytes) -> None:
        self._check(name, Action.WRITE)
        self._store.set_secret(name, value)

    def delete_secret(self, name: str) -> bool:
        self._check(name, Action.DELETE)
        return self._store.delete_secret(name)

    def list_secrets(self) -> list[str]:
        self._check("*", Action.LIST)
        return self._store.list_secrets()
