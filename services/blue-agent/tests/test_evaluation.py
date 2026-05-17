"""Tests for the multi-seed evaluation engine with BCa bootstrap CIs."""

import logging
from unittest.mock import MagicMock

import pytest
from blue_agent.evaluation.runner import MultiSeedEvaluator
from blue_agent.evaluation.statistics import compute_confidence_intervals, compute_statistics
from blue_agent.isolation import BlueAgentEvaluator
from centinela.models.evaluation import ClassificationResult, MetricScore

# ---------------------------------------------------------------------------
# Statistics unit tests
# ---------------------------------------------------------------------------


class TestComputeConfidenceIntervals:
    """Tests for BCa bootstrap confidence interval computation."""

    def test_ci_contains_mean_for_known_data(self) -> None:
        """BCa CI from 5 seeds should contain the mean."""
        scores = [0.8, 0.85, 0.9, 0.75, 0.88]
        ci_low, ci_high = compute_confidence_intervals(scores)
        mean = sum(scores) / len(scores)
        assert ci_low <= mean <= ci_high, (
            f"Expected mean {mean} to be within CI [{ci_low}, {ci_high}]"
        )

    def test_fewer_than_3_seeds_raises_value_error(self) -> None:
        """Fewer than 3 seeds must raise ValueError."""
        with pytest.raises(ValueError, match="Minimum 3 seeds required for BCa bootstrap"):
            compute_confidence_intervals([0.8, 0.85])

    def test_empty_list_raises_value_error(self) -> None:
        """Empty score list should also raise ValueError (fewer than 3)."""
        with pytest.raises(ValueError, match="Minimum 3 seeds required for BCa bootstrap"):
            compute_confidence_intervals([])


class TestComputeStatistics:
    """Tests for descriptive statistics computation."""

    def test_returns_all_expected_keys(self) -> None:
        """compute_statistics returns dict with all required keys."""
        scores = [0.8, 0.85, 0.9, 0.75, 0.88]
        stats = compute_statistics(scores)

        expected_keys = {"mean", "std", "median", "min", "max", "ci_low", "ci_high", "n_seeds"}
        assert set(stats.keys()) == expected_keys, (
            f"Missing keys: {expected_keys - set(stats.keys())}"
        )

    def test_mean_is_correct(self) -> None:
        """Mean of known scores is computed correctly."""
        scores = [0.8, 0.85, 0.9, 0.75, 0.88]
        stats = compute_statistics(scores)
        expected_mean = sum(scores) / len(scores)
        assert abs(stats["mean"] - expected_mean) < 1e-10

    def test_n_seeds_is_correct(self) -> None:
        """n_seeds matches input length."""
        scores = [0.8, 0.85, 0.9]
        stats = compute_statistics(scores)
        assert stats["n_seeds"] == 3

    def test_min_max_are_correct(self) -> None:
        """min and max values are correct."""
        scores = [0.8, 0.85, 0.9, 0.75, 0.88]
        stats = compute_statistics(scores)
        assert stats["min"] == 0.75
        assert stats["max"] == 0.9


# ---------------------------------------------------------------------------
# MultiSeedEvaluator unit tests
# ---------------------------------------------------------------------------


def _make_mock_evaluator(
    label: str = "safe",
    confidence: float = 0.95,
    model_source: str = "mock",
) -> BlueAgentEvaluator:
    """Create a BlueAgentEvaluator with a mock classifier that returns fixed results."""
    mock_classifier = MagicMock()
    mock_classifier.classify.return_value = ClassificationResult(
        label=label,
        confidence=confidence,
        model_source=model_source,
    )
    return BlueAgentEvaluator(classifier=mock_classifier)


def _make_mock_registry(
    scores: list[MetricScore] | None = None,
) -> MagicMock:
    """Create a mock MetricRegistry that returns known scores."""
    if scores is None:
        scores = [
            MetricScore(name="toxicity", category="toxicity", score=0.2, passed=True),
            MetricScore(name="bias", category="bias", score=0.1, passed=True),
        ]
    registry = MagicMock()
    registry.score.return_value = scores
    return registry


