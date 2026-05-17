"""Cryptographic secrets management with AES-256-GCM encryption.

Provides secure encryption, key derivation, and secret rotation.
"""

import os
from abc import ABC, abstractmethod
from base64 import b64decode, b64encode

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pydantic import BaseModel, Field

# AES-256-GCM uses 256-bit (32-byte) key
KEY_SIZE_BYTES = 32
# Recommended nonce size for GCM is 12 bytes (96 bits)
NONCE_SIZE_BYTES = 12
# Salt size for key derivation (16 bytes recommended)
SALT_SIZE_BYTES = 16


class SecretRef(BaseModel, frozen=True):
    """Reference to a cryptographic secret stored in tmpfs.

    Provides secure access to secrets without writing to disk.
    """

    name: str = Field(description="Secret name identifier")
    path: str | None = Field(default=None, description="tmpfs mount point path")
    encryption_key_id: str | None = Field(default=None, description="Key identifier for encryption")


def generate_salt() -> bytes:
    """Generate a random salt for key derivation.

    Returns:
        16 bytes of cryptographically secure random data
    """
    return os.urandom(SALT_SIZE_BYTES)


def derive_key(password: str, salt: bytes, iterations: int = 600000) -> bytes:
    """Derive a key from a password using PBKDF2-HMAC-SHA256.

    Uses 600,000 iterations as recommended for password-based key derivation.

    Args:
        password: Password string to derive key from
        salt: Salt bytes for key derivation
        iterations: Number of PBKDF2 iterations (default: 600,000)

    Returns:
        32-byte derived key suitable for AES-256
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE_BYTES,
        salt=salt,
        iterations=iterations,
        backend=default_backend(),
    )
    return kdf.derive(password.encode("utf-8"))


class SecretManager:
    """Manages encryption and decryption of secrets using AES-256-GCM.

    Provides:
    - AES-256-GCM encryption with authenticated encryption
    - PBKDF2 key derivation from passwords
    - Key rotation support
    - Master key management

    The master key should be stored securely (e.g., in memory only, tmpfs).
    """

    def __init__(self, master_key: bytes) -> None:
        """Initialize SecretManager with a master key.

        Args:
            master_key: 32-byte master key for encryption

        Raises:
            ValueError: If master_key is not 32 bytes
        """
        if len(master_key) != KEY_SIZE_BYTES:
            raise ValueError(f"Master key must be {KEY_SIZE_BYTES} bytes, got {len(master_key)}")
        self._key = master_key
        self._aesgcm = AESGCM(master_key)

    def encrypt(self, plaintext: bytes) -> tuple[bytes, bytes]:
        """Encrypt plaintext using AES-256-GCM.

        Generates a random nonce for each encryption operation.

        Args:
            plaintext: Data to encrypt

        Returns:
            Tuple of (ciphertext, nonce) - both as bytes
        """
        nonce = os.urandom(NONCE_SIZE_BYTES)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext, None)
        return ciphertext, nonce

    def decrypt(self, ciphertext: bytes, nonce: bytes) -> bytes:
        """Decrypt ciphertext using AES-256-GCM.

        Args:
            ciphertext: Encrypted data
            nonce: Nonce used during encryption

        Returns:
            Decrypted plaintext bytes

        Raises:
            InvalidTag: If authentication fails (tampering detected)
        """
        return self._aesgcm.decrypt(nonce, ciphertext, None)

    def encrypt_string(self, plaintext: str) -> tuple[str, str]:
        """Encrypt a string and return base64-encoded result.

        Convenience method that handles string encoding and base64 output.

        Args:
            plaintext: String to encrypt

        Returns:
            Tuple of (base64_ciphertext, base64_nonce)
        """
        ciphertext, nonce = self.encrypt(plaintext.encode("utf-8"))
        return b64encode(ciphertext).decode("utf-8"), b64encode(nonce).decode("utf-8")

    def decrypt_string(self, ciphertext_b64: str, nonce_b64: str) -> str:
        """Decrypt base64-encoded ciphertext.

        Convenience method that handles base64 decoding and string output.

        Args:
            ciphertext_b64: Base64-encoded ciphertext
            nonce_b64: Base64-encoded nonce

        Returns:
            Decrypted plaintext string
        """
        ciphertext = b64decode(ciphertext_b64)
        nonce = b64decode(nonce_b64)
        plaintext = self.decrypt(ciphertext, nonce)
        return plaintext.decode("utf-8")

    def rotate_key(self, new_master_key: bytes) -> "SecretManager":
        """Create a new SecretManager with a rotated key.

        Used for key rotation scenarios.

        Args:
            new_master_key: New 32-byte master key

        Returns:
            New SecretManager instance with rotated key
        """
        return SecretManager(new_master_key)


class SecretStore(ABC):
    """Abstract interface for secret storage backends.

    Implementations can use SQLite, HashiCorp Vault, or other backends.
    """

    @abstractmethod
    def get_secret(self, name: str) -> bytes | None:
        """Retrieve a secret by name.

        Args:
            name: Secret identifier

        Returns:
            Secret value as bytes, or None if not found
        """
        pass

    @abstractmethod
    def set_secret(self, name: str, value: bytes) -> None:
        """Store a secret.

        Args:
            name: Secret identifier
            value: Secret value as bytes
        """
        pass

    @abstractmethod
    def delete_secret(self, name: str) -> bool:
        """Delete a secret by name.

        Args:
            name: Secret identifier

        Returns:
            True if secret was deleted, False if not found
        """
        pass

    @abstractmethod
    def list_secrets(self) -> list[str]:
        """List all secret names.

        Returns:
            List of secret identifiers
        """
        pass


__all__ = [
    "SecretManager",
    "SecretRef",
    "SecretStore",
    "derive_key",
    "generate_salt",
]
