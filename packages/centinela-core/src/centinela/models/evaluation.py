"""Evaluation types for the blue-agent safety classification system."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ClassificationResult(BaseModel, frozen=True):
    """Result of a single safety classification."""

    label: Literal["safe", "harm"]
    confidence: float = Field(ge=0.0, le=1.0)
    model_source: str


class MetricScore(BaseModel, frozen=True):
    """Score for a single safety metric."""

    name: str
    category: str
    score: float = Field(ge=0.0, le=1.0)
    passed: bool


class EvaluationResult(BaseModel, frozen=True):
    """Complete evaluation result combining classification and metric scores."""

    classification: ClassificationResult
    metric_scores: list[MetricScore]
    seed: int | None = None
    timestamp: datetime
