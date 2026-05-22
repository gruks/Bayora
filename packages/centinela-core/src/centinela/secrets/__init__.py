"""Cryptographic secrets management for secure credential handling."""

from .abac import ABACEngine, AccessDeniedError
from .abac_models import (
    ABACPolicy,
    ABACRule,
    Action,
    Effect,
    ResourceSpec,
    SubjectSpec,
)
from .injector import SecretInjectionError, SecretInjector
from .manager import (
    SecretManager,
    SecretRef,
    SecretStore,
    derive_key,
    generate_salt,
)
from .mtls import generate_ca, generate_client_cert, generate_server_cert
from .rotation import KeyRotationError, KeyRotator
from .secure_store import SecureSecretStore
from .sqlite_store import SQLiteSecretStore
from .vault_store import VaultSecretStore

__all__ = [
    "ABACEngine",
    "ABACPolicy",
    "ABACRule",
    "AccessDeniedError",
    "Action",
    "Effect",
    "KeyRotationError",
    "KeyRotator",
    "ResourceSpec",
    "SQLiteSecretStore",
    "SecretInjectionError",
    "SecretInjector",
    "SecretManager",
    "SecretRef",
    "SecretStore",
    "SecureSecretStore",
    "SubjectSpec",
    "VaultSecretStore",
    "derive_key",
    "generate_ca",
    "generate_client_cert",
    "generate_salt",
    "generate_server_cert",
]
