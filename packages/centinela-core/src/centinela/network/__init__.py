"""Network management module for centinela."""

from typing import Any

from centinela.enums import NetworkPolicyType

from .manager import NetworkManager, PeerConfig, WireGuardConfig


class NetworkPolicyGenerator:
    """Helper to generate Kubernetes NetworkPolicy artifacts."""

    @staticmethod
    def generate(policy_type: NetworkPolicyType, tenant_id: str) -> dict[str, Any]:
        """Adapter for manager's apply_policy."""
        manager = NetworkManager()
        return manager.apply_policy(policy_type, tenant_id)


__all__ = [
    "NetworkManager",
    "NetworkPolicyGenerator",
    "PeerConfig",
    "WireGuardConfig",
]
