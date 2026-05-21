"""Cryptographic secrets management for secure credential handling.

Exports:
- SecretManager: AES-256-GCM encryption/decryption
- SecretRef: Reference to tmpfs-mounted secrets
- derive_key: PBKDF2 key derivation
- generate_salt: Random salt generation
- SecretStore: Abstract backend interface
"""

from .manager import (
    SecretManager,
    SecretRef,
    SecretStore,
    derive_key,
    generate_salt,
)

__all__ = [
    "SecretManager",
    "SecretRef",
    "SecretStore",
    "derive_key",
    "generate_salt",
]
