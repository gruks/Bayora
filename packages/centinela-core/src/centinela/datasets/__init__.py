"""Dataset management for adversarial testing.

Provides unified dataset types, loading, and caching for red-team and blue-team operations.
"""

from centinela.datasets.advbench import AdvBenchDataset
from centinela.datasets.base import DEFAULT_CACHE_DIR, Dataset
from centinela.datasets.gandalf import GandalfDataset
from centinela.datasets.jailbreakbench import JailbreakBenchDataset
from centinela.datasets.loader import DatasetLoader, compute_hash, download_file, verify_hash
from centinela.datasets.types import DatasetCategory, DatasetEntry, DatasetMetadata

__all__ = [
    "DEFAULT_CACHE_DIR",
    "Dataset",
    "DatasetLoader",
    "AdvBenchDataset",
    "JailbreakBenchDataset",
    "GandalfDataset",
    "DatasetCategory",
    "DatasetEntry",
    "DatasetMetadata",
    "compute_hash",
    "download_file",
    "verify_hash",
]
