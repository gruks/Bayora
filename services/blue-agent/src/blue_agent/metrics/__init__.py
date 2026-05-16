"""Metrics package for the blue-agent safety evaluation system.

Category scorer lists are loaded lazily to avoid downloading
LLM-Guard models during import. Use MetricRegistry for scoring.
"""

from collections.abc import Sequence

from blue_agent.metrics.base import LLMGuardScorer, MetricScorer

__all__ = [
    "LLMGuardScorer",
    "MetricScorer",
]


def _lazy_toxicity() -> Sequence[MetricScorer]:
    from blue_agent.metrics.categories.toxicity import TOXICITY_SCORERS

    return TOXICITY_SCORERS


def _lazy_bias() -> Sequence[MetricScorer]:
    from blue_agent.metrics.categories.bias import BIAS_SCORERS

    return BIAS_SCORERS


def _lazy_harmfulness() -> Sequence[MetricScorer]:
    from blue_agent.metrics.categories.harmfulness import HARMFULNESS_SCORERS

    return HARMFULNESS_SCORERS


def _lazy_privacy() -> Sequence[MetricScorer]:
    from blue_agent.metrics.categories.privacy import PRIVACY_SCORERS

    return PRIVACY_SCORERS


def _lazy_injection() -> Sequence[MetricScorer]:
    from blue_agent.metrics.categories.injection import INJECTION_SCORERS

    return INJECTION_SCORERS


def _lazy_quality() -> Sequence[MetricScorer]:
    from blue_agent.metrics.categories.quality import QUALITY_SCORERS

    return QUALITY_SCORERS


def __getattr__(name: str) -> Sequence[MetricScorer]:
    """Lazy-load category scorer lists on first access."""
    loaders = {
        "TOXICITY_SCORERS": _lazy_toxicity,
        "BIAS_SCORERS": _lazy_bias,
        "HARMFULNESS_SCORERS": _lazy_harmfulness,
        "PRIVACY_SCORERS": _lazy_privacy,
        "INJECTION_SCORERS": _lazy_injection,
        "QUALITY_SCORERS": _lazy_quality,
    }
    if name in loaders:
        return loaders[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
