"""Anomaly detection module for centinela."""

from pydantic import BaseModel

from .detector import AnomalyDetector, anomaly_count


class AnomalyAlert(BaseModel):
    """Output alert for a detected anomaly."""

    metric_name: str
    value: float
    expected_mean: float
    std_dev: float
    z_score: float
    severity: str


__all__ = ["AnomalyAlert", "AnomalyDetector", "anomaly_count"]
