"""CENTINELA core enums — platform-wide enumerated types."""

from enum import StrEnum


class SessionState(StrEnum):
    """Lifecycle state of a scoring session."""

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"
    FAILED = "FAILED"


class EventType(StrEnum):
    """Events tracked in the audit log."""

    SESSION_START = "SESSION_START"
    SESSION_END = "SESSION_END"
    PROMPT_SUBMITTED = "PROMPT_SUBMITTED"
    RESPONSE_RECEIVED = "RESPONSE_RECEIVED"
    CONTAINER_START = "CONTAINER_START"
    CONTAINER_STOP = "CONTAINER_STOP"
    SECRET_ROTATE = "SECRET_ROTATE"
    CONFIG_CHANGE = "CONFIG_CHANGE"


class ResourceUnit(StrEnum):
    """Units for resource quota specification."""

    CPU_CORES = "CPU_CORES"
    MEMORY_MB = "MEMORY_MB"
    DISK_MB = "DISK_MB"
    NETWORK_BW_MBPS = "NETWORK_BW_MBPS"


class SecurityLevel(StrEnum):
    """Security posture levels for platform resources."""

    STANDARD = "STANDARD"
    ENHANCED = "ENHANCED"
    RESTRICTED = "RESTRICTED"


class NetworkPolicyType(StrEnum):
    """Network isolation policy types."""

    ALLOW_ALL = "ALLOW_ALL"
    DENY_ALL = "DENY_ALL"
    WHITELIST = "WHITELIST"


class AuditAction(StrEnum):
    """Actions recorded in the audit log."""

    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    EXECUTE = "EXECUTE"


__all__ = [
    "AuditAction",
    "EventType",
    "NetworkPolicyType",
    "ResourceUnit",
    "SecurityLevel",
    "SessionState",
]
