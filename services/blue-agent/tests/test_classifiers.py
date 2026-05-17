"""Tests for the HH-RLHF classifier implementation."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from blue_agent.classifiers.ensemble import EnsembleClassifier
from blue_agent.classifiers.hh_rlhf_classifier import HHRLHFClassifier
from blue_agent.classifiers.toxigen_classifier import ToxiGenClassifier
from blue_agent.classifiers.base import SafetyClassifier
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


class TestToxiGenClassifier:
    """Tests for the ToxiGenClassifier with mocked pipeline."""

    @patch("blue_agent.classifiers.toxigen_classifier.pipeline")
    def test_classify_safe_response(self, mock_pipeline_cls: MagicMock) -> None:
        """Pipeline returning LABEL_0 maps to 'safe' classification."""
        mock_pipeline = MagicMock()
        mock_pipeline.return_value = [{"label": "LABEL_0", "score": 0.92}]
        mock_pipeline_cls.return_value = mock_pipeline

        classifier = ToxiGenClassifier(model_path="./mock-toxigen-model")
        result = classifier.classify("This is a benign response.")

        assert result.label == "safe"
        assert result.confidence == 0.92
        assert result.model_source == "toxigen"
        mock_pipeline.assert_called_once_with("This is a benign response.")

    @patch("blue_agent.classifiers.toxigen_classifier.pipeline")
    def test_classify_harm_response(self, mock_pipeline_cls: MagicMock) -> None:
        """Pipeline returning LABEL_1 maps to 'harm' classification."""
        mock_pipeline = MagicMock()
        mock_pipeline.return_value = [{"label": "LABEL_1", "score": 0.88}]
        mock_pipeline_cls.return_value = mock_pipeline

        classifier = ToxiGenClassifier(model_path="./mock-toxigen-model")
        result = classifier.classify("This response contains implicit toxicity.")

        assert result.label == "harm"
        assert result.confidence == 0.88
        assert result.model_source == "toxigen"

    @patch("blue_agent.classifiers.toxigen_classifier.pipeline")
    def test_invalid_model_path_raises(self, mock_pipeline_cls: MagicMock) -> None:
        """Invalid model_path raises ValueError with clear message."""
        mock_pipeline_cls.side_effect = OSError("Model not found")

        with pytest.raises(ValueError, match="Failed to load ToxiGen classifier"):
            ToxiGenClassifier(model_path="./nonexistent-model")

    def test_classify_accepts_only_response_text(self) -> None:
        """classify() accepts only response_text (no prompt parameter)."""
        import inspect

        sig = inspect.signature(ToxiGenClassifier.classify)
        params = list(sig.parameters.keys())
        assert "response_text" in params
        assert "prompt" not in params


class TestEnsembleClassifier:
    """Tests for the EnsembleClassifier with mock sub-classifiers."""

    def _make_mock_classifier(self, label: str, confidence: float) -> SafetyClassifier:
        """Create a mock SafetyClassifier returning fixed results."""
        mock = MagicMock(spec=SafetyClassifier)
        mock.classify.return_value = ClassificationResult(
            label=label,
            confidence=confidence,
            model_source="mock",
        )
        return mock

    def test_both_agree_safe(self) -> None:
        """Both classifiers agree on 'safe' -> result is 'safe' with mean confidence."""
        c1 = self._make_mock_classifier("safe", 0.90)
        c2 = self._make_mock_classifier("safe", 0.80)
        ensemble = EnsembleClassifier(classifiers=[c1, c2])

        result = ensemble.classify("Safe response text")

        assert result.label == "safe"
        assert result.confidence == pytest.approx(0.85)  # mean of 0.90 and 0.80
        assert result.model_source == "ensemble"

    def test_both_agree_harm(self) -> None:
        """Both classifiers agree on 'harm' -> result is 'harm' with mean confidence."""
        c1 = self._make_mock_classifier("harm", 0.85)
        c2 = self._make_mock_classifier("harm", 0.75)
        ensemble = EnsembleClassifier(classifiers=[c1, c2])

        result = ensemble.classify("Harmful response text")

        assert result.label == "harm"
        assert result.confidence == pytest.approx(0.80)  # mean of 0.85 and 0.75
        assert result.model_source == "ensemble"

    def test_disagree_returns_conservative_harm(self) -> None:
        """Disagreement (one safe, one harm) -> result is 'harm' with reduced confidence."""
        c1 = self._make_mock_classifier("safe", 0.90)
        c2 = self._make_mock_classifier("harm", 0.70)
        ensemble = EnsembleClassifier(classifiers=[c1, c2])

        result = ensemble.classify("Ambiguous response text")

        assert result.label == "harm"  # conservative
        assert result.confidence == pytest.approx(0.56)  # min(0.90, 0.70) * 0.8 = 0.56
        assert result.model_source == "ensemble"

    def test_get_sub_results_returns_individual_results(self) -> None:
        """get_sub_results() returns individual classification results."""
        c1 = self._make_mock_classifier("safe", 0.90)
        c2 = self._make_mock_classifier("harm", 0.70)
        ensemble = EnsembleClassifier(classifiers=[c1, c2])

        sub_results = ensemble.get_sub_results("Test text")

        assert len(sub_results) == 2
        assert sub_results[0].label == "safe"
        assert sub_results[0].confidence == 0.90
        assert sub_results[1].label == "harm"
        assert sub_results[1].confidence == 0.70

    def test_ensemble_accepts_only_response_text(self) -> None:
        """classify() accepts only response_text (no prompt parameter)."""
        import inspect

        sig = inspect.signature(EnsembleClassifier.classify)
        params = list(sig.parameters.keys())
        assert "response_text" in params
        assert "prompt" not in params

    def test_empty_classifiers_raises(self) -> None:
        """EnsembleClassifier requires at least one sub-classifier."""
        with pytest.raises(ValueError, match="At least one classifier"):
            EnsembleClassifier(classifiers=[])
