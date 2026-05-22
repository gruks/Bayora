"""Tests for ABAC engine and SecureSecretStore."""

from unittest.mock import MagicMock

import pytest

from centinela.secrets.abac import ABACEngine, AccessDeniedError
from centinela.secrets.abac_models import (
    ABACPolicy,
    ABACRule,
    Action,
    Effect,
    ResourceSpec,
    SubjectSpec,
)
from centinela.secrets.secure_store import SecureSecretStore


def make_policy(*rules: ABACRule) -> ABACPolicy:
    return ABACPolicy(rules=list(rules))


def allow_rule(
    rule_id: str,
    tenant_role: str,
    resource_pattern: str,
    actions: list[Action],
) -> ABACRule:
    return ABACRule(
        id=rule_id,
        effect=Effect.ALLOW,
        subjects=[SubjectSpec(tenant_role=tenant_role)],
        resources=[ResourceSpec(name=resource_pattern)],
        actions=actions,
    )


def deny_rule(
    rule_id: str,
    tenant_role: str,
    resource_pattern: str,
    actions: list[Action],
) -> ABACRule:
    return ABACRule(
        id=rule_id,
        effect=Effect.DENY,
        subjects=[SubjectSpec(tenant_role=tenant_role)],
        resources=[ResourceSpec(name=resource_pattern)],
        actions=actions,
    )


# --- ABACEngine tests ---

def test_allow_matching_rule():
    policy = make_policy(allow_rule("r1", "red-agent", "api_key", [Action.READ]))
    engine = ABACEngine(policy)
    assert engine.evaluate({"tenant_role": "red-agent"}, "api_key", Action.READ) is True


def test_deny_when_no_rule_matches():
    policy = make_policy(allow_rule("r1", "red-agent", "api_key", [Action.READ]))
    engine = ABACEngine(policy)
    # blue-agent has no rule — default deny
    assert engine.evaluate({"tenant_role": "blue-agent"}, "api_key", Action.READ) is False


def test_explicit_deny_rule_wins():
    policy = make_policy(
        deny_rule("deny-sandbox", "llm-sandbox", "*", [Action.WRITE]),
        allow_rule("allow-all-write", "llm-sandbox", "*", [Action.WRITE]),
    )
    engine = ABACEngine(policy)
    # deny rule comes first — should deny
    assert engine.evaluate({"tenant_role": "llm-sandbox"}, "any_key", Action.WRITE) is False


def test_wildcard_resource_pattern():
    policy = make_policy(allow_rule("r1", "orchestrator", "api_*", [Action.READ]))
    engine = ABACEngine(policy)
    assert engine.evaluate({"tenant_role": "orchestrator"}, "api_key_prod", Action.READ) is True
    assert engine.evaluate({"tenant_role": "orchestrator"}, "db_password", Action.READ) is False


def test_action_mismatch_no_match():
    policy = make_policy(allow_rule("r1", "red-agent", "*", [Action.READ]))
    engine = ABACEngine(policy)
    assert engine.evaluate({"tenant_role": "red-agent"}, "key", Action.WRITE) is False


def test_multiple_subject_specs():
    rule = ABACRule(
        id="multi-subject",
        effect=Effect.ALLOW,
        subjects=[
            SubjectSpec(tenant_role="red-agent"),
            SubjectSpec(tenant_role="blue-agent"),
        ],
        resources=[ResourceSpec(name="shared_key")],
        actions=[Action.READ],
    )
    engine = ABACEngine(make_policy(rule))
    assert engine.evaluate({"tenant_role": "red-agent"}, "shared_key", Action.READ) is True
    assert engine.evaluate({"tenant_role": "blue-agent"}, "shared_key", Action.READ) is True
    assert engine.evaluate({"tenant_role": "orchestrator"}, "shared_key", Action.READ) is False


# --- SecureSecretStore tests ---

@pytest.fixture
def mock_store():
    store = MagicMock()
    store.get_secret.return_value = b"value"
    store.list_secrets.return_value = ["key1"]
    store.delete_secret.return_value = True
    return store


def test_secure_store_allows_read(mock_store):
    policy = make_policy(allow_rule("r1", "red-agent", "*", [Action.READ]))
    engine = ABACEngine(policy)
    secure = SecureSecretStore(mock_store, engine, {"tenant_role": "red-agent"})
    result = secure.get_secret("api_key")
    assert result == b"value"
    mock_store.get_secret.assert_called_once_with("api_key")


def test_secure_store_denies_read(mock_store):
    policy = make_policy(allow_rule("r1", "red-agent", "*", [Action.READ]))
    engine = ABACEngine(policy)
    secure = SecureSecretStore(mock_store, engine, {"tenant_role": "blue-agent"})
    with pytest.raises(AccessDeniedError):
        secure.get_secret("api_key")
    mock_store.get_secret.assert_not_called()


def test_secure_store_allows_write(mock_store):
    policy = make_policy(allow_rule("r1", "orchestrator", "*", [Action.WRITE]))
    engine = ABACEngine(policy)
    secure = SecureSecretStore(mock_store, engine, {"tenant_role": "orchestrator"})
    secure.set_secret("key", b"val")
    mock_store.set_secret.assert_called_once_with("key", b"val")


def test_secure_store_denies_delete(mock_store):
    policy = make_policy(allow_rule("r1", "orchestrator", "*", [Action.READ]))
    engine = ABACEngine(policy)
    secure = SecureSecretStore(mock_store, engine, {"tenant_role": "orchestrator"})
    with pytest.raises(AccessDeniedError):
        secure.delete_secret("key")


def test_secure_store_list_denied(mock_store):
    policy = make_policy(allow_rule("r1", "red-agent", "*", [Action.READ]))
    engine = ABACEngine(policy)
    secure = SecureSecretStore(mock_store, engine, {"tenant_role": "red-agent"})
    with pytest.raises(AccessDeniedError):
        secure.list_secrets()
