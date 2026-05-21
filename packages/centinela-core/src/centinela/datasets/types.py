"""Dataset types and enums for adversarial testing datasets.

Provides unified schema for all datasets used by red-agent (AdvBench, JailbreakBench, Gandalf)
and blue-agent training (ToxiGen, HH-RLHF).
"""

from datetime import UTC, datetime
from enum import auto
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DatasetCategory(str):
    """Categories for adversarial prompts and training data."""

    VIOLENCE = auto()
    DRUGS = auto()
    HATE_SPEECH = auto()
    SEXUAL_CONTENT = auto()
    SELF_HARM = auto()
    PRIVACY = auto()
    MALICIOUS_USE = auto()
    JAILBREAK = auto()
    DOMAIN_SPECIFIC = auto()
    GENERAL = auto()


class DatasetEntry(BaseModel, frozen=True):
    """Single entry in an adversarial or training dataset.

    All datasets are normalized to this schema regardless of original format.
    """

    entry_id: UUID = Field(default_factory=uuid4)
    prompt: str
    label: str | None = None
    category: DatasetCategory = DatasetCategory.GENERAL
    severity: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DatasetMetadata(BaseModel, frozen=True):
    """Metadata about a loaded dataset."""

    name: str
    version: str
    source: str
    total_entries: int
    categories: list[DatasetCategory]
    license: str | None = None
    description: str = ""
