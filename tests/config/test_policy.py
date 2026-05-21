import json
import textwrap

import pytest
from pydantic import ValidationError

from centinela.config.cli import main as cli_main
from centinela.config.policy import (
    CircularDependencyError,
    PolicyParser,
    PolicyRegistry,
    ResourceLimitsOverride,
    SecurityConfigOverride,
    SecurityPolicy,
)
from pydantic import ValidationError


def test_basic_schema_parsing_yaml():
    yaml_content = """
    name: test-policy
    description: A test policy
    resources:
      cpu_cores: 2.5
      memory_mb: 2048
    security:
      enable_network_isolation: false
    dependencies:
      - other-policy
    """
    policy = PolicyParser.parse_yaml(yaml_content)
    assert policy.name == "test-policy"
    assert policy.description == "A test policy"
    assert policy.resources.cpu_cores == 2.5
    assert policy.resources.memory_mb == 2048
    assert policy.security.enable_network_isolation is False
    assert policy.dependencies == ["other-policy"]


def test_basic_schema_parsing_json():
    json_content = json.dumps({
        "name": "test-json",
        "extends": "base-policy",
        "resources": {
            "timeout_seconds": 600
        }
    })
    policy = PolicyParser.parse_json(json_content)
    assert policy.name == "test-json"
    assert policy.extends == "base-policy"
    assert policy.resources.timeout_seconds == 600
    assert policy.resources.cpu_cores is None


def test_env_var_substitution(monkeypatch):
    monkeypatch.setenv("TEST_CPU", "4.0")
    monkeypatch.setenv("TEST_MEM", "4096")

    yaml_content = """
    name: env-policy
    resources:
      cpu_cores: ${TEST_CPU}
      memory_mb: ${TEST_MEM}
      timeout_seconds: ${UNSET_VAR:-120}
    """
    policy = PolicyParser.parse_yaml(yaml_content)
    assert policy.name == "env-policy"
    assert policy.resources.cpu_cores == 4.0
    assert policy.resources.memory_mb == 4096
    assert policy.resources.timeout_seconds == 120


def test_circular_dependency_extends():
    registry = PolicyRegistry()
    registry.register(SecurityPolicy(name="a", extends="b"))
    registry.register(SecurityPolicy(name="b", extends="c"))
    registry.register(SecurityPolicy(name="c", extends="a"))

    with pytest.raises(CircularDependencyError, match="Circular dependency detected: a -> b -> c -> a"):
        registry.resolve("a")


def test_circular_dependency_dependencies():
    registry = PolicyRegistry()
    registry.register(SecurityPolicy(name="p1", dependencies=["p2"]))
    registry.register(SecurityPolicy(name="p2", dependencies=["p3"]))
    registry.register(SecurityPolicy(name="p3", dependencies=["p1"]))

    with pytest.raises(CircularDependencyError, match="Circular dependency detected: p1 -> p2 -> p3 -> p1"):
        registry.resolve("p1")


def test_multi_level_extends_merging():
    registry = PolicyRegistry()
    registry.register(SecurityPolicy(
        name="base",
        resources=ResourceLimitsOverride(cpu_cores=1.0, memory_mb=1024, disk_mb=5000),
        security=SecurityConfigOverride(enable_network_isolation=True, seccomp_profile="RuntimeDefault")
    ))
    registry.register(SecurityPolicy(
        name="mid",
        extends="base",
        resources=ResourceLimitsOverride(cpu_cores=2.0),
        security=SecurityConfigOverride(gvisor_enabled=True)
    ))
    registry.register(SecurityPolicy(
        name="leaf",
        extends="mid",
        resources=ResourceLimitsOverride(memory_mb=2048, timeout_seconds=600),
        security=SecurityConfigOverride(enable_network_isolation=False)
    ))

    resolved = registry.resolve("leaf")

    assert resolved.resources.cpu_cores == 2.0
    assert resolved.resources.memory_mb == 2048
    assert resolved.resources.disk_mb == 5000
    assert resolved.resources.timeout_seconds == 600

    assert resolved.security.enable_network_isolation is False
    assert resolved.security.gvisor_enabled is True
    assert resolved.security.seccomp_profile == "RuntimeDefault"


def test_enforcing_resource_limits():
    registry = PolicyRegistry()

    # All should fail validation either in parser or models
    with pytest.raises(ValidationError):
        PolicyParser.parse_dict({"name": "fail1", "resources": {"cpu_cores": 100.0}})

    with pytest.raises(ValidationError):
        PolicyParser.parse_dict({"name": "fail2", "resources": {"cpu_cores": 0.0}})
        
    with pytest.raises(ValidationError):
        PolicyParser.parse_dict({"name": "fail3", "resources": {"memory_mb": 100000}})

    with pytest.raises(ValidationError):
        PolicyParser.parse_dict({"name": "fail4", "resources": {"memory_mb": 64}})


def test_cli_validate(tmp_path, monkeypatch, capsys):
    policy_file = tmp_path / "policies.yaml"
    policy_file.write_text(textwrap.dedent("""
    name: valid1
    extends: valid2
    ---
    name: valid2
    """))
    monkeypatch.setattr("sys.argv", ["centinela-policy", "validate", str(policy_file)])
    cli_main()
    captured = capsys.readouterr()
    assert "Successfully validated 2 policies." in captured.out


def test_cli_resolve(tmp_path, monkeypatch, capsys):
    policy_file = tmp_path / "policies.yaml"
    policy_file.write_text(textwrap.dedent("""
    name: target
    description: Resolvable
    resources:
      cpu_cores: 4.0
    """))
    monkeypatch.setattr("sys.argv", ["centinela-policy", "resolve", str(policy_file), "--policy", "target"])
    cli_main()
    captured = capsys.readouterr()
    assert "Policy: target" in captured.out
    assert "Description: Resolvable" in captured.out
    assert "CPU Cores: 4.0" in captured.out


def test_cli_graph(tmp_path, monkeypatch, capsys):
    policy_file = tmp_path / "policies.yaml"
    policy_file.write_text(textwrap.dedent("""
    name: child
    extends: parent
    dependencies:
      - other
    ---
    name: parent
    ---
    name: other
    """))
    monkeypatch.setattr("sys.argv", ["centinela-policy", "graph", str(policy_file)])
    cli_main()
    captured = capsys.readouterr()
    assert "child -> parent" in captured.out
    assert "child -> other" in captured.out
