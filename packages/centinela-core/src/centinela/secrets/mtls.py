"""mTLS certificate generation utilities.

Generates an internal Certificate Authority (CA) and issues
client/server X.509 certificates for mutual TLS authentication
between orchestrator and agents.

All certificates use ECDSA P-256 keys and SHA-256 signatures.
"""

import datetime

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


def _utcnow() -> datetime.datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.datetime.now(datetime.UTC)


def generate_ca(
    common_name: str = "CENTINELA Internal CA",
    validity_days: int = 3650,
) -> tuple[bytes, bytes]:
    """Generate a self-signed CA certificate and private key.

    Args:
        common_name: CN for the CA certificate.
        validity_days: Certificate validity period in days (default: 10 years).

    Returns:
        Tuple of ``(ca_cert_pem, ca_key_pem)`` as PEM-encoded bytes.
    """
    key = ec.generate_private_key(ec.SECP256R1())
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "CENTINELA"),
        ]
    )
    now = _utcnow()
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=validity_days))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(key.public_key()),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    return cert_pem, key_pem


def generate_server_cert(
    ca_cert_pem: bytes,
    ca_key_pem: bytes,
    common_name: str,
    san_dns_names: list[str] | None = None,
    validity_days: int = 365,
) -> tuple[bytes, bytes]:
    """Generate a server certificate signed by the CA.

    The certificate includes the ``SERVER_AUTH`` Extended Key Usage OID and a
    Subject Alternative Name extension containing at least the *common_name*
    as a DNS SAN.

    Args:
        ca_cert_pem: CA certificate in PEM format.
        ca_key_pem: CA private key in PEM format.
        common_name: CN for the server certificate (also added as a DNS SAN).
        san_dns_names: Optional additional DNS SANs.
        validity_days: Certificate validity period in days (default: 1 year).

    Returns:
        Tuple of ``(server_cert_pem, server_key_pem)`` as PEM-encoded bytes.
    """
    ca_cert = x509.load_pem_x509_certificate(ca_cert_pem)
    ca_key = serialization.load_pem_private_key(ca_key_pem, password=None)

    key = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "CENTINELA"),
        ]
    )
    now = _utcnow()

    # Always include the CN as a DNS SAN; append any extras.
    san_names: list[x509.GeneralName] = [x509.DNSName(common_name)]
    for dns in san_dns_names or []:
        san_names.append(x509.DNSName(dns))

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=validity_days))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.SubjectAlternativeName(san_names), critical=False)
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    return cert_pem, key_pem


def generate_client_cert(
    ca_cert_pem: bytes,
    ca_key_pem: bytes,
    common_name: str,
    validity_days: int = 365,
) -> tuple[bytes, bytes]:
    """Generate a client certificate signed by the CA.

    The certificate includes the ``CLIENT_AUTH`` Extended Key Usage OID,
    identifying it as a valid mTLS client credential.

    Args:
        ca_cert_pem: CA certificate in PEM format.
        ca_key_pem: CA private key in PEM format.
        common_name: CN for the client certificate (e.g. ``"red-agent"``).
        validity_days: Certificate validity period in days (default: 1 year).

    Returns:
        Tuple of ``(client_cert_pem, client_key_pem)`` as PEM-encoded bytes.
    """
    ca_cert = x509.load_pem_x509_certificate(ca_cert_pem)
    ca_key = serialization.load_pem_private_key(ca_key_pem, password=None)

    key = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "CENTINELA"),
        ]
    )
    now = _utcnow()

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=validity_days))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    return cert_pem, key_pem


__all__ = ["generate_ca", "generate_client_cert", "generate_server_cert"]
