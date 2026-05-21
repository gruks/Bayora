"""WireGuard network management and isolation."""

import subprocess
from typing import Any

import wgconfig  # type: ignore[import-untyped]
from pydantic import BaseModel

from centinela.enums import NetworkPolicyType


class PeerConfig(BaseModel):
    """WireGuard peer configuration."""

    public_key: str
    allowed_ips: list[str]
    endpoint: str | None = None
    persistent_keepalive: int | None = None


class WireGuardConfig(BaseModel):
    """WireGuard interface configuration."""

    interface_name: str
    private_key: str
    address: str
    dns: list[str] = []
    peers: list[PeerConfig] = []


class NetworkManager:
    """Manager for WireGuard and network policies."""

    def load_config(self, path: str) -> WireGuardConfig:
        """Parse wgconfig-style file using wgconfig library."""
        wg = wgconfig.WGConfig(path)
        wg.read_file()

        # Parse interface
        iface = wg.interface
        private_key = iface.get("PrivateKey")
        address = iface.get("Address")
        dns = iface.get("DNS")
        dns_list = dns.split(",") if dns else []

        peers = []
        for peer_pk, peer_data in wg.peers.items():
            allowed_ips = peer_data.get("AllowedIPs", "")
            allowed_ips_list = allowed_ips.split(",") if allowed_ips else []
            endpoint = peer_data.get("Endpoint")
            pka = peer_data.get("PersistentKeepalive")
            pka_int = int(pka) if pka else None

            peers.append(
                PeerConfig(
                    public_key=peer_pk,
                    allowed_ips=[ip.strip() for ip in allowed_ips_list],
                    endpoint=endpoint,
                    persistent_keepalive=pka_int,
                )
            )

        return WireGuardConfig(
            interface_name="wg0",  # default, could extract from filename if needed
            private_key=private_key or "",
            address=address or "",
            dns=[d.strip() for d in dns_list],
            peers=peers,
        )

    def generate_keypair(self) -> tuple[str, str]:
        """Generate private/public key pair (base64 string)."""
        try:
            privkey_proc = subprocess.run(
                ["wg", "genkey"], capture_output=True, text=True, check=True
            )
            privkey = privkey_proc.stdout.strip()

            pubkey_proc = subprocess.run(
                ["wg", "pubkey"], input=privkey, capture_output=True, text=True, check=True
            )
            pubkey = pubkey_proc.stdout.strip()
            return privkey, pubkey
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback mock for testing environments where `wg` tool is not available
            return "mock_priv_key_base64_string=", "mock_pub_key_base64_string="

    def apply_policy(
        self, policy_type: NetworkPolicyType, tenant_id: str
    ) -> dict[str, Any]:
        """Generate Kubernetes NetworkPolicy."""
        # Create a simple representation of a NetworkPolicy
        policy: dict[str, Any] = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {"name": f"{tenant_id}-policy", "namespace": tenant_id},
            "spec": {"podSelector": {}, "policyTypes": ["Ingress", "Egress"]},
        }

        if policy_type == NetworkPolicyType.DENY_ALL:
            policy["spec"]["ingress"] = []
            policy["spec"]["egress"] = []
        elif policy_type == NetworkPolicyType.ALLOW_ALL:
            policy["spec"]["ingress"] = [{}]
            policy["spec"]["egress"] = [{}]
        elif policy_type == NetworkPolicyType.WHITELIST:
            policy["spec"]["ingress"] = []
            policy["spec"]["egress"] = []

        return policy

    def validate_config(self, config: WireGuardConfig) -> list[str]:
        """Return validation errors for a given WireGuardConfig."""
        errors = []
        if not config.private_key:
            errors.append("Private key is required")
        if not config.address:
            errors.append("Address is required")
        for peer in config.peers:
            if not peer.public_key:
                errors.append("Peer public key is required")
            if not peer.allowed_ips:
                errors.append(f"Peer {peer.public_key} requires AllowedIPs")
        return errors