class TestMultiSeedEvaluator:
    """Tests for the MultiSeedEvaluator orchestrator."""

    def test_evaluate_returns_correct_structure(self) -> None:
        """evaluate() returns dict with all expected top-level keys."""
        evaluator = _make_mock_evaluator()
        registry = _make_mock_registry()
        mse = MultiSeedEvaluator(evaluator=evaluator, metric_registry=registry)

        responses = ["safe response one", "safe response two"]
        result = mse.evaluate(responses)

        expected_keys = {
            "n_responses",
            "n_seeds",
            "seeds",
            "overall",
            "per_seed",
            "per_response",
            "classifier_derived",
        }
        assert set(result.keys()) == expected_keys, (
            f"Missing keys: {expected_keys - set(result.keys())}"
        )

    def test_evaluate_uses_default_seeds_when_none_provided(self) -> None:
        """Default seeds [42, 123, 456, 789, 1011] are used when seeds=None."""
        evaluator = _make_mock_evaluator()
        registry = _make_mock_registry()
        mse = MultiSeedEvaluator(evaluator=evaluator, metric_registry=registry)

        result = mse.evaluate(["test response"])
        assert result["n_seeds"] == 5
        assert result["seeds"] == [42, 123, 456, 789, 1011]

    def test_custom_seeds_override_defaults(self) -> None:
        """Custom seeds override the default seed list."""
        evaluator = _make_mock_evaluator()
        registry = _make_mock_registry()
        mse = MultiSeedEvaluator(evaluator=evaluator, metric_registry=registry)

        custom_seeds = [7, 13, 21]
        result = mse.evaluate(["test response"], seeds=custom_seeds)
        assert result["n_seeds"] == 3
        assert result["seeds"] == custom_seeds

    def test_classifier_derived_section_present(self) -> None:
        """Output always includes classifier_derived section."""
        evaluator = _make_mock_evaluator()
        registry = _make_mock_registry()
        mse = MultiSeedEvaluator(evaluator=evaluator, metric_registry=registry)

        result = mse.evaluate(["response"])
        derived = result["classifier_derived"]
        assert "harm_classification_confidence" in derived
        assert "toxigen_confidence" in derived
        assert "ensemble_agreement" in derived

    def test_classifier_derived_harm_confidence(self) -> None:
        """harm_classification_confidence is populated when label='harm'."""
        evaluator = _make_mock_evaluator(label="harm", confidence=0.88, model_source="test")
        registry = _make_mock_registry()
        mse = MultiSeedEvaluator(evaluator=evaluator, metric_registry=registry)

        result = mse.evaluate(["harmful response"])
        derived = result["classifier_derived"]
        assert derived["harm_classification_confidence"] == pytest.approx(0.88)

    def test_classifier_derived_toxigen_confidence(self) -> None:
        """toxigen_confidence is populated when model_source contains 'toxigen'."""
        evaluator = _make_mock_evaluator(model_source="toxigen_v1")
        registry = _make_mock_registry()
        mse = MultiSeedEvaluator(evaluator=evaluator, metric_registry=registry)

        result = mse.evaluate(["response"])
        derived = result["classifier_derived"]
        assert derived["toxigen_confidence"] == 0.95

    def test_classifier_derived_ensemble_agreement(self) -> None:
        """ensemble_agreement is populated when model_source contains 'ensemble'."""
        evaluator = _make_mock_evaluator(model_source="ensemble_v2")
        registry = _make_mock_registry()
        mse = MultiSeedEvaluator(evaluator=evaluator, metric_registry=registry)

        result = mse.evaluate(["response"])
        derived = result["classifier_derived"]
        assert derived["ensemble_agreement"] == 0.95

    def test_per_seed_results_correct(self) -> None:
        """Per-seed results contain expected keys."""
        evaluator = _make_mock_evaluator()
        registry = _make_mock_registry()
        mse = MultiSeedEvaluator(evaluator=evaluator, metric_registry=registry)

        result = mse.evaluate(["response"])
        for entry in result["per_seed"]:
            assert "seed" in entry
            assert "mean" in entry
            assert "pass_rate" in entry

    def test_per_response_results_correct(self) -> None:
        """Per-response results contain expected keys."""
        evaluator = _make_mock_evaluator()
        registry = _make_mock_registry()
        mse = MultiSeedEvaluator(evaluator=evaluator, metric_registry=registry)

        result = mse.evaluate(["response"])
        for entry in result["per_response"]:
            assert "response_index" in entry
            assert "classification" in entry
            assert "metrics" in entry

    def test_n_responses_matches_input(self) -> None:
        """n_responses matches the number of input responses."""
        evaluator = _make_mock_evaluator()
        registry = _make_mock_registry()
        mse = MultiSeedEvaluator(evaluator=evaluator, metric_registry=registry)

        responses = ["r1", "r2", "r3"]
        result = mse.evaluate(responses)
        assert result["n_responses"] == 3

    def test_evaluate_single_returns_same_structure(self) -> None:
        """evaluate_single() returns the same dict structure as evaluate()."""
        evaluator = _make_mock_evaluator()
        registry = _make_mock_registry()
        mse = MultiSeedEvaluator(evaluator=evaluator, metric_registry=registry)

        result = mse.evaluate_single("single response")
        assert result["n_responses"] == 1
        assert "overall" in result
        assert "classifier_derived" in result

    def test_fewer_than_5_seeds_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """A warning is logged when fewer than 5 seeds are provided."""
        evaluator = _make_mock_evaluator()
        registry = _make_mock_registry()
        mse = MultiSeedEvaluator(evaluator=evaluator, metric_registry=registry)

        with caplog.at_level(logging.WARNING):
            mse.evaluate(["response"], seeds=[1, 2, 3])

        assert any("Fewer than 5 seeds" in message for message in caplog.messages)


