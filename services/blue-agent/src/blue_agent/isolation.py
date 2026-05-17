"""Isolation layer for the blue-agent evaluation system.

Enforces BLUE-04: the blue-agent never receives the original prompt.
The orchestrator strips prompts before forwarding responses to this layer.
"""

from datetime import UTC, datetime

import structlog
from centinela.models.evaluation import EvaluationResult

from blue_agent.classifiers.base import SafetyClassifier

logger = structlog.get_logger()


class BlueAgentEvaluator:
    """Evaluates model responses using a safety classifier.

    The interface accepts ONLY response_text — no prompt parameter.
    This enforces BLUE-04 at the API boundary.
    """

    def __init__(self, classifier: SafetyClassifier) -> None:
        """Initialize with a safety classifier.

        Args:
            classifier: A SafetyClassifier implementation used to
                classify response text as safe or harmful.
        """
        self._classifier = classifier

    def evaluate_response(self, response_text: str) -> EvaluationResult:
        """Evaluate a model response for safety.

        Args:
            response_text: The model's response text to evaluate.
                The original prompt is NEVER accessible here.

        Returns:
            EvaluationResult containing the classification and any
                metric scores (empty list for base implementation).
        """
        classification = self._classifier.classify(response_text)

        logger.info(
            "evaluation_complete",
            response_length=len(response_text),
            label=classification.label,
            confidence=classification.confidence,
            model_source=classification.model_source,
        )

        return EvaluationResult(
            classification=classification,
            metric_scores=[],
            timestamp=datetime.now(UTC),
        )
