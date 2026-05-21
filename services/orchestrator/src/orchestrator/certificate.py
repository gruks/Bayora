"""Certificate generation with Ed25519 signing."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch


@dataclass
class CertificateData:
    """Data for certificate generation."""

    model_info: str
    test_date: str
    session_id: str
    vuln_count: int
    mutation_rounds: int
    merkle_root: str
    public_key_hex: str


class CertificateGenerator:
    """Generates signed PDF safety certificates."""

    def __init__(self):
        # Generate session key pair per session (CERT-08)
        self._private_key = Ed25519PrivateKey.generate()
        self._public_key = self._private_key.public_key()

    def get_public_key_hex(self) -> str:
        """Get public key as hex for inclusion in certificate."""
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        ).hex()

    def sign_certificate_data(self, data: CertificateData) -> bytes:
        """Sign certificate payload with Ed25519 (CERT-08)."""
        # Create canonical payload string
        payload = self._create_payload(data)
        return self._private_key.sign(payload.encode())

    def _create_payload(self, data: CertificateData) -> str:
        """Create canonical string for signing."""
        return f"{data.model_info}|{data.test_date}|{data.session_id}|{data.vuln_count}|{data.mutation_rounds}|{data.merkle_root}"

    def generate_pdf(self, data: CertificateData, signature: bytes, output_path: str) -> None:
        """Generate PDF certificate with all required fields."""
        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter

        # Title (CERT-01)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(1 * inch, height - 1.5 * inch, "Safety Certificate")

        # Subtitle
        c.setFont("Helvetica", 12)
        c.drawString(1 * inch, height - 2 * inch, "AI Safety Validation Report")

        y = height - 3 * inch

        # Model under test (CERT-02)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, y, "Model Under Test:")
        c.setFont("Helvetica", 11)
        c.drawString(2.5 * inch, y, data.model_info)
        y -= 0.4 * inch

        # Test date (CERT-03)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, y, "Test Date:")
        c.setFont("Helvetica", 11)
        c.drawString(2.5 * inch, y, data.test_date)
        y -= 0.4 * inch

        # Session ID (CERT-03)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, y, "Session ID:")
        c.setFont("Helvetica", 11)
        c.drawString(2.5 * inch, y, data.session_id)
        y -= 0.6 * inch

        # Attack breakdown (CERT-04)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1 * inch, y, "Attack Results")
        y -= 0.4 * inch

        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, y, "Vulnerabilities Found:")
        c.setFont("Helvetica", 11)
        c.drawString(2.5 * inch, y, str(data.vuln_count))
        y -= 0.35 * inch

        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, y, "Mutation Rounds:")
        c.setFont("Helvetica", 11)
        c.drawString(2.5 * inch, y, str(data.mutation_rounds))
        y -= 0.6 * inch

        # Merkle root (CERT-07)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1 * inch, y, "Cryptographic Verification")
        y -= 0.4 * inch

        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, y, "Merkle Root Hash:")
        c.setFont("Helvetica", 10)
        # Split long hash into multiple lines
        hash_lines = [data.merkle_root[i : i + 60] for i in range(0, len(data.merkle_root), 60)]
        for line in hash_lines:
            c.drawString(2.5 * inch, y, line)
            y -= 0.25 * inch
        y -= 0.2 * inch

        # Ed25519 signature (CERT-06, CERT-08)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, y, "Ed25519 Signature:")
        c.setFont("Helvetica", 9)
        sig_hex = signature.hex()
        sig_lines = [sig_hex[i : i + 60] for i in range(0, len(sig_hex), 60)]
        for line in sig_lines:
            c.drawString(2.5 * inch, y, line)
            y -= 0.2 * inch
        y -= 0.4 * inch

        # Public key (CERT-08)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, y, "Session Public Key (hex):")
        c.setFont("Helvetica", 9)
        key_lines = [
            data.public_key_hex[i : i + 60] for i in range(0, len(data.public_key_hex), 60)
        ]
        for line in key_lines:
            c.drawString(2.5 * inch, y, line)
            y -= 0.2 * inch
        y -= 0.5 * inch

        # Verification command (CERT-09)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1 * inch, y, "Verification")
        y -= 0.4 * inch

        c.setFont("Helvetica-Oblique", 10)
        c.drawString(1 * inch, y, "To verify this certificate, run:")
        y -= 0.3 * inch

        c.setFont("Courier", 9)
        c.drawString(1.2 * inch, y, f"python -m orchestrator.verify_cert \\")
        y -= 0.25 * inch
        c.drawString(1.2 * inch, y, f"  --cert {Path(output_path).name} \\")
        y -= 0.25 * inch
        c.drawString(1.2 * inch, y, f"  --pubkey {data.public_key_hex[:32]}...")

        c.save()

    def generate(
        self,
        model_info: str,
        session_id: str,
        vuln_count: int,
        mutation_rounds: int,
        audit_client,  # AuditClient instance
        output_path: str,
    ) -> str:
        """Generate complete certificate (CERT-01, CERT-05)."""
        # Get Merkle root from audit chain (CERT-07)
        merkle_root = audit_client.get_merkle_root(session_id)

        # Create certificate data
        data = CertificateData(
            model_info=model_info,
            test_date=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            session_id=session_id,
            vuln_count=vuln_count,
            mutation_rounds=mutation_rounds,
            merkle_root=merkle_root,
            public_key_hex=self.get_public_key_hex(),
        )

        # Sign certificate data (CERT-08)
        signature = self.sign_certificate_data(data)

        # Generate PDF (CERT-01)
        self.generate_pdf(data, signature, output_path)

        return output_path
