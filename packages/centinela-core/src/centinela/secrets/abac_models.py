"""Pydantic models for ABAC (Attribute-Based Access Control) policies.

Defines a YAML-serializable DSL for controlling which subjects can
perform which actions on which secret resources.

Example policy YAML:
    rules:
      - id: allow-red-agent-read
        effect: allow
        subjects:
          - tenant_role: red-agent
        resources:
          - name: "api_key*"
        actions:
          - read
      - id: deny-sandbox-write
        effect: deny
        subjects:
          - tenant_role: llm-sandbox
        resources:
          - name: "*"
        actions:
          - write
          - delete
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class Effect(StrEnum):
    ALLOW = "allow"
    DENY = "deny"


class Action(StrEnum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    LIST = "list"


class SubjectSpec(BaseModel, frozen=True):
    """Attributes that identify a subject (caller/tenant)."""

    tenant_role: str | None = Field(default=None, description="Role of the calling tenant")
    tenant_id: str | None = Field(default=None, description="Specific tenant identifier")
    environment: str | None = Field(default=None, description="Deployment environment")


class ResourceSpec(BaseModel, frozen=True):
    """Attributes that identify a resource (secret)."""

    name: str = Field(description="Secret name pattern (supports fnmatch wildcards)")


class ABACRule(BaseModel, frozen=True):
    """A single ABAC policy rule."""

    id: str = Field(description="Unique rule identifier")
    effect: Effect = Field(description="allow or deny")
    subjects: list[SubjectSpec] = Field(description="Subject attribute matchers")
    resources: list[ResourceSpec] = Field(description="Resource attribute matchers")
    actions: list[Action] = Field(description="Actions this rule applies to")


class ABACPolicy(BaseModel, frozen=True):
    """Top-level ABAC policy containing a list of rules.

    Rules are evaluated in order. First matching rule wins.
    Default effect when no rule matches is DENY.
    """

    rules: list[ABACRule] = Field(default_factory=list)
