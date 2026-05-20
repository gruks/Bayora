"""Anomaly detection module using statistical baseline."""

import math
from typing import Any

from prometheus_client import Counter, Gauge

metric_value_gauge = Gauge(
    "centinela_metric_value", "Current value of a metric", ["metric_name"]
)
anomaly_count = Counter(
    "centinela_anomaly_count", "Number of detected anomalies", ["metric_name", "severity"]
)


class WelfordStat:
    """Running statistics using Welford's algorithm over a sliding window."""

    def __init__(self, window_size: int) -> None:
        self.window_size = window_size
        self.count = 0
        self.mean = 0.0
        self.m2 = 0.0
        self._min = float('inf')
        self._max = float('-inf')
        self.values: list[float] = []

    def update(self, value: float) -> None:
        """Update the running statistics."""
        self.values.append(value)
        if len(self.values) > self.window_size:
            self.values.pop(0)
            self.count = len(self.values)
            self.mean = sum(self.values) / self.count
            self.m2 = sum((x - self.mean) ** 2 for x in self.values)
            self._min = min(self.values)
            self._max = max(self.values)
            return

        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        delta2 = value - self.mean
        self.m2 += delta * delta2

        if value < self._min:
            self._min = value
        if value > self._max:
            self._max = value

    @property
    def variance(self) -> float:
        """Get the variance."""
        if self.count < 2:
            return 0.0
        return self.m2 / (self.count - 1)

    @property
    def std_dev(self) -> float:
        """Get the standard deviation."""
        return math.sqrt(self.variance)


class AnomalyDetector:
    """Anomaly detector with statistical tracking and thresholds."""

    def __init__(self, window_size: int = 100, threshold_sigma: float = 3.0) -> None:
        self.window_size = window_size
        self.threshold_sigma = threshold_sigma
        self._stats: dict[str, WelfordStat] = {}
        self._latest_values: dict[str, float] = {}

    def observe(self, metric_name: str, value: float) -> None:
        """Update baseline statistics with a new value."""
        if metric_name not in self._stats:
            self._stats[metric_name] = WelfordStat(self.window_size)

        self._stats[metric_name].update(value)
        self._latest_values[metric_name] = value
        metric_value_gauge.labels(metric_name=metric_name).set(value)

    def detect(self, metric_name: str) -> list[dict[str, Any]]:
        """Return anomalies if latest value exceeds threshold_sigma."""
        anomalies: list[dict[str, Any]] = []
        if metric_name not in self._stats or metric_name not in self._latest_values:
            return anomalies

        stat = self._stats[metric_name]
        if stat.count < 2:
            return anomalies

        latest = self._latest_values[metric_name]
        mean = stat.mean
        std = stat.std_dev

        if std > 0:
            z_score = abs(latest - mean) / std
            if z_score > self.threshold_sigma:
                severity = "high" if z_score > self.threshold_sigma * 1.5 else "medium"

                anomaly_count.labels(metric_name=metric_name, severity=severity).inc()

                anomalies.append({
                    "metric_name": metric_name,
                    "value": latest,
                    "expected_mean": mean,
                    "std_dev": std,
                    "z_score": z_score,
                    "severity": severity,
                })

        return anomalies

    def get_baseline(self, metric_name: str) -> dict[str, Any]:
        """Return mean, std, min, max for a metric."""
        if metric_name not in self._stats:
            return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}

        stat = self._stats[metric_name]
        return {
            "mean": stat.mean,
            "std": stat.std_dev,
            "min": stat._min if stat.count > 0 else 0.0,
            "max": stat._max if stat.count > 0 else 0.0,
        }
