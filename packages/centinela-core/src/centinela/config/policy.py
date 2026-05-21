"""Declarative security policy models and resolution logic."""

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, Field

from centinela.config.models import PlatformConfig, ResourceLimits, SecurityConfig, substitute_env_vars_in_dict


class ResourceLimitsOverride(BaseModel, frozen=True):
    """Optional resource limits for overriding."""

    cpu_cores: float | None = Field(default=None, ge=0.1, le=32, description="CPU cores allocated")
    memory_mb: int | None = Field(default=None, ge=128, le=65536, description="Memory in MB")
    timeout_seconds: int | None = Field(default=None, ge=1, le=3600, description="Timeout in seconds")
    disk_mb: int | None = Field(default=None, ge=0, le=65536, description="Disk space in MB")


class SecurityConfigOverride(BaseModel, frozen=True):
    """Optional security configuration for overriding."""

    enable_network_isolation: bool | None = None
    wireguard_enabled: bool | None = None
    gvisor_enabled: bool | None = None
    seccomp_profile: str | None = None


class SecurityPolicy(BaseModel, frozen=True):
    """A security policy with overrides and dependencies."""

    name: str = Field(..., description="Unique policy name")
    description: str | None = Field(default=None, description="Policy description")
    extends: str | None = Field(default=None, description="Parent policy name to inherit from")
    resources: ResourceLimitsOverride = Field(default_factory=ResourceLimitsOverride)
    security: SecurityConfigOverride = Field(default_factory=SecurityConfigOverride)
    dependencies: list[str] = Field(default_factory=list, description="Other policies this depends on")


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected in policies."""
    pass


def detect_cycles(graph: dict[str, list[str]]) -> None:
    """Detect circular references in a directed graph.

    Args:
        graph: Adjacency list representation of the graph.

    Raises:
        CircularDependencyError: If a cycle is detected.
    """
    visited: set[str] = set()
    stack: set[str] = set()
    path: list[str] = []

    def dfs(node: str) -> None:
        if node in stack:
            cycle_path = path[path.index(node):] + [node]
            raise CircularDependencyError(f"Circular dependency detected: {' -> '.join(cycle_path)}")
        if node in visited:
            return

        visited.add(node)
        stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            dfs(neighbor)

        stack.remove(node)
        path.pop()

    for node in list(graph.keys()):
        if node not in visited:
            dfs(node)


class PolicyRegistry:
    """Registry for managing and resolving security policies."""

    def __init__(self) -> None:
        self.policies: dict[str, SecurityPolicy] = {}

    def register(self, policy: SecurityPolicy) -> None:
        """Register a new policy.

        Args:
            policy: The SecurityPolicy to register.
        """
        self.policies[policy.name] = policy

    def _check_cycles(self) -> None:
        """Check for cycles in extends and dependencies graphs."""
        extends_graph: dict[str, list[str]] = {
            name: [p.extends] if p.extends else []
            for name, p in self.policies.items()
        }
        detect_cycles(extends_graph)

        deps_graph: dict[str, list[str]] = {
            name: p.dependencies
            for name, p in self.policies.items()
        }
        detect_cycles(deps_graph)

    def resolve(self, name: str) -> PlatformConfig:
        """Resolve a policy by name, merging with its parents.

        Args:
            name: Policy name to resolve.

        Returns:
            Resolved PlatformConfig.

        Raises:
            ValueError: If policy or a parent is not found.
            CircularDependencyError: If inheritance has a cycle.
        """
        self._check_cycles()

        if name not in self.policies:
            raise ValueError(f"Policy '{name}' not found in registry")

        chain: list[SecurityPolicy] = []
        curr: str | None = name
        while curr:
            policy = self.policies[curr]
            chain.append(policy)
            curr = policy.extends
            if not curr:
                break
            if curr not in self.policies:
                raise ValueError(f"Parent policy '{curr}' not found in registry")

        # Start from base ancestor
        chain.reverse()

        # Defaults matching PlatformConfig and ResourceLimits defaults/minimums
        # (Though we'll rely on PlatformConfig to enforce them fully)
        merged_res: dict[str, Any] = {"cpu_cores": 1.0, "memory_mb": 512, "timeout_seconds": 300}
        merged_sec: dict[str, Any] = {
            "enable_network_isolation": True,
            "wireguard_enabled": False,
            "gvisor_enabled": False,
            "seccomp_profile": "RuntimeDefault"
        }

        for p in chain:
            res_dump = p.resources.model_dump(exclude_unset=True, exclude_none=True)
            merged_res.update(res_dump)

            sec_dump = p.security.model_dump(exclude_unset=True, exclude_none=True)
            merged_sec.update(sec_dump)

        resources = ResourceLimits(**merged_res)
        security = SecurityConfig(**merged_sec)

        return PlatformConfig(
            namespace=name,
            resources=resources,
            security=security,
            audit_enabled=True,
        )


class PolicyParser:
    """Parser for loading SecurityPolicy from dict/json/yaml."""

    @staticmethod
    def parse_dict(data: dict[str, Any]) -> SecurityPolicy:
        """Parse dictionary into SecurityPolicy with env var substitution."""
        processed = substitute_env_vars_in_dict(data)
        return SecurityPolicy.model_validate(processed)

    @staticmethod
    def parse_json(json_str: str) -> SecurityPolicy:
        """Parse JSON string into SecurityPolicy."""
        return PolicyParser.parse_dict(json.loads(json_str))

    @staticmethod
    def parse_yaml(yaml_str: str) -> SecurityPolicy:
        """Parse YAML string into SecurityPolicy."""
        data = yaml.safe_load(yaml_str)
        return PolicyParser.parse_dict(data or {})

    @staticmethod
    def load_file(path: str | Path) -> list[SecurityPolicy]:
        """Load policies from a JSON or YAML file."""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Policy file not found: {path}")

        policies: list[SecurityPolicy] = []
        with file_path.open(encoding="utf-8") as f:
            if file_path.suffix in (".yaml", ".yml"):
                docs = yaml.safe_load_all(f)
                for doc in docs:
                    if doc is None:
                        continue
                    if isinstance(doc, list):
                        policies.extend([PolicyParser.parse_dict(d) for d in doc])
                    else:
                        policies.append(PolicyParser.parse_dict(doc))
            else:
                data = json.load(f)
                if isinstance(data, list):
                    policies.extend([PolicyParser.parse_dict(d) for d in data])
                else:
                    policies.append(PolicyParser.parse_dict(data))

        return policies
