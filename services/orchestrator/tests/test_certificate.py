import pytest
import tempfile
from pathlib import Path

from services.orchestrator.src.orchestrator.certificate import CertificateGenerator, CertificateData


class TestCertificateGenerator:
    def test_generates_key_pair(self):
        gen = CertificateGenerator()
        pubkey_hex = gen.get_public_key_hex()
        assert len(pubkey_hex) == 64  # Ed25519 public key is 32 bytes = 64 hex chars

    def test_signs_certificate_data(self):
        gen = CertificateGenerator()
        data = CertificateData(
            model_info="gpt-4",
            test_date="2026-05-16",
            session_id="session-123",
            vuln_count=5,
            mutation_rounds=100,
            merkle_root="abc123",
            public_key_hex=gen.get_public_key_hex(),
        )
        signature = gen.sign_certificate_data(data)
        assert len(signature) == 64  # Ed25519 signature is 64 bytes

    def test_generate_pdf_creates_file(self):
        gen = CertificateGenerator()
        data = CertificateData(
            model_info="gpt-4",
            test_date="2026-05-16 12:00:00 UTC",
            session_id="session-123",
            vuln_count=5,
            mutation_rounds=100,
            merkle_root="a" * 64,
            public_key_hex="b" * 64,
        )
        signature = bytes(64)  # mock signature

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            output_path = f.name

        try:
            gen.generate_pdf(data, signature, output_path)
            assert Path(output_path).exists()
            assert Path(output_path).stat().st_size > 0
        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_payload_format(self):
        gen = CertificateGenerator()
        data = CertificateData(
            model_info="gpt-4",
            test_date="2026-05-16",
            session_id="session-123",
            vuln_count=5,
            mutation_rounds=100,
            merkle_root="abc123",
            public_key_hex="def456",
        )
        payload = gen._create_payload(data)
        assert "gpt-4" in payload
        assert "session-123" in payload
        assert "5" in payload
        assert "100" in payload
        assert "abc123" in payload
