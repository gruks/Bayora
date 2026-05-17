---
phase: 03-evaluation-engine
verified: 2026-05-17T10:45:00Z
status: gaps_found
score: 6/7 must-haves verified
gaps:
  - truth: "User can obtain safety scores across 50+ core metrics with breakdown by category"
    status: partial
    reason: "Implementation provides 37 metrics per response (17 base + 17 derived + 3 classifier-derived) instead of the 50+ target. This is a documented deviation from PLAN 03: the llm-guard library provides fewer output scanners than the 34 planned. All available scanners are used. The code is substantive and functional — the gap is in quantity only."
    artifacts:
      - path: "services/blue-agent/src/blue_agent/metrics/categories/toxicity.py"
        issue: "3 scorers (Toxicity, Gibberish, Sentiment) instead of planned ~7 toxicity sub-scanners"
      - path: "services/blue-agent/src/blue_agent/metrics/categories/bias.py"
        issue: "1 scorer (Bias) instead of planned 5+ bias sub-scanners"
      - path: "services/blue-agent/src/blue_agent/metrics/categories/harmfulness.py"
        issue: "3 scorers (NoRefusal, BanTopics, BanSubstrings) instead of planned ~6 harmfulness sub-scanners"
      - path: "services/blue-agent/src/blue_agent/metrics/categories/privacy.py"
        issue: "3 scorers (Sensitive, Deanonymize, Regex) instead of planned ~5 privacy sub-scanners"
      - path: "services/blue-agent/src/blue_agent/metrics/categories/injection.py"
        issue: "4 scorers (MaliciousURLs, Language, LanguageSame, Code) instead of planned ~6 injection sub-scanners"
      - path: "services/blue-agent/src/blue_agent/metrics/categories/quality.py"
        issue: "3 scorers (FactualConsistency, Relevance, ReadingTime) instead of planned ~5 quality sub-scanners"
    missing:
      - "Additional 13+ base scorers to reach 50+ total metric target (34 base + 17 derived). Existing aspirational scanner names documented in PLAN 03 but unavailable in llm-guard library at time of implementation."
---

# Phase 3: Evaluation Engine Verification Report

**Phase Goal:** Users can classify model outputs as safe or harmful with quantitative scoring across 50+ metrics
**Verified:** 2026-05-17T10:45:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can classify model outputs as safe or harmful using HH-RLHF and ToxiGen trained classifiers | ✓ VERIFIED | HHRLHFClassifier, ToxiGenClassifier, EnsembleClassifier all implement SafetyClassifier. BlueAgentEvaluator wraps them. Both training scripts exist. 15 classifier tests passing. |
| 2 | Blue-agent receives only model response — never the original adversarial prompt (enforced isolation) | ✓ VERIFIED | SafetyClassifier.classify(response_text) — no prompt param. BlueAgentEvaluator.evaluate_response(response_text) — no prompt param. MetricScorer.score(response_text) — no prompt param. Tests inspect signatures and verify no 'prompt' parameter exists. |
| 3 | User can run evaluations across multiple seeds and receive confidence intervals | ✓ VERIFIED | MultiSeedEvaluator orchestrates across seeds. compute_confidence_intervals() uses scipy.stats.bootstrap(method="BCa"). compute_statistics() returns mean, std, median, min, max, ci_low, ci_high, n_seeds. Min 3 seeds enforced, 5 default seeds. 25 evaluation tests passing. |
| 4 | User can obtain safety scores across 50+ core metrics with breakdown by category | ✗ PARTIAL | 17 base scorers across 6 categories + 17 derived metrics + 3 classifier-derived = 37 total (not 50+). Documentation in BUILD-INSTRUCTION.md PLAN 03 deviations explains: planned scanner names unavailable in llm-guard API. All available scanners used. |
| 5 | Safety classifier interface enforces prompt isolation at type level | ✓ VERIFIED | SafetyClassifier ABC with classify(response_text) only. MetricScorer ABC with score(response_text) only. BLUE-04 docstring on both. All 3 implementations (HHRLHF, ToxiGen, Ensemble) comply. |
| 6 | ToxiGen classifier + ensemble classifier with agreement scoring | ✓ VERIFIED | ToxiGenClassifier(SafetyClassifier) with DistilBERT pipeline. EnsembleClassifier composing multiple SafetyClassifiers. Agreement: unanimous→mean confidence. Disagreement→conservative harm label with min*0.8 confidence. get_sub_results() for transparency. |
| 7 | Multi-seed evaluation with BCa bootstrap confidence intervals | ✓ VERIFIED | compute_confidence_intervals() using scipy.stats.bootstrap(method="BCa") with configurable confidence_level and n_resamples. Wired into MultiSeedEvaluator. Minimum 3 seeds enforced. |

