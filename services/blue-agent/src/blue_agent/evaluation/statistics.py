"""Statistical functions for multi-seed evaluation analysis.

Provides BCa bootstrap confidence interval computation and
descriptive statistics for per-seed score aggregation.
"""

import numpy as np
from scipy import stats


def compute_confidence_intervals(
    per_seed_scores: list[float],
    confidence_level: float = 0.95,
    n_resamples: int = 10000,
) -> tuple[float, float]:
    """Compute BCa bootstrap confidence intervals for a list of scores.

    Args:
        per_seed_scores: List of metric scores from different seeds.
        confidence_level: Confidence level for the interval (default 0.95).
        n_resamples: Number of bootstrap resamples (default 10000).

    Returns:
        Tuple of (ci_low, ci_high) representing the confidence interval.

    Raises:
        ValueError: If fewer than 3 seeds are provided.
    """
    if len(per_seed_scores) < 3:
        raise ValueError("Minimum 3 seeds required for BCa bootstrap")

    result = stats.bootstrap(
        (np.asarray(per_seed_scores),),
        statistic=np.mean,
        confidence_level=confidence_level,
        n_resamples=n_resamples,
        method="BCa",
    )

    return (float(result.confidence_interval.low), float(result.confidence_interval.high))


def compute_statistics(per_seed_scores: list[float]) -> dict[str, float]:
    """Compute descriptive statistics for per-seed scores.

    Args:
        per_seed_scores: List of metric scores from different seeds.

    Returns:
        Dict with mean, std, median, min, max, ci_low, ci_high, n_seeds.
    """
    mean_val = float(np.mean(per_seed_scores))
    std_val = float(np.std(per_seed_scores))
    median_val = float(np.median(per_seed_scores))
    min_val = float(np.min(per_seed_scores))
    max_val = float(np.max(per_seed_scores))

    ci_low, ci_high = compute_confidence_intervals(per_seed_scores)

    return {
        "mean": mean_val,
        "std": std_val,
        "median": median_val,
        "min": min_val,
        "max": max_val,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "n_seeds": len(per_seed_scores),
    }
