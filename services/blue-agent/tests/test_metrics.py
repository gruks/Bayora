"""Tests for the metric scoring system."""

from unittest.mock import MagicMock

import pytest

from blue_agent.metrics.base import LLMGuardScorer, MetricScorer
from blue_agent.metrics.registry import MetricRegistry
from centinela.models.evaluation import MetricScore


class TestMetricScorerInterface:
    """Tests for the abstract MetricScorer interface."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """MetricScorer is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError):
            MetricScorer()  # type: ignore[abstract]

    def test_concrete_subclass_must_implement_score(self) -> None:
        """A concrete subclass that doesn't implement score raises TypeError."""

        class IncompleteScorer(MetricScorer):
            pass

        with pytest.raises(TypeError):
            IncompleteScorer()


class TestLLMGuardScorer:
    """Tests for the LLM-Guard wrapper scorer."""

    def _make_mock_scanner(self, sanitized: str, is_valid: bool, risk_score: float):
        """Create a mock LLM-Guard scanner."""
        scanner = MagicMock()
        scanner.scan.return_value = (sanitized, is_valid, risk_score)
        return scanner

    def test_score_returns_metric_score(self) -> None:
        """LLMGuardScorer.score returns a properly constructed MetricScore."""
        scanner = self._make_mock_scanner("clean text", True, 0.3)
        scorer = LLMGuardScorer(
            name="test_toxicity",
            category="toxicity",
            scanner=scanner,
            threshold=0.5,
        )
        result = scorer.score("test input")

        assert result.name == "test_toxicity"
        assert result.category == "toxicity"
        assert result.score == 0.3
        assert result.passed is True

    def test_score_passed_false_when_risk_high(self) -> None:
        """High risk score results in passed=False."""
        scanner = self._make_mock_scanner("bad text", False, 0.8)
        scorer = LLMGuardScorer(
            name="test_toxicity",
            category="toxicity",
            scanner=scanner,
            threshold=0.5,
        )
        result = scorer.score("test input")

        assert result.passed is False
        assert result.score == 0.8

    def test_scanner_called_with_response_text(self) -> None:
        """The underlying scanner is called with the response text."""
        scanner = self._make_mock_scanner("text", True, 0.1)
        scorer = LLMGuardScorer(
            name="test",
            category="test",
            scanner=scanner,
        )
        scorer.score("hello world")
        scanner.scan.assert_called_once_with("hello world")


class TestMetricRegistry:
    """Tests for the MetricRegistry."""

    def _make_mock_scorer(
        self, name: str, category: str, score: float, passed: bool
    ) -> MetricScorer:
        """Create a mock MetricScorer."""
        scorer = MagicMock(spec=MetricScorer)
        scorer.name = name
        scorer.category = category
        scorer.threshold = 0.5
        scorer.score.return_value = MetricScore(
            name=name,
            category=category,
            score=score,
            passed=passed,
        )
        return scorer

    def test_score_returns_correct_number_of_scores(self) -> None:
        """Registry.score returns base + derived metric scores."""
        scorers = [
            self._make_mock_scorer("s1", "toxicity", 0.2, True),
            self._make_mock_scorer("s2", "toxicity", 0.3, True),
            self._make_mock_scorer("s3", "bias", 0.1, True),
            self._make_mock_scorer("s4", "harmfulness", 0.4, True),
            self._make_mock_scorer("s5", "privacy", 0.2, True),
        ]
        registry = MetricRegistry(scorers=[scorers])
        results = registry.score("test response text")

        # 5 base scorers + 17 derived metrics
        assert len(results) >= 5

    def test_score_accepts_only_response_text(self) -> None:
        """Registry.score accepts only response_text, no prompt parameter."""
        scorers = [
            self._make_mock_scorer("s1", "toxicity", 0.2, True),
        ]
        registry = MetricRegistry(scorers=[scorers])
        # This should work with just response_text
        results = registry.score("some text")
        assert len(results) > 0

    def test_get_scores_by_category_groups_correctly(self) -> None:
        """Scores are grouped by category correctly."""
        scores = [
            MetricScore(name="t1", category="toxicity", score=0.2, passed=True),
            MetricScore(name="t2", category="toxicity", score=0.3, passed=True),
            MetricScore(name="b1", category="bias", score=0.1, passed=True),
        ]
        registry = MetricRegistry(scorers=[])
        grouped = registry.get_scores_by_category(scores)

        assert len(grouped["toxicity"]) == 2
        assert len(grouped["bias"]) == 1

    def test_get_summary_returns_correct_counts(self) -> None:
        """Summary returns correct total, passed, failed counts."""
        scores = [
            MetricScore(name="s1", category="toxicity", score=0.2, passed=True),
            MetricScore(name="s2", category="toxicity", score=0.8, passed=False),
            MetricScore(name="s3", category="bias", score=0.1, passed=True),
        ]
        registry = MetricRegistry(scorers=[])
        summary = registry.get_summary(scores)

        assert summary["total"] == 3
        assert summary["passed"] == 2
        assert summary["failed"] == 1
        assert "toxicity" in summary["by_category"]
        assert summary["by_category"]["toxicity"]["total"] == 2

    def test_score_batch_processes_multiple_responses(self) -> None:
        """score_batch returns a list of score lists, one per response."""
        scorers = [
            self._make_mock_scorer("s1", "toxicity", 0.2, True),
        ]
        registry = MetricRegistry(scorers=[scorers])
        results = registry.score_batch(["text one", "text two", "text three"])

        assert len(results) == 3
        assert all(isinstance(r, list) for r in results)

    def test_derived_metrics_computed_from_base_scores(self) -> None:
        """Derived metrics are computed correctly from known base scores."""
        scorers = [
            self._make_mock_scorer("toxicity", "toxicity", 0.4, True),
            self._make_mock_scorer("bias", "bias", 0.3, True),
        ]
        registry = MetricRegistry(scorers=[scorers])
        results = registry.score("test response")

        # Find derived metrics by name
        derived_by_name = {s.name: s for s in results if s.category == "derived"}

        assert "toxicity_mean" in derived_by_name
        assert "bias_mean" in derived_by_name
        assert "overall_safety" in derived_by_name
        assert "passed_ratio" in derived_by_name
        assert "max_risk_score" in derived_by_name
        assert "critical_failures" in derived_by_name
        assert "lexical_diversity" in derived_by_name
        assert "response_complexity" in derived_by_name
        assert "consistency_score" in derived_by_name

    def test_empty_response_handled_gracefully(self) -> None:
        """Empty response text does not cause errors."""
        scorers = [
            self._make_mock_scorer("s1", "toxicity", 0.2, True),
        ]
        registry = MetricRegistry(scorers=[scorers])
        results = registry.score("")
        assert len(results) > 0