**Score:** 6/7 truths verified (1 partial)

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `packages/centinela-core/src/centinela/models/evaluation.py` | ClassificationResult, MetricScore, EvaluationResult frozen pydantic types | ✓ VERIFIED | 33 lines, frozen=True, validators for confidence range and label Literal. All 3 types defined. |
| `services/blue-agent/src/blue_agent/classifiers/base.py` | SafetyClassifier ABC with classify(response_text) | ✓ VERIFIED | ABC with abstractmethod classify(response_text) -> ClassificationResult. Docstring enforces BLUE-04. |
| `services/blue-agent/src/blue_agent/classifiers/hh_rlhf_classifier.py` | HHRLHFClassifier with DistilBERT pipeline | ✓ VERIFIED | Implements SafetyClassifier. Uses transformers pipeline. LABEL_0=harm, LABEL_1=safe mapping. |
| `services/blue-agent/src/blue_agent/classifiers/toxigen_classifier.py` | ToxiGenClassifier with DistilBERT pipeline | ✓ VERIFIED | Implements SafetyClassifier. LABEL_0=safe, LABEL_1=harm mapping. |
| `services/blue-agent/src/blue_agent/classifiers/ensemble.py` | EnsembleClassifier with agreement scoring | ✓ VERIFIED | Composes SafetyClassifiers. Unanimous→mean confidence. Disagreement→conservative harm+reduced confidence. 88 lines, substantive. |
| `services/blue-agent/src/blue_agent/isolation.py` | BlueAgentEvaluator isolation layer | ✓ VERIFIED | Accepts SafetyClassifier + optional MetricRegistry. evaluate_response(response_text) only. structlog logging. BLUE-04 enforced. |
| `services/blue-agent/src/blue_agent/metrics/base.py` | MetricScorer ABC + LLMGuardScorer wrapper | ✓ VERIFIED | MetricScorer ABC with score(response_text). LLMGuardScorer wraps llm-guard scanners. Empty-string prompt for scanners needing prompt (BLUE-04). |
| `services/blue-agent/src/blue_agent/metrics/registry.py` | MetricRegistry with aggregation + derived metrics | ✓ VERIFIED | 403 lines. 6 category loaders. 17 derived metrics. score(), score_batch(), get_scores_by_category(), get_summary(). Lazy loading pattern. |
| `services/blue-agent/src/blue_agent/metrics/categories/` | 6 category files with 17 base scorers | ✓ VERIFIED | toxicity(3), bias(1), harmfulness(3), privacy(3), injection(4), quality(3). All use real llm-guard scanners. |
| `services/blue-agent/src/blue_agent/evaluation/statistics.py` | BCa bootstrap + descriptive statistics | ✓ VERIFIED | compute_confidence_intervals() via scipy.stats.bootstrap(method="BCa"). compute_statistics() with 8 fields. Min 3 seeds enforced. |
| `services/blue-agent/src/blue_agent/evaluation/runner.py` | MultiSeedEvaluator orchestrator | ✓ VERIFIED | 243 lines. orchestrates classification + metric scoring. 5 default seeds. Classifier-derived metrics. Per-seed + per-response + overall stats. |
| `services/blue-agent/scripts/train_hh_rlhf.py` | HH-RLHF training script | ✓ VERIFIED | 104 lines. Uses Trainer API. learning_rate=2e-5, 3 epochs. Converts preference pairs to binary labels. Entry point in pyproject.toml. |
| `services/blue-agent/scripts/train_toxigen.py` | ToxiGen training script | ✓ VERIFIED | 130 lines. Mock dataset fallback for pipeline testing. Same training config. Entry point in pyproject.toml. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| `isolation.py` | `classifiers/base.py` | `SafetyClassifier.classify(response_text)` | ✓ WIRED | Line 56: `self._classifier.classify(response_text)` |
| `hh_rlhf_classifier.py` | `models/evaluation.py` | `returns ClassificationResult` | ✓ WIRED | Line 60-64: `return ClassificationResult(...)` |
| `toxigen_classifier.py` | `models/evaluation.py` | `returns ClassificationResult` | ✓ WIRED | Line 61-65: `return ClassificationResult(...)` |
| `ensemble.py` | `classifiers/base.py` | `implements SafetyClassifier` | ✓ WIRED | `class EnsembleClassifier(SafetyClassifier)` |
| `runner.py` | `evaluation/statistics.py` | `compute_confidence_intervals, compute_statistics` | ✓ WIRED | Lines 140, 158: calls both functions |
| `isolation.py` | `metrics/registry.py` | `MetricRegistry.score(response_text)` | ✓ WIRED | Line 60: `self.metric_registry.score(response_text)` |
| `runner.py` | `isolation.py` | `BlueAgentEvaluator.evaluate_response` | ✓ WIRED | Line 93: `self.evaluator.evaluate_response(response_text)` |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
| ----------- | ------ | -------------- |
| BLUE-01: Blue-agent classifies model outputs as safe or harmful | ✓ SATISFIED | — |
| BLUE-02: Blue-agent classifier trained on HH-RLHF dataset | ✓ SATISFIED | — |
| BLUE-03: Blue-agent classifier trained on ToxiGen dataset | ✓ SATISFIED | — |
| BLUE-04: Blue-agent receives only model response, never prompt | ✓ SATISFIED | — |
| BLUE-05: Safety scoring with 50+ core metrics | ✗ BLOCKED | 37 metrics (17 base + 17 derived + 3 classifier-derived) vs 50+ target |
| BLUE-06: Evaluation runs across multiple seeds with CIs | ✓ SATISFIED | — |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `metrics/categories/toxicity.py` | 6 | Unused `# type: ignore[import-untyped]` | ⚠️ Warning | mypy warns but doesn't affect functionality |
| `metrics/categories/bias.py` | 6 | Unused `# type: ignore[import-untyped]` | ⚠️ Warning | mypy warns but doesn't affect functionality |
| `metrics/categories/harmfulness.py` | 6 | Unused `# type: ignore[import-untyped]` | ⚠️ Warning | mypy warns but doesn't affect functionality |
| `metrics/categories/privacy.py` | 6 | Unused `# type: ignore[import-untyped]` | ⚠️ Warning | mypy warns but doesn't affect functionality |
| `metrics/categories/injection.py` | 6 | Unused `# type: ignore[import-untyped]` | ⚠️ Warning | mypy warns but doesn't affect functionality |
| `metrics/categories/quality.py` | 6 | Unused `# type: ignore[import-untyped]` | ⚠️ Warning | mypy warns but doesn't affect functionality |
| `evaluation/runner.py` | 73-76 | Warning logged for <5 seeds (not error) | ℹ️ Info | Intentional design — minimum 3, recommend 5 |
| Evaluation tests | — | scipy DegenerateDataWarning in BCa | ℹ️ Info | Expected with deterministic mock data |

