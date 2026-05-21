# Phase 7: Configuration Parser and Validator - Research

**Researched:** 2026-05-20
**Domain:** Declarative security policy management, YAML/JSON parsing, schema validation, circular dependency detection, pretty-printing
**Confidence:** HIGH

## Summary

This phase implements declarative security policy management for the CENTINELA platform. The goal is to provide a robust configuration parsing and validation engine that reads security policies from YAML/JSON files, validates their schemas, enforces strict resource limit boundaries (CPU 0.1–32 cores, Memory 128MB–64GB), detects circular dependencies in policy inheritance (`extends`) and service dependencies (`dependencies`), pretty-prints the resolved configuration, and supports environment variable substitution.

**Primary recommendations:**
1. Use Pydantic v2 `BaseModel` to define `SecurityPolicy`, extending the existing configuration models (`ResourceLimits`, `SecurityConfig`).
2. Support partial specification of resource limits and security configurations in sub-policies, and recursively merge them with their parent policies (`extends`) to get the fully resolved configuration.
3. Perform circular dependency detection using a Depth-First Search (DFS) graph traversal algorithm to identify cycles in both the inheritance chain (`extends`) and service dependencies (`dependencies`) before resolving policies.
4. Implement a comprehensive recursive environment variable substitution function that handles `${VAR}` and `${VAR:-default}` patterns inside string values, including nested dictionaries and lists.
5. Create a standalone CLI tool `centinela-policy` registered as an entry point in `packages/centinela-core/pyproject.toml` to parse, validate, resolve, and pretty-print policies.

---

## Standard Stack

### Schema Validation & Parsing

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **pydantic** | >=2.0 | Schema validation and serialization | Already a core dependency, highly performant, handles coercion and validation seamlessly |
| **pyyaml** | >=6.0 | YAML file parsing | Standard Python YAML parser, safe loading out-of-the-box |
| **json** | Built-in | JSON string/file parsing | Standard library, robust and fast |

### Dependency Graph Analysis

Since we want to keep the core library dependencies minimal and prevent bloated installation sizes, we will use a **hand-rolled DFS cycle detection algorithm** rather than importing heavy graph libraries like NetworkX. This approach is highly efficient for policy graphs and matches the design decision in Phase 5 Plan 4 (which used simple dictionary-based adjacency lists to keep overhead low).

---

## Architecture Patterns

### Recommended Folder & Package Structure

We will place all configuration and policy code within the existing `centinela.config` sub-package:

```
packages/centinela-core/src/centinela/config/
├── __init__.py         # Exports ConfigLoader, load_config, SecurityPolicy, PolicyParser, PolicyRegistry
├── models.py           # Existing PlatformConfig, ResourceLimits, SecurityConfig
├── policy.py           # NEW: SecurityPolicy, PolicyRegistry, PolicyParser, and cycle detection
└── cli.py              # NEW: centinela-policy CLI commands and pretty-printer
```

### 1. Declarative Security Policy Schema

We define a `SecurityPolicy` model that allows partial overrides and links to a parent policy via `extends`.

```python
from typing import Any
from pydantic import BaseModel, Field

class ResourceLimitsOverride(BaseModel, frozen=True):
    """Optional resource limits override (allowing partial specs)."""
    cpu_cores: float | None = Field(default=None, ge=0.1, le=32, description="CPU cores override")
    memory_mb: int | None = Field(default=None, ge=128, le=65536, description="Memory in MB override")
    timeout_seconds: int | None = Field(default=None, ge=1, le=3600, description="Timeout override")
    disk_mb: int | None = Field(default=None, ge=0, le=65536, description="Disk space override")

class SecurityConfigOverride(BaseModel, frozen=True):
    """Optional security config overrides."""
    enable_network_isolation: bool | None = Field(default=None)
    wireguard_enabled: bool | None = Field(default=None)
    gvisor_enabled: bool | None = Field(default=None)
    seccomp_profile: str | None = Field(default=None)

class SecurityPolicy(BaseModel, frozen=True):
    """Declarative security policy containing resource and security rules."""
    name: str = Field(min_length=1, description="Unique policy identifier")
    description: str | None = Field(default=None, description="Policy description")
    extends: str | None = Field(default=None, description="Parent policy name to inherit from")
    resources: ResourceLimitsOverride | None = Field(default=None, description="Resource limits")
    security: SecurityConfigOverride | None = Field(default=None, description="Security settings")
    dependencies: list[str] = Field(default_factory=list, description="Services or policies this policy depends on")
```

### 2. Graph Cycle Detection Pattern

To detect circular dependencies in both `extends` (policy inheritance) and `dependencies` (service dependency graph), we construct a directed graph and run a DFS cycle detector.

