"""Quality category metric scorers.

Wraps LLM-Guard output scanners that assess response quality.
"""

from llm_guard.output_scanners import (
    FactualConsistency,
    ReadingTime,
    Relevance,
)

from blue_agent.metrics.base import LLMGuardScorer

QUALITY_SCORERS: list[LLMGuardScorer] = [
    LLMGuardScorer(
        name="factual_consistency",
        category="quality",
        scanner=FactualConsistency(),
        threshold=0.5,
    ),
    LLMGuardScorer(
        name="relevance",
        category="quality",
        scanner=Relevance(),
        threshold=0.5,
    ),
    LLMGuardScorer(
        name="reading_time",
        category="quality",
        scanner=ReadingTime(max_time=5),
        threshold=0.5,
    ),
]
