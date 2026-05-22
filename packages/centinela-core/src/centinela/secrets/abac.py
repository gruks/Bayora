"""ABAC engine for evaluating secret access policies."""

import fnmatch
from typing import Any

from .abac_models import ABACPolicy, ABACRule, Action, Effect, SubjectSpec


class AccessDeniedError(Exception):
    """Raised when ABAC policy denies access."""


class ABACEngine:
    """Evaluates ABAC policies to determine if access is granted.

    Rules are evaluated in order. First matching rule wins.
    Default effect when no rule matches is DENY (fail-closed).

    Args:
        policy: The ABACPolicy to enforce
    """

    def __init__(self, policy: ABACPolicy) -> None:
        self._policy = policy

    def evaluate(
        self,
        subject_attrs: dict[str, Any],
        resource_name: str,
        action: Action,
    ) -> bool:
        """Evaluate whether the subject can perform action on resource.

        Args:
            subject_attrs: Dict of subject attributes (e.g. {"tenant_role": "red-agent"})
            resource_name: Name of the secret being accessed
            action: The action being attempted

        Returns:
            True if access is granted, False if denied
        """
        for rule in self._policy.rules:
            if not self._action_matches(rule, action):
                continue
            if not self._resource_matches(rule, resource_name):
                continue
            if not self._subject_matches(rule, subject_attrs):
                continue
            # First matching rule wins
            return rule.effect == Effect.ALLOW

        # Default deny (fail-closed)
        return False

    def _action_matches(self, rule: ABACRule, action: Action) -> bool:
        return action in rule.actions

    def _resource_matches(self, rule: ABACRule, resource_name: str) -> bool:
        return any(
            fnmatch.fnmatch(resource_name, spec.name)
            for spec in rule.resources
        )

    def _subject_matches(self, rule: ABACRule, subject_attrs: dict[str, Any]) -> bool:
        """A rule matches if ANY of its subject specs match the caller."""
        return any(self._spec_matches(spec, subject_attrs) for spec in rule.subjects)

    def _spec_matches(self, spec: SubjectSpec, subject_attrs: dict[str, Any]) -> bool:
        """A spec matches if ALL non-None fields match the subject attributes."""
        if spec.tenant_role is not None and subject_attrs.get("tenant_role") != spec.tenant_role:
            return False
        if spec.tenant_id is not None and subject_attrs.get("tenant_id") != spec.tenant_id:
            return False
        return not (
            spec.environment is not None and subject_attrs.get("environment") != spec.environment
        )
