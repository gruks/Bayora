"""CLI for CENTINELA security policy management."""

import argparse
import sys
from pathlib import Path

from centinela.config.models import PlatformConfig
from centinela.config.policy import CircularDependencyError, PolicyParser, PolicyRegistry, SecurityPolicy


def pretty_print_policy(policy: SecurityPolicy, resolved_config: PlatformConfig) -> None:
    """Pretty-prints a policy and its resolved configuration.

    Args:
        policy: The raw SecurityPolicy.
        resolved_config: The resolved PlatformConfig.
    """
    print(f"Policy: {policy.name}")
    if policy.description:
        print(f"Description: {policy.description}")
    if policy.extends:
        print(f"Extends: {policy.extends}")
    if policy.dependencies:
        print(f"Dependencies: {', '.join(policy.dependencies)}")
    
    print("\nResolved Resource Limits:")
    print(f"  CPU Cores: {resolved_config.resources.cpu_cores}")
    print(f"  Memory: {resolved_config.resources.memory_mb} MB")
    print(f"  Timeout: {resolved_config.resources.timeout_seconds} s")
    if resolved_config.resources.disk_mb is not None:
        print(f"  Disk: {resolved_config.resources.disk_mb} MB")

    print("\nResolved Security Config:")
    print(f"  Network Isolation: {resolved_config.security.enable_network_isolation}")
    print(f"  Wireguard: {resolved_config.security.wireguard_enabled}")
    print(f"  gVisor: {resolved_config.security.gvisor_enabled}")
    print(f"  Seccomp Profile: {resolved_config.security.seccomp_profile}")


def main() -> None:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(description="CENTINELA Policy Management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # validate command
    val_parser = subparsers.add_parser(
        "validate", help="Validates schema and circular dependencies in all policies in a file"
    )
    val_parser.add_argument("path", type=str, help="Path to policy YAML/JSON file")

    # resolve command
    res_parser = subparsers.add_parser(
        "resolve", help="Resolves a policy and pretty-prints it"
    )
    res_parser.add_argument("path", type=str, help="Path to policy YAML/JSON file")
    res_parser.add_argument("--policy", type=str, required=True, help="Name of the policy to resolve")

    # graph command
    graph_parser = subparsers.add_parser(
        "graph", help="Prints the inheritance (extends) tree and dependencies graph"
    )
    graph_parser.add_argument("path", type=str, help="Path to policy YAML/JSON file")

    args = parser.parse_args()

    try:
        policies = PolicyParser.load_file(args.path)
    except Exception as e:
        print(f"Error loading policies: {e}", file=sys.stderr)
        sys.exit(1)

    registry = PolicyRegistry()
    for p in policies:
        registry.register(p)

    if args.command == "validate":
        try:
            registry._check_cycles()
            print(f"Successfully validated {len(policies)} policies.")
        except CircularDependencyError as e:
            print(f"Validation failed: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "resolve":
        try:
            resolved = registry.resolve(args.policy)
            policy = registry.policies[args.policy]
            pretty_print_policy(policy, resolved)
        except Exception as e:
            print(f"Error resolving policy: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "graph":
        print("Inheritance (extends) Tree:")
        has_extends = False
        for name, p in registry.policies.items():
            if p.extends:
                has_extends = True
                print(f"  {name} -> {p.extends}")
        if not has_extends:
            print("  No extends relationships defined.")

        print("\nDependencies Graph:")
        has_deps = False
        for name, p in registry.policies.items():
            if p.dependencies:
                has_deps = True
                print(f"  {name} -> {', '.join(p.dependencies)}")
        if not has_deps:
            print("  No dependencies defined.")


if __name__ == "__main__":
    main()
