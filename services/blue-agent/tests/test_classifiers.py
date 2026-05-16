"""Tests for the HH-RLHF classifier implementation."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from blue_agent.classifiers.hh_rlhf_classifier import HHRLHFClassifier
from centinela.models.evaluation import ClassificationResult


class TestHHRLHFClassifier:
    """Tests for the HHRLHFClassifier with mocked pipeline."""

    @patch("blue_agent.classifiers.hh_rlhf_classifier.pipeline")
    def test_classify_safe_response(self, mock_pipeline_cls: MagicMock) -> None:
        """Pipeline returning LABEL_1 maps to 'safe' classification."""
        mock_pipeline = MagicMock()
        mock_pipeline.return_value = [{"label": "LABEL_1", "score": 0.95}]
        mock_pipeline_cls.return_value = mock_pipeline

        classifier = HHRLHFClassifier(model_path="./mock-model")
        result = classifier.classify("This is a helpful and safe response.")

        assert result.label == "safe"
        assert result.confidence == 0.95
        assert result.model_source == "hh_rlhf"
        mock_pipeline.assert_called_once_with("This is a helpful and safe response.")

    @patch("blue_agent.classifiers.hh_rlhf_classifier.pipeline")
    def test_classify_harm_response(self, mock_pipeline_cls: MagicMock) -> None:
        """Pipeline returning LABEL_0 maps to 'harm' classification."""
        mock_pipeline = MagicMock()
        mock_pipeline.return_value = [{"label": "LABEL_0", "score": 0.80}]
        mock_pipeline_cls.return_value = mock_pipeline

        classifier = HHRLHFClassifier(model_path="./mock-model")
        result = classifier.classify("This response contains harmful content.")

        assert result.label == "harm"
        assert result.confidence == 0.80
        assert result.model_source == "hh_rlhf"

    def test_classify_accepts_only_response_text(self) -> None:
        """classify() accepts only response_text (no prompt parameter)."""
        import inspect

        sig = inspect.signature(HHRLHFClassifier.classify)
        params = list(sig.parameters.keys())
        assert "response_text" in params
        assert "prompt" not in params

    @patch("blue_agent.classifiers.hh_rlhf_classifier.pipeline")
    def test_invalid_model_path_raises(self, mock_pipeline_cls: MagicMock) -> None:
        """Invalid model_path raises ValueError with clear message."""
        mock_pipeline_cls.side_effect = OSError("Model not found")

        with pytest.raises(ValueError, match="Failed to load HH-RLHF classifier"):
            HHRLHFClassifier(model_path="./nonexistent-model")


class TestClassificationResultImmutability:
    """Tests for ClassificationResult immutability (frozen=True)."""

    def test_result_is_frozen(self) -> None:
        """ClassificationResult cannot be modified after creation."""
        result = ClassificationResult(
            label="safe",
            confidence=0.95,
            model_source="hh_rlhf",
        )

        with pytest.raises(ValidationError):
            result.label = "harm"  # type: ignore[misc]
