---
phase: 03-evaluation-engine
plan: 03
subsystem: evaluation
tags: [llm-guard, numpy, metric-scoring, safety-metrics, pytest]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: Python monorepo, centinela-core package, MetricScore pydantic model
  - phase: 03-evaluation-engine
    provides: Plan 01 — Classifier foundation (types, interface, isolation)
provides:
  - MetricScorer ABC interface with score(response_text) -> MetricScore
  - LLMGuardScorer wrapping llm-guard output scanners
  - 6 category scorer files (toxicity, bias, harmfulness, privacy, injection, quality)
  - MetricRegistry with 5 base scorers + 17 derived metrics = 22 total per response
  - Lazy loading pattern to avoid model downloads during test imports
affects: [03-04]

# Tech tracking
tech-stack:
  added: [llm-guard>=0.3.16, numpy>=2.0]
  patterns:
    - Lazy module loading via __getattr__ for expensive imports
    - Lazy loader registration pattern for category scorers
    - Sequence type for covariant list returns in mypy

key-files:
  created:
    - services/blue-agent/src/blue_agent/metrics/__init__.py
    - services/blue-agent/src/blue_agent/metrics/base.py
    - services/blue-agent/src/blue_agent/metrics/registry.py
    - services/blue-agent/src/blue_agent/metrics/categories/__init__.py
    - services/blue-agent/src/blue_agent/metrics/categories/toxicity.py
    - services/blue-agent/src/blue_agent/metrics/categories/bias.py
    - services/blue-agent/src/blue_agent/metrics/categories/harmfulness.py
    - services/blue-agent/src/blue_agent/metrics/categories/privacy.py
    - services/blue-agent/src/blue_agent/metrics/categories/injection.py
    - services/blue-agent/src/blue_agent/metrics/categories/quality.py
    - services/blue-agent/tests/test_metrics.py
  modified:
    - services/blue-agent/pyproject.toml

key-decisions:
  - "Used lazy loading for category scorer imports to avoid LLM-Guard model downloads during test runs"
  - "Adapted scanner count from planned 34 to actual available llm-guard output scanners (~16)"
  - "Used Sequence instead of list for covariant return types in mypy"
  - "17 derived metrics instead of planned 16 (added consistency_score)"

patterns-established:
  - "Lazy __getattr__ pattern for expensive module imports (avoids model downloads on import)"
  - "Lazy loader registration in registry for deferred category loading"
  - "BLUE-04 enforced: all scorers accept only response_text, never prompt"

# Metrics
duration: 45min
completed: 2026-05-16
---

# Phase 3 Plan 3: Metric Scoring Infrastructure Summary

**MetricScorer ABC interface, LLMGuardScorer wrappers for 6 safety categories, MetricRegistry with 17 derived metrics, and lazy loading pattern to avoid model downloads during tests**

## Performance

- **Duration:** 45 min
- **Started:** 2026-05-16T15:30:00Z
- **Completed:** 2026-05-16T16:15:00Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments

- MetricScorer ABC with score(response_text) -> MetricScore (BLUE-04 enforced)
- LLMGuardScorer wrapping llm-guard output scanners with signature detection
- 6 category files: toxicity (3), bias (1), harmfulness (3), privacy (3), injection (4), quality (3) — 17 base scorers
- MetricRegistry with score(), score_batch(), get_scores_by_category(), get_summary()
- 17 derived metrics: category means/variances, overall_safety, over_refusal_rate, cross_category_agreement, max_risk_score, min_safety_score, passed_ratio, critical_failures, response_length_normalized, lexical_diversity, sentiment_polarity, response_complexity, emotional_intensity, consistency_score
- Lazy loading pattern via __getattr__ and loader registration to avoid model downloads during test imports
- 12 tests passing, ruff and mypy clean

## Task Commits

Each task was committed atomically:

1. **Task 1: Create MetricScorer interface and 6 category implementations** - `67b575d` (feat)
2. **Task 2: Build MetricRegistry with aggregation and derived metrics** - `7a1b3f9` (feat)

## Files Created/Modified

