"""Resource governance module for centinela."""

from prometheus_client import Counter, Gauge

from .governor import ResourceGovernor, ResourceQuotaSpec

resource_limit = Gauge(
    "centinela_resource_limit", "Configured resource limit", ["resource_type"]
)
resource_usage = Gauge(
    "centinela_resource_usage", "Current resource usage", ["resource_type"]
)
resource_violations = Counter(
    "centinela_resource_violations_total",
    "Total resource limit violations",
    ["resource_type"],
)

__all__ = [
    "ResourceGovernor",
    "ResourceQuotaSpec",
    "resource_limit",
    "resource_usage",
    "resource_violations",
]
