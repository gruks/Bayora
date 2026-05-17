"""Configuration models with validation for platform security policies."""

import os
import re
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ResourceLimits(BaseModel, frozen=True):
    """Resource limits for a container or pod.

    Enforces constraints:
    - cpu_cores: 0.1 to 32 cores
    - memory_mb: 128 to 65536 MB
    - timeout_seconds: 1 to 3600 seconds
    - disk_mb: optional, 0 to 65536 MB
    """

    cpu_cores: float = Field(ge=0.1, le=32, description="CPU cores allocated")
    memory_mb: int = Field(ge=128, le=65536, description="Memory in MB")
    timeout_seconds: int = Field(ge=1, le=3600, default=300, description="Timeout in seconds")
    disk_mb: int | None = Field(default=None, ge=0, le=65536, description="Disk space in MB")

    @field_validator("cpu_cores")
    @classmethod
    def validate_cpu(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("cpu_cores must be >= 0.1")
        return v


class SecurityConfig(BaseModel, frozen=True):
    """Security configuration for platform resources.

    Controls isolation, encryption, and sandboxing options.
    """

    enable_network_isolation: bool = Field(default=True, description="Enable network segmentation")
    wireguard_enabled: bool = Field(default=False, description="Enable WireGuard VPN")
    gvisor_enabled: bool = Field(default=False, description="Enable gVisor sandboxing")
    seccomp_profile: str = Field(default="RuntimeDefault", description="Seccomp profile name")


class PlatformConfig(BaseModel, frozen=True):
    """Platform configuration combining resources, security, and audit settings.

    This is the main configuration model used throughout the platform.
    Supports env var substitution in string values:
    - ${VAR} - substitute with environment variable VAR
    - ${VAR:-default} - substitute with default if VAR not set

    Note: Env var substitution is handled by ConfigLoader before validation.
    """

    namespace: str = Field(default="default", description="Kubernetes namespace")
    resources: ResourceLimits = Field(description="Resource limits")
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    audit_enabled: bool = Field(default=True, description="Enable audit logging")


def _substitute_env_vars(value: str) -> str:
    """Substitute environment variables in a string value.

    Supports two patterns:
    - ${VAR} - substitute with environment variable VAR
    - ${VAR:-default} - substitute with default if VAR not set

    Args:
        value: String potentially containing env var references

    Returns:
        String with env vars substituted
    """
    if not isinstance(value, str):
        return value

    # Pattern: ${VAR} or ${VAR:-default}
    pattern = r"\$\{([^}:]+)(?::-([^}]*))?\}"

    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        default_value = match.group(2)
        return os.environ.get(var_name, default_value if default_value is not None else "")

    return re.sub(pattern, replacer, value)


def substitute_env_vars_in_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively substitute env vars in all string values of a dict.

    Args:
        data: Dictionary to process

    Returns:
        Dictionary with env vars substituted
    """
    result: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = _substitute_env_vars(value)
        elif isinstance(value, dict):
            result[key] = substitute_env_vars_in_dict(value)
        elif isinstance(value, list):
            result[key] = [
                _substitute_env_vars(item) if isinstance(item, str) else item for item in value
            ]
        else:
            result[key] = value
    return result


__all__ = ["PlatformConfig", "ResourceLimits", "SecurityConfig", "substitute_env_vars_in_dict"]
