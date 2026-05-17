"""CENTINELA core type models — platform-wide data structures."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Session(BaseModel, frozen=True):
    """Represents a scoring session lifecycle."""

    id: UUID = Field(default_factory=uuid4)
    state: str = Field(default="CREATED")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    config: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContainerConfig(BaseModel, frozen=True):
    """Configuration for a single container in a pod."""

    name: str
    image: str
    command: list[str] | None = None
    env_vars: dict[str, str] = Field(default_factory=dict)
    resources: dict[str, Any] = Field(default_factory=dict)
    security_context: dict[str, Any] = Field(default_factory=dict)


class PodSpec(BaseModel, frozen=True):
    """Specification for a Kubernetes pod."""

    name: str
    namespace: str = "default"
    containers: list[ContainerConfig] = Field(min_length=1)
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)


class SecretRef(BaseModel, frozen=True):
    """Reference to a cryptographic secret."""

    name: str
    path: str | None = None  # tmpfs mount point
    encryption_key_id: str | None = None


class NetworkConfig(BaseModel, frozen=True):
    """Network interface configuration."""

    interface_name: str
    allowed_peers: list[str] = Field(default_factory=list)
    endpoint: str | None = None
    peer_public_key: str | None = None


class ResourceQuota(BaseModel, frozen=True):
    """Resource limits for a pod or container."""

    cpu_limit: float | None = None
    memory_limit: int | None = None  # MB
    disk_limit: int | None = None  # MB
    network_bw_limit: int | None = None  # Mbps


class AuditRecord(BaseModel, frozen=True):
    """Audit log entry with hash chain."""

    entry_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    event_type: str
    actor: str | None = None
    resource: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    prev_hash: str | None = None


__all__ = [
    "AuditRecord",
    "ContainerConfig",
    "NetworkConfig",
    "PodSpec",
    "ResourceQuota",
    "SecretRef",
    "Session",
]