```python
class CircularDependencyError(ValueError):
    """Raised when a cycle is detected in the policy or dependency graph."""
    pass

def detect_cycles(graph: dict[str, list[str]]) -> None:
    """Detect cycles in a directed graph using DFS.
    
    Args:
        graph: Adjacency list mapping node name to list of outgoing neighbor nodes.
        
    Raises:
        CircularDependencyError: If a cycle is detected, showing the cyclic path.
    """
    visited: set[str] = set()
    rec_stack: set[str] = set()
    path: list[str] = []

    def dfs(node: str) -> bool:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                cycle_start_idx = path.index(neighbor)
                cycle_path = " -> ".join(path[cycle_start_idx:] + [neighbor])
                raise CircularDependencyError(f"Circular dependency detected: {cycle_path}")

        path.pop()
        rec_stack.remove(node)
        return False

    for node in graph:
        if node not in visited:
            dfs(node)
```

### 3. Policy Merging & Resolution

When a policy extends another, it should inherit all values from its parent and apply its own overrides. We do this recursively:

```python
def merge_configs(parent: dict[str, Any], child: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge two dictionaries, overriding parent values with child values."""
    merged = parent.copy()
    for key, val in child.items():
        if val is None:
            continue
        if isinstance(val, dict) and key in merged and isinstance(merged[key], dict):
            merged[key] = merge_configs(merged[key], val)
        else:
            merged[key] = val
    return merged
```

---

## Anti-Patterns to Avoid

- **Resolving inheritance before checking for cycles:** This leads to `RecursionError` and application crashes. Always run cycle detection on the inheritance graph first!
- **Using a generic graph library (e.g. NetworkX):** NetworkX has heavy transitive dependencies. Building a lightweight, standard DFS in 30 lines of pure Python keeps `centinela-core` fast and lean.
- **Applying env var substitution after schema validation:** If environment variables contain integers or booleans, applying env var substitution after schema validation will either fail to validate or leave raw `${VAR}` placeholders in string fields. Env var substitution must happen at the dictionary stage before Pydantic models are validated.

---

## Don't Hand-Roll

- **JSON/YAML parsing:** Use PyYAML (`yaml.safe_load`) and standard library `json.loads`. Do not attempt to parse these configuration formats using manual string slicing or regexes.
- **Constraint validation:** Use Pydantic's `Field(ge=..., le=...)` and custom validators where appropriate to enforce resource limit boundaries (CPU 0.1-32 cores, Memory 128MB-64GB).

---

## Common Pitfalls

### Pitfall 1: Type Coercion during Merging
**What goes wrong:** A child override overrides a key with `None` or an invalid type.
**How to avoid:** Ensure that during dictionary merging, key-value pairs with `None` in the child configuration are discarded so they do not wipe out valid parent configurations.

### Pitfall 2: Environment Variable Type Mismatch
**What goes wrong:** Substituting an environment variable like `CPU_CORES=${CORES:-1.5}` results in Pydantic validating the literal string `"1.5"` instead of the float `1.5`.
**How to avoid:** Pydantic natively coerces compatible types (e.g., numeric strings to floats/ints). However, we must ensure our env var substitution outputs clean string representations that Pydantic can successfully coerce.

---

## Code Examples

### CLI Command Design

The CLI command `centinela-policy` should support:
- `validate <path>`: Validates one or more policy files.
- `resolve <path> --policy <name>`: Resolves a specific policy with inheritance and outputs the final pretty-printed YAML/JSON.
- `graph <path>`: Prints the inheritance and dependency tree of the policies in a structured format.

```python
import argparse
import sys

def main() -> None:
    parser = argparse.ArgumentParser(description="CENTINELA Security Policy Parser and Validator")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    validate_parser = subparsers.add_parser("validate", help="Validate policy files")
    validate_parser.add_argument("path", help="Path to policy YAML or JSON file")
    
    resolve_parser = subparsers.add_parser("resolve", help="Resolve a specific policy inheritance")
    resolve_parser.add_argument("path", help="Path to policy file")
    resolve_parser.add_argument("--policy", required=True, help="Name of policy to resolve")
    resolve_parser.add_argument("--format", choices=["yaml", "json"], default="yaml", help="Output format")
    
    args = parser.parse_args()
    # Execute commands...
```

---

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH - PyYAML and Pydantic are standard and already present in the workspace
- Architecture Patterns: HIGH - DFS is robust, dictionary merging is standard
- CLI and Pretty Printing: HIGH - argparse and standard terminal formatting are safe and highly portable

**Research date:** 2026-05-20
**Valid until:** 2026-06-20
