"""Cgroup v2 resource governor."""

from pydantic import BaseModel, Field


class ResourceQuotaSpec(BaseModel):
    """Resource quota specification for a cgroup."""

    cpu_quota: int | None = None  # in microseconds for quota/period
    cpu_period: int = 100000  # default 100ms
    memory_high: int | None = None  # bytes
    memory_max: int | None = None  # bytes
    io_weight: int | None = Field(default=None, ge=1, le=10000)
    pids_max: int | None = None


class ResourceGovernor:
    """Enforces resource limits using cgroup v2."""

    def __init__(self, quota: ResourceQuotaSpec) -> None:
        self.quota = quota

    def generate_cgroup_spec(self) -> dict[str, str]:
        """Produce cgroup v2 settings dict."""
        spec = {}

        if self.quota.cpu_quota is not None:
            spec["cpu.max"] = f"{self.quota.cpu_quota} {self.quota.cpu_period}"

        if self.quota.memory_high is not None:
            spec["memory.high"] = str(self.quota.memory_high)

        if self.quota.memory_max is not None:
            spec["memory.max"] = str(self.quota.memory_max)

        if self.quota.io_weight is not None:
            spec["io.weight"] = str(self.quota.io_weight)

        if self.quota.pids_max is not None:
            spec["pids.max"] = str(self.quota.pids_max)

        return spec

    def validate_quota(self) -> list[str]:
        """Return validation errors."""
        errors = []
        if self.quota.cpu_quota is not None and self.quota.cpu_quota <= 0:
            errors.append("cpu_quota must be positive")
        if self.quota.cpu_period <= 0:
            errors.append("cpu_period must be positive")
        if self.quota.memory_max is not None and self.quota.memory_high is not None and self.quota.memory_high > self.quota.memory_max:
            errors.append("memory_high cannot exceed memory_max")
        return errors