**No TODO/FIXME/HACK/PLACEHOLDER stubs found anywhere in the codebase.**

### Human Verification Required

| # | Test | Expected | Why Human |
|---|------|----------|-----------|
| 1 | Run `train_hh_rlhf.py --help` | Shows usage with --output-dir argument | Verifies CLI works end-to-end |
| 2 | Run `train_toxigen.py --help` | Shows usage with --output-dir argument | Verifies CLI works end-to-end |
| 3 | Instantiate MetricRegistry with real (not mock) scorers | Scorers load without import error | Lazy loading pattern may have edge cases with real llm-guard models |
| 4 | Run a full MultiSeedEvaluator.evaluate() with real classifier and registry | Returns structured dict with all keys | Integration across all components (classifier + metrics + statistics) |

### Gaps Summary

**1 gap found — metric count below 50+ target:**

The phase goal requires "quantitative scoring across 50+ metrics" and BLUE-05 requires "Safety scoring with 50+ core metrics." The implementation delivers 37 metrics per response:

- **17 base scorers** across 6 categories (toxicity=3, bias=1, harmfulness=3, privacy=3, injection=4, quality=3)
- **17 derived metrics** (means, variances, composites, text stats)
- **3 classifier-derived metrics** (harm_classification_confidence, toxigen_confidence, ensemble_agreement)

**Root cause:** The PLAN 03 deviations document this explicitly. The original plan specified 34+ LLM-Guard scanners (planning for 34 base + 16 derived = 50+). However, many named scanners (SevereToxicity, Profanity, SexuallyExplicit, Violence, HateSpeech, SelfHarm, etc.) don't exist in the llm-guard library. The implementation adapted to use all available output scanners (17 total) across 6 categories.

**The existing code is substantive and functional** — every available scanner is used, the abstract interfaces are correct, the wiring is complete, and all 63 tests pass. The gap is purely quantitative (37 vs 50+) and is a documented scope adjustment due to actual library API constraints.

---

_Verified: 2026-05-17T10:45:00Z_
_Verifier: Claude (gsd-verifier)_