# ---------------------------------------------------------------------------
# BlueAgentEvaluator integration tests
# ---------------------------------------------------------------------------


class TestBlueAgentEvaluatorWithMetricRegistry:
    """Tests for BlueAgentEvaluator with optional MetricRegistry."""

    def test_evaluate_response_with_registry_includes_metrics(self) -> None:
        """EvaluationResult includes metric_scores when metric_registry is provided."""
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = ClassificationResult(
            label="safe",
            confidence=0.95,
            model_source="mock",
        )
        mock_registry = MagicMock()
        expected_metrics = [
            MetricScore(name="toxicity", category="toxicity", score=0.2, passed=True),
        ]
        mock_registry.score.return_value = expected_metrics

        evaluator = BlueAgentEvaluator(classifier=mock_classifier, metric_registry=mock_registry)
        result = evaluator.evaluate_response("test response")

        assert len(result.metric_scores) == 1
        assert result.metric_scores[0].name == "toxicity"
        assert result.metric_scores[0].score == 0.2
        mock_registry.score.assert_called_once_with("test response")

    def test_evaluate_response_without_registry_empty_metrics(self) -> None:
        """EvaluationResult has empty metric_scores when no registry is given."""
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = ClassificationResult(
            label="safe",
            confidence=0.95,
            model_source="mock",
        )

        evaluator = BlueAgentEvaluator(classifier=mock_classifier)
        result = evaluator.evaluate_response("test response")

        assert result.metric_scores == []

    def test_metric_registry_signature_present(self) -> None:
        """BlueAgentEvaluator.__init__ accepts optional metric_registry parameter."""
        import inspect

        sig = inspect.signature(BlueAgentEvaluator.__init__)
        assert "metric_registry" in sig.parameters

    def test_metric_registry_param_is_optional(self) -> None:
        """metric_registry parameter defaults to None."""
        import inspect

        sig = inspect.signature(BlueAgentEvaluator.__init__)
        param = sig.parameters["metric_registry"]
        assert param.default is None

    def test_backward_compatible_without_registry(self) -> None:
        """BlueAgentEvaluator works without metric_registry (backward compat)."""
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = ClassificationResult(
            label="safe",
            confidence=0.95,
            model_source="mock",
        )

        evaluator = BlueAgentEvaluator(classifier=mock_classifier)
        result = evaluator.evaluate_response("any text")

        assert result.classification.label == "safe"
        assert result.metric_scores == []

    def test_classification_present_with_registry(self) -> None:
        """Classification result is still present when metric_registry is used."""
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = ClassificationResult(
            label="harm",
            confidence=0.88,
            model_source="mock",
        )
        mock_registry = MagicMock()
        mock_registry.score.return_value = []

        evaluator = BlueAgentEvaluator(classifier=mock_classifier, metric_registry=mock_registry)
        result = evaluator.evaluate_response("harmful text")

        assert result.classification.label == "harm"
        assert result.classification.confidence == 0.88
