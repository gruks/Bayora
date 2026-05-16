"""Tests for the blue-agent isolation layer and evaluation types."""

import inspect
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from blue_agent.isolation import BlueAgentEvaluator
from centinela.models.evaluation import (
    ClassificationResult,
    EvaluationResult,
    MetricScore,
)


def _make_mock_classifier(label="safe", confidence=0.95):
    """Create a mock SafetyClassifier that returns a fixed ClassificationResult."""
    mock = MagicMock()
    mock.classify.return_value = ClassificationResult(
        label=label,
        confidence=confidence,
        model_source="mock",
    )
    return mock


class TestBlueAgentEvaluator:
    """Tests for the BlueAgentEvaluator isolation layer."""

    def test_evaluate_response_with_mock_classifier(self) -> None:
        """BlueAgentEvaluator.evaluate_response() works with a mock classifier."""
        classifier = _make_mock_classifier(label="safe", confidence=0.95)
        evaluator = BlueAgentEvaluator(classifier=classifier)

        result = evaluator.evaluate_response("This is a safe response.")

        assert result.classification.label == "safe"
        assert result.classification.confidence == 0.95
        assert result.classification.model_source == "mock"
        assert result.metric_scores == []
        assert result.timestamp is not None
        classifier.classify.assert_called_once_with("This is a safe response.")

    def test_evaluate_response_harm_classification(self) -> None:
        """BlueAgentEvaluator correctly propagates harm classification."""
        classifier = _make_mock_classifier(label="harm", confidence=0.88)
        evaluator = BlueAgentEvaluator(classifier=classifier)

        result = evaluator.evaluate_response("This is harmful content.")

        assert result.classification.label == "harm"
        assert result.classification.confidence == 0.88

    def test_no_method_accepts_prompt_parameter(self) -> None:
        """No method on BlueAgentEvaluator accepts a prompt parameter (BLUE-04)."""
        sig = inspect.signature(BlueAgentEvaluator.evaluate_response)
        assert "prompt" not in sig.parameters

        # Also check __init__
        sig_init = inspect.signature(BlueAgentEvaluator.__init__)
        assert "prompt" not in sig_init.parameters


class TestClassificationResultImmutability:
    """Tests for ClassificationResult frozen=True immutability."""

    def test_classification_result_is_frozen(self) -> None:
        """ClassificationResult cannot be modified after creation."""
        result = ClassificationResult(
            label="safe",
            confidence=0.95,
            model_source="test",
        )

        with pytest.raises(ValidationError):
            result.label = "harm"  # type: ignore[misc]

    def test_classification_result_valid_values(self) -> None:
        """ClassificationResult accepts valid label and confidence values."""
        safe = ClassificationResult(label="safe", confidence=1.0, model_source="test")
        assert safe.label == "safe"
        assert safe.confidence == 1.0

        harm = ClassificationResult(label="harm", confidence=0.0, model_source="test")
        assert harm.label == "harm"
        assert harm.confidence == 0.0

    def test_classification_result_rejects_invalid_confidence(self) -> None:
        """ClassificationResult rejects confidence outside [0.0, 1.0]."""
        with pytest.raises(ValidationError):
            ClassificationResult(label="safe", confidence=1.5, model_source="test")

        with pytest.raises(ValidationError):
            ClassificationResult(label="safe", confidence=-0.1, model_source="test")

    def test_classification_result_rejects_invalid_label(self) -> None:
        """ClassificationResult rejects labels other than 'safe' or 'harm'."""
        with pytest.raises(ValidationError):
            ClassificationResult(label="unsafe", confidence=0.5, model_source="test")


class TestEvaluationResultImmutability:
    """Tests for EvaluationResult frozen=True immutability."""

    def test_evaluation_result_is_frozen(self) -> None:
        """EvaluationResult cannot be modified after creation."""
        classification = ClassificationResult(label="safe", confidence=0.95, model_source="test")
        result = EvaluationResult(
            classification=classification,
            metric_scores=[],
            timestamp=datetime.now(timezone.utc),
        )

        with pytest.raises(ValidationError):
            result.classification = classification  # type: ignore[misc]

    def test_evaluation_result_with_metric_scores(self) -> None:
        """EvaluationResult accepts metric scores."""
        classification = ClassificationResult(label="safe", confidence=0.95, model_source="test")
        metric = MetricScore(
            name="toxicity",
            category="safety",
            score=0.1,
            passed=True,
        )
        result = EvaluationResult(
            classification=classification,
            metric_scores=[metric],
            timestamp=datetime.now(timezone.utc),
        )

        assert len(result.metric_scores) == 1
        assert result.metric_scores[0].name == "toxicity"
        assert result.metric_scores[0].passed is True

    def test_evaluation_result_with_seed(self) -> None:
        """EvaluationResult accepts optional seed."""
        classification = ClassificationResult(label="safe", confidence=0.95, model_source="test")
        result = EvaluationResult(
            classification=classification,
            metric_scores=[],
            seed=42,
            timestamp=datetime.now(timezone.utc),
        )

        assert result.seed == 42