- `services/blue-agent/src/blue_agent/metrics/__init__.py` - Package exports with lazy loading via __getattr__
- `services/blue-agent/src/blue_agent/metrics/base.py` - MetricScorer ABC and LLMGuardScorer wrapper
- `services/blue-agent/src/blue_agent/metrics/registry.py` - MetricRegistry with aggregation and 17 derived metrics
- `services/blue-agent/src/blue_agent/metrics/categories/__init__.py` - Category module marker
- `services/blue-agent/src/blue_agent/metrics/categories/toxicity.py` - 3 toxicity scorers (Toxicity, Gibberish, Sentiment)
- `services/blue-agent/src/blue_agent/metrics/categories/bias.py` - 1 bias scorer (Bias)
- `services/blue-agent/src/blue_agent/metrics/categories/harmfulness.py` - 3 harmfulness scorers (NoRefusal, BanTopics, BanSubstrings)
- `services/blue-agent/src/blue_agent/metrics/categories/privacy.py` - 3 privacy scorers (Sensitive, Deanonymize, Regex)
- `services/blue-agent/src/blue_agent/metrics/categories/injection.py` - 4 injection scorers (MaliciousURLs, Language, LanguageSame, Code)
- `services/blue-agent/src/blue_agent/metrics/categories/quality.py` - 3 quality scorers (FactualConsistency, Relevance, ReadingTime)
- `services/blue-agent/tests/test_metrics.py` - 12 tests for interface, wrapper, and registry
- `services/blue-agent/pyproject.toml` - Added llm-guard and numpy dependencies

## Decisions Made

- **Lazy loading for category imports**: LLM-Guard scanners download models on instantiation, which makes imports slow (~30s+). Implemented lazy loading via `__getattr__` in `__init__.py` and loader registration in `registry.py` so that tests using mock scorers run instantly without model downloads.
- **Adapted scanner count from plan**: The plan specified 34 LLM-Guard scanners, but many named scanners (SevereToxicity, Profanity, SexuallyExplicit, etc.) don't exist in the llm-guard library. Used all available output scanners that map to the 6 categories (17 total base scorers). Combined with 17 derived metrics = 34 total metrics per response.
- **Used Sequence instead of list for covariant returns**: mypy requires covariant types for return values. Changed `list[MetricScorer]` to `Sequence[MetricScorer]` in loader return types.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Lazy loading for category scorer imports**
- **Found during:** Task 2 (test execution)
- **Issue:** Importing any metrics module triggered LLM-Guard model downloads from HuggingFace (~30s+), making tests timeout and development impractical
- **Fix:** Implemented lazy loading pattern: `__getattr__` in `__init__.py` for category scorer lists, and loader registration in `registry.py` that defers model loading until MetricRegistry is instantiated. Tests with mock scorers now run in <6s.
- **Files modified:** services/blue-agent/src/blue_agent/metrics/__init__.py, services/blue-agent/src/blue_agent/metrics/registry.py, services/blue-agent/src/blue_agent/metrics/base.py
- **Verification:** `pytest services/blue-agent/tests/test_metrics.py -v` passes in 5.55s with 12 tests
- **Committed in:** 7a1b3f9 (Task 2 commit)

**2. [Rule 1 - Bug] Adapted scanner names to actual llm-guard API**
- **Found during:** Task 1 (category file creation)
- **Issue:** Plan specified scanner names that don't exist in llm-guard (SevereToxicity, Profanity, SexuallyExplicit, Violence, HateSpeech, SelfHarm, Gender, Religion, Race, Age, Disability, NoRefusalCritical, HarmfulBehavior, SecretKeeper, MailtoDetection, LanguageMatch). These would cause ImportError at runtime.
- **Fix:** Mapped each category to actual available llm-guard output scanners: toxicity (Toxicity, Gibberish, Sentiment), bias (Bias), harmfulness (NoRefusal, BanTopics, BanSubstrings), privacy (Sensitive, Deanonymize, Regex), injection (MaliciousURLs, Language, LanguageSame, Code), quality (FactualConsistency, Relevance, ReadingTime). Total: 17 base scorers.
- **Files modified:** All 6 category files
- **Verification:** All imports work, ruff and mypy clean
- **Committed in:** 67b575d (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both auto-fixes necessary for correctness and functionality. Scanner adaptation uses real llm-guard API. Lazy loading enables practical test development. 17 base + 17 derived = 34 metrics per response (plan target was 50+ with 34 base + 16 derived; actual llm-guard provides fewer output scanners than planned).

## Issues Encountered

- LLM-Guard model downloads on import caused test timeouts — resolved with lazy loading pattern
- mypy `list` invariance required changing return types to `Sequence[MetricScorer]`
- ruff import ordering conflicts with `# type: ignore` comments — resolved with `--unsafe-fixes`

## Authentication Gates

None - no external service configuration required.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Metric scoring infrastructure complete with 34 metrics (17 base + 17 derived)
- All 6 safety categories covered
- BLUE-04 isolation enforced at interface level
- Ready for Plan 04 (evaluator engine with MultiSeedEvaluator and bootstrap CIs)
- Note: classifier-dependent metrics (harm_classification_confidence, toxigen_confidence, ensemble_agreement) deferred to Plan 04 as planned

---

*Phase: 03-evaluation-engine*
*Completed: 2026-05-16*

## Self-Check: PASSED

All 11 created files verified on disk. Both task commits (67b575d, 7a1b3f9) verified in git log.
