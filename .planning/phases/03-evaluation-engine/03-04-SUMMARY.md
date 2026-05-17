---
phase: 03-evaluation-engine
plan: 04
subsystem: evaluation
tags: bca-bootstrap, scipy, confidence-intervals, multi-seed, classifier-derived-metrics

requires:
  - phase: 03-01
    provides: EvaluationResult, ClassificationResult, MetricScore types, SafetyClassifier interface
  - phase: 03-02
    provides: ToxiGen classifier, ensemble classifier with sub_results
  - phase: 03-03
    provides: MetricRegistry with 17 derived metrics across 6 categories
provides:
  - MultiSeedEvaluator orchestrating classification + metric scoring across multiple random seeds
  - BCa bootstrap confidence intervals via scipy.stats.bootstrap
  - compute_statistics() returning mean, std, median, min, max, ci_low, ci_high, n_seeds
  - Classifier-dependent derived metrics: harm_classification_confidence, toxigen_confidence, ensemble_agreement
  - BlueAgentEvaluator with optional MetricRegistry integration
affects: []
tech-stack:
  added:
    - scipy>=1.14 (BCa bootstrap)
  patterns:
    - TYPE_CHECKING guards for circular import safety
    - Classifier-dependent metrics computed in runner.py, not MetricRegistry
    - Backward compatible optional parameter pattern (metric_registry=None)

key-files:
  created:
    - services/blue-agent/src/blue_agent/evaluation/__init__.py
    - services/blue-agent/src/blue_agent/evaluation/runner.py
    - services/blue-agent/src/blue_agent/evaluation/statistics.py
    - services/blue-agent/tests/test_evaluation.py
  modified:
    - services/blue-agent/src/blue_agent/isolation.py
    - services/blue-agent/pyproject.toml

key-decisions:
  - "Classifier-dependent derived metrics live in MultiSeedEvaluator._compute_classifier_derived(), not in MetricRegistry — they depend on EvaluationResult.classification data rather than MetricScore lists"
  - "BlueAgentEvaluator accepts optional MetricRegistry with backward-compatible default None — consumer doesn't need metric scoring"
  - "BCa bootstrap via scipy.stats.bootstrap with minimum 3 seeds enforced, 5 seeds recommended with log warning"
  - "Default seeds: [42, 123, 456, 789, 1011] — 5 seeds for reasonable CIs"

duration: 7 min
completed: 2026-05-17
---

# Phase 3 Plan 4: Multi-Seed Evaluation Engine Summary

**BCa bootstrap confidence intervals for multi-seed evaluation, classifier-dependent derived metrics, and MetricRegistry integration into BlueAgentEvaluator**

## Performance

- **Duration:** 7 min
- **Started:** 2026-05-17T04:57:32Z
- **Completed:** 2026-05-17T05:04:25Z
- **Tasks:** 2 (2 committed)
- **Files modified:** 6

## Accomplishments

- BCa bootstrap `compute_confidence_intervals()` using scipy with configurable confidence level and n_resamples
- `compute_statistics()` returning mean, std, median, min, max, ci_low, ci_high, n_seeds in a single dict
- `MultiSeedEvaluator` class that orchestrates classification + metric scoring across multiple random seeds
- Classifier-dependent derived metrics computed from EvaluationResult data: harm_classification_confidence, toxigen_confidence, ensemble_agreement
- Default 5 seeds [42, 123, 456, 789, 1011] with 3-seed minimum enforcement
- BlueAgentEvaluator updated with optional `metric_registry` parameter, backward compatible (empty metric_scores when absent)
- 25 new tests covering BCa CIs, compute_statistics, MultiSeedEvaluator orchestration, and BlueAgentEvaluator integration

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement BCa bootstrap statistics and multi-seed evaluator** - `c76ce05` (feat)
2. **Task 2: Integrate MetricRegistry into BlueAgentEvaluator and write evaluation tests** - `6d0d586` (feat)

## Files Created/Modified

- `services/blue-agent/src/blue_agent/evaluation/__init__.py` - Package init exporting MultiSeedEvaluator, compute_confidence_intervals, compute_statistics
- `services/blue-agent/src/blue_agent/evaluation/statistics.py` - BCa bootstrap + descriptive statistics functions
- `services/blue-agent/src/blue_agent/evaluation/runner.py` - MultiSeedEvaluator orchestrator with classifier-derived metrics
- `services/blue-agent/src/blue_agent/isolation.py` - BlueAgentEvaluator updated with optional metric_registry parameter
- `services/blue-agent/pyproject.toml` - Added scipy>=1.14 dependency
- `services/blue-agent/tests/test_evaluation.py` - 25 tests for statistics, MultiSeedEvaluator, and BlueAgentEvaluator integration

## Decisions Made

- **Classifier-derived metrics in runner.py, not MetricRegistry**: Metrics like `harm_classification_confidence` depend on `EvaluationResult.classification` data (label, confidence, model_source), not on `MetricScore` lists. They logically belong in the evaluation runner alongside the classification results.
- **Optional MetricRegistry with None default**: Keeps BlueAgentEvaluator backward compatible. Consumers that only need classification (no metrics) don't need to provide a registry.
- **BCa bootstrap via scipy**: Uses `scipy.stats.bootstrap(method="BCa")` instead of manual implementation — battle-tested, numerically stable.
- **Default 5 seeds**: [42, 123, 456, 789, 1011] provides reasonable CI widths. Warning logged below 5.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Mypy found 4 missing type-arg annotations in runner.py (list[dict], list without type args) — fixed with explicit `list[dict[str, Any]]` and `list[Any]` annotations.
- Ruff TC001 rule required moving `SafetyClassifier` import into TYPE_CHECKING block in isolation.py since `from __future__ import annotations` makes it a string annotation.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- BLUE-06 satisfied: multi-seed evaluation with BCa bootstrap confidence intervals
- Classifier-dependent derived metrics computed in MultiSeedEvaluator
- All 63 blue-agent tests pass (38 existing + 25 new)
- Ready for Phase 4 (orchestrator integration) when evaluation engine is consumed by the main pipeline

## Self-Check: PASSED

- [x] All 6 files exist on disk
- [x] Both commits present in git history
- [x] 63 tests collected (38 existing + 25 new)
- [x] BCa CIs return valid intervals, < 3 seeds raises ValueError
- [x] classifier_derived section in MultiSeedEvaluator output
- [x] BlueAgentEvaluator accepts optional metric_registry parameter
- [x] Backward compatible: works without metric_registry (empty metric_scores)
- [x] ruff and mypy pass on all evaluation module files

---
*Phase: 03-evaluation-engine*
*Completed: 2026-05-17*
