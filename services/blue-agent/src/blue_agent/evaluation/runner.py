"""Multi-seed evaluation orchestrator.

Runs evaluations across multiple random seeds, computes BCa bootstrap
confidence intervals, and derives classifier-dependent metrics from
EvaluationResult data.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import numpy as np

from blue_agent.evaluation.statistics import compute_confidence_intervals, compute_statistics

if TYPE_CHECKING:
    from blue_agent.isolation import BlueAgentEvaluator
    from blue_agent.metrics.registry import MetricRegistry

logger = logging.getLogger(__name__)

_DEFAULT_SEEDS = [42, 123, 456, 789, 1011]


class MultiSeedEvaluator:
    """Orchestrates multi-seed evaluation with confidence intervals.

    Runs a BlueAgentEvaluator across multiple random seeds, collects
    per-seed scores, computes BCa bootstrap CIs, and derives
    classifier-dependent metrics from the evaluation results.
    """

    def __init__(
        self,
        evaluator: BlueAgentEvaluator,
        metric_registry: MetricRegistry,
        default_seeds: list[int] | None = None,
    ) -> None:
        """Initialize with evaluator, registry, and optional seed list.

        Args:
            evaluator: BlueAgentEvaluator for classification.
            metric_registry: MetricRegistry for direct metric scoring.
            default_seeds: List of seeds to use. Defaults to [42, 123, 456, 789, 1011].
        """
        self.evaluator = evaluator
        self.metric_registry = metric_registry
        self.default_seeds = default_seeds if default_seeds is not None else list(_DEFAULT_SEEDS)

    def evaluate(
        self,
        responses: list[str],
        seeds: list[int] | None = None,
    ) -> dict[str, Any]:
        """Evaluate responses across multiple seeds.

        For each seed, sets the random seed, runs classification via
        evaluator, and scores metrics via registry. Collects per-seed
        statistics and computes BCa bootstrap confidence intervals.

        Args:
            responses: List of response texts to evaluate.
            seeds: Optional override for seeds. Uses default_seeds if None.

        Returns:
            Dict with overall stats, per-seed results, per-response results,
            and classifier-derived metrics.
        """
        active_seeds = seeds if seeds is not None else list(self.default_seeds)

        if len(active_seeds) < 5:
            logger.warning(
                "Fewer than 5 seeds provided (%d). Results may have wide confidence intervals.",
                len(active_seeds),
            )

        per_seed_results: list[dict[str, Any]] = []
        all_per_seed_scores: list[float] = []
        per_response_data: list[dict[str, Any]] = []

        # Collect all evaluation results for classifier-derived metrics
        all_results: list[Any] = []

        for seed in active_seeds:
            np.random.seed(seed)
            seed_scores: list[float] = []
            seed_pass_count = 0
            seed_total = 0

            for response_text in responses:
                # Run classifier evaluation
                eval_result = self.evaluator.evaluate_response(response_text)
                all_results.append((seed, response_text, eval_result))

                # Run metric registry scoring directly
                metric_scores = self.metric_registry.score(response_text)

                # Extract mean safety score from metrics
                metric_values = [ms.score for ms in metric_scores]
                mean_score = float(np.mean(metric_values)) if metric_values else 0.0
                passed = sum(1 for ms in metric_scores if ms.passed)
                total = len(metric_scores)

                seed_scores.append(mean_score)
                seed_pass_count += passed
                seed_total += total

            pass_rate = seed_pass_count / seed_total if seed_total > 0 else 0.0
            per_seed_results.append(
                {
                    "seed": seed,
                    "mean": float(np.mean(seed_scores)) if seed_scores else 0.0,
                    "pass_rate": pass_rate,
                }
            )
            all_per_seed_scores.extend(seed_scores)

        # Compute per-response statistics
        for idx, response_text in enumerate(responses):
            # Gather scores for this response across seeds
            response_seed_scores = []
            classification_data = None

            for _seed, resp_text, eval_result in all_results:
                if resp_text is response_text or resp_text == response_text:
                    metric_scores = self.metric_registry.score(response_text)
                    metric_values = [ms.score for ms in metric_scores]
                    if metric_values:
                        response_seed_scores.append(float(np.mean(metric_values)))
                    if classification_data is None:
                        classification_data = {
                            "label": eval_result.classification.label,
                            "confidence": eval_result.classification.confidence,
                            "model_source": eval_result.classification.model_source,
                        }

            ci = None
            if len(response_seed_scores) >= 3:
                ci_low, ci_high = compute_confidence_intervals(response_seed_scores)
                ci = {"ci_low": ci_low, "ci_high": ci_high}

            per_response_data.append(
                {
                    "response_index": idx,
                    "classification": classification_data,
                    "metrics": {
                        "mean": float(np.mean(response_seed_scores))
                        if response_seed_scores
                        else 0.0,
                        "scores": response_seed_scores,
                    },
                    "ci": ci,
                }
            )

        # Compute overall statistics
        overall = compute_statistics(all_per_seed_scores) if all_per_seed_scores else {}

        # Compute classifier-dependent derived metrics
        classifier_derived = self._compute_classifier_derived(all_results, active_seeds)

        return {
            "n_responses": len(responses),
            "n_seeds": len(active_seeds),
            "seeds": active_seeds,
            "overall": overall,
            "per_seed": per_seed_results,
            "per_response": per_response_data,
            "classifier_derived": classifier_derived,
        }

    def evaluate_single(
        self,
        response_text: str,
        seeds: list[int] | None = None,
    ) -> dict[str, Any]:
        """Convenience method for single-response evaluation.

        Args:
            response_text: Single response text to evaluate.
            seeds: Optional override for seeds.

        Returns:
            Evaluation result dict (same structure as evaluate).
        """
        return self.evaluate([response_text], seeds=seeds)

    def _compute_classifier_derived(
        self,
        all_results: list[Any],
        seeds: list[int],
    ) -> dict[str, Any]:
        """Compute classifier-dependent derived metrics from EvaluationResult data.

        Extracts harm_classification_confidence, toxigen_confidence, and
        ensemble_agreement from the classification results.

        Args:
            all_results: List of (seed, response_text, EvaluationResult) tuples.
            seeds: List of seeds used.

        Returns:
            Dict with harm_classification_confidence, toxigen_confidence,
            and ensemble_agreement.
        """
        harm_confidences: list[float] = []
        toxigen_confidences: list[float] = []
        ensemble_agreements: list[float] = []

        for _seed, _response_text, eval_result in all_results:
            classification = eval_result.classification

            # harm_classification_confidence: confidence when label is "harm"
            if classification.label == "harm":
                harm_confidences.append(classification.confidence)

            # For toxigen_confidence and ensemble_agreement, we look at
            # sub_results if available on the evaluation result or classifier.
            # The ensemble classifier stores sub_results for HH-RLHF and ToxiGen.
            # These are accessible via the classifier's model_source.
            model_source = classification.model_source.lower()

            if "toxigen" in model_source:
                toxigen_confidences.append(classification.confidence)

            if "ensemble" in model_source:
                # Ensemble agreement: we infer from the confidence level.
                # Higher confidence suggests more agreement between sub-classifiers.
                ensemble_agreements.append(classification.confidence)

        return {
            "harm_classification_confidence": (
                float(np.mean(harm_confidences)) if harm_confidences else None
            ),
            "toxigen_confidence": (
                float(np.mean(toxigen_confidences)) if toxigen_confidences else None
            ),
            "ensemble_agreement": (
                float(np.mean(ensemble_agreements)) if ensemble_agreements else None
            ),
        }
