"""Abstract base class for dataset implementations.

All dataset downloaders (AdvBench, JailbreakBench, Gandalf, etc.) must subclass
Dataset and implement _download() and _parse().
"""

from abc import ABC, abstractmethod
from pathlib import Path
from random import Random

from centinela.datasets.types import DatasetCategory, DatasetEntry, DatasetMetadata

DEFAULT_CACHE_DIR = Path.home() / ".centinela" / "datasets"


class Dataset(ABC):
    """Base class for adversarial/training datasets.

    Subclasses must implement:
    - _download(): fetch raw data from source
    - _parse(): convert raw data to DatasetEntry list
    """

    name: str = "base"
    version: str = "0.1.0"

    def __init__(self) -> None:
        self._entries: list[DatasetEntry] = []

    @abstractmethod
    def _download(self, dest_dir: Path) -> Path:
        """Download dataset to dest_dir.

        Returns path to downloaded file or directory.
        """

    @abstractmethod
    def _parse(self, raw_path: Path) -> list[DatasetEntry]:
        """Parse raw dataset file(s) into DatasetEntry list."""

    def load(
        self,
        cache_dir: Path = DEFAULT_CACHE_DIR,
        force_download: bool = False,
    ) -> list[DatasetEntry]:
        """Load dataset from cache or download if missing."""
        cache_dir.mkdir(parents=True, exist_ok=True)
        dataset_dir = cache_dir / f"{self.name}-{self.version}"

        if force_download or not dataset_dir.exists():
            if dataset_dir.exists():
                import shutil

                shutil.rmtree(dataset_dir)
            raw_path = self._download(dataset_dir)
            self._entries = self._parse(raw_path)
        else:
            cached_file = self._find_cached_file(dataset_dir)
            if cached_file:
                self._entries = self._parse(cached_file)
            else:
                raw_path = self._download(dataset_dir)
                self._entries = self._parse(raw_path)

        return self._entries

    def _find_cached_file(self, dataset_dir: Path) -> Path | None:
        """Find first file in cached directory."""
        if not dataset_dir.exists():
            return None
        for item in dataset_dir.iterdir():
            if item.is_file():
                return item
        return None

    def filter(
        self,
        category: DatasetCategory | None = None,
        label: str | None = None,
    ) -> list[DatasetEntry]:
        """Filter entries by category and/or label."""
        results = self._entries
        if category is not None:
            results = [e for e in results if e.category == category]
        if label is not None:
            results = [e for e in results if e.label == label]
        return results

    def sample(self, n: int, seed: int | None = None) -> list[DatasetEntry]:
        """Random sample of n entries with optional seed."""
        rng = Random(seed)
        return rng.sample(self._entries, min(n, len(self._entries)))

    def get_stats(self) -> DatasetMetadata:
        """Compute and return dataset metadata."""
        categories = list({e.category for e in self._entries})
        return DatasetMetadata(
            name=self.name,
            version=self.version,
            source=self._get_source(),
            total_entries=len(self._entries),
            categories=categories,
            description=self._get_description(),
        )

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self):
        return iter(self._entries)

    def _get_source(self) -> str:
        return f"{self.name} v{self.version}"

    def _get_description(self) -> str:
        return f"{self.name} dataset v{self.version}"
