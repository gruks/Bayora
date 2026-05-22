"""Tests for mTLS certificate generation."""

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import ExtendedKeyUsageOID

from centinela.secrets.mtls import generate_ca, generate_client_cert, generate_server_cert


def test_generate_ca_returns_valid_pem():
    cert_pem, key_pem = generate_ca()
    assert cert_pem.startswith(b"-----BEGIN CERTIFICATE-----")
    assert key_pem.startswith(b"-----BEGIN EC PRIVATE KEY-----")


def test_ca_is_self_signed():
    cert_pem, _ = generate_ca(common_name="Test CA")
    cert = x509.load_pem_x509_certificate(cert_pem)
    assert cert.subject == cert.issuer


def test_ca_has_basic_constraints():
    cert_pem, _ = generate_ca()
    cert = x509.load_pem_x509_certificate(cert_pem)
    bc = cert.extensions.get_extension_for_class(x509.BasicConstraints)
    assert bc.value.ca is True


def test_server_cert_signed_by_ca():
    ca_cert_pem, ca_key_pem = generate_ca()
    server_cert_pem, _ = generate_server_cert(ca_cert_pem, ca_key_pem, "orchestrator")
    ca_cert = x509.load_pem_x509_certificate(ca_cert_pem)
    server_cert = x509.load_pem_x509_certificate(server_cert_pem)
    assert server_cert.issuer == ca_cert.subject


def test_server_cert_has_server_auth_eku():
    ca_cert_pem, ca_key_pem = generate_ca()
    server_cert_pem, _ = generate_server_cert(ca_cert_pem, ca_key_pem, "orchestrator")
    cert = x509.load_pem_x509_certificate(server_cert_pem)
    eku = cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage)
    assert ExtendedKeyUsageOID.SERVER_AUTH in eku.value


def test_client_cert_signed_by_ca():
    ca_cert_pem, ca_key_pem = generate_ca()
    client_cert_pem, _ = generate_client_cert(ca_cert_pem, ca_key_pem, "red-agent")
    ca_cert = x509.load_pem_x509_certificate(ca_cert_pem)
    client_cert = x509.load_pem_x509_certificate(client_cert_pem)
    assert client_cert.issuer == ca_cert.subject


def test_client_cert_has_client_auth_eku():
    ca_cert_pem, ca_key_pem = generate_ca()
    client_cert_pem, _ = generate_client_cert(ca_cert_pem, ca_key_pem, "red-agent")
    cert = x509.load_pem_x509_certificate(client_cert_pem)
    eku = cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage)
    assert ExtendedKeyUsageOID.CLIENT_AUTH in eku.value


def test_client_cert_common_name():
    ca_cert_pem, ca_key_pem = generate_ca()
    client_cert_pem, _ = generate_client_cert(ca_cert_pem, ca_key_pem, "blue-agent")
    cert = x509.load_pem_x509_certificate(client_cert_pem)
    cn = cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value
    assert cn == "blue-agent"


def test_server_cert_san_dns_names():
    ca_cert_pem, ca_key_pem = generate_ca()
    server_cert_pem, _ = generate_server_cert(
        ca_cert_pem,
        ca_key_pem,
        "orchestrator",
        san_dns_names=["orchestrator.svc.cluster.local"],
    )
    cert = x509.load_pem_x509_certificate(server_cert_pem)
    san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
    dns_names = san.value.get_values_for_type(x509.DNSName)
    assert "orchestrator.svc.cluster.local" in dns_names


def test_server_cert_cn_included_in_san():
    """The CN is always added as a DNS SAN even without explicit san_dns_names."""
    ca_cert_pem, ca_key_pem = generate_ca()
    server_cert_pem, _ = generate_server_cert(ca_cert_pem, ca_key_pem, "myserver")
    cert = x509.load_pem_x509_certificate(server_cert_pem)
    san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
    dns_names = san.value.get_values_for_type(x509.DNSName)
    assert "myserver" in dns_names


def test_server_cert_is_not_ca():
    ca_cert_pem, ca_key_pem = generate_ca()
    server_cert_pem, _ = generate_server_cert(ca_cert_pem, ca_key_pem, "orchestrator")
    cert = x509.load_pem_x509_certificate(server_cert_pem)
    bc = cert.extensions.get_extension_for_class(x509.BasicConstraints)
    assert bc.value.ca is False


def test_client_cert_is_not_ca():
    ca_cert_pem, ca_key_pem = generate_ca()
    client_cert_pem, _ = generate_client_cert(ca_cert_pem, ca_key_pem, "agent")
    cert = x509.load_pem_x509_certificate(client_cert_pem)
    bc = cert.extensions.get_extension_for_class(x509.BasicConstraints)
    assert bc.value.ca is False
