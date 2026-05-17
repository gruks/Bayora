"""Isolation layer for the blue-agent evaluation system.

Enforces BLUE-04: the blue-agent never receives the original prompt.
The orchestrator strips prompts before forwarding responses to this layer.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog
from centinela.models.evaluation import EvaluationResult, MetricScore

if TYPE_CHECKING:
    from blue_agent.classifiers.base import SafetyClassifier
    from blue_agent.metrics.registry import MetricRegistry

logger = structlog.get_logger()


class BlueAgentEvaluator:
    """Evaluates model responses using a safety classifier.

    The interface accepts ONLY response_text — no prompt parameter.
    This enforces BLUE-04 at the API boundary.
    """

    def __init__(
        self,
        classifier: SafetyClassifier,
        metric_registry: MetricRegistry | None = None,
    ) -> None:
        """Initialize with a safety classifier and optional metric registry.

        Args:
            classifier: A SafetyClassifier implementation used to
                classify response text as safe or harmful.
            metric_registry: Optional MetricRegistry for scoring response
                metrics alongside classification.
        """
        self._classifier = classifier
        self.metric_registry = metric_registry

    def evaluate_response(self, response_text: str) -> EvaluationResult:
        """Evaluate a model response for safety.

        Args:
            response_text: The model's response text to evaluate.
                The original prompt is NEVER accessible here.

        Returns:
            EvaluationResult containing the classification and any
                metric scores (empty list if no registry provided).
        """
        classification = self._classifier.classify(response_text)

        metric_scores: list[MetricScore] = []
        if self.metric_registry is not None:
            metric_scores = self.metric_registry.score(response_text)

        logger.info(
            "evaluation_complete",
            response_length=len(response_text),
            label=classification.label,
            confidence=classification.confidence,
            model_source=classification.model_source,
            n_metrics=len(metric_scores),
        )

        return EvaluationResult(
            classification=classification,
            metric_scores=metric_scores,
            timestamp=datetime.now(UTC),
        )
