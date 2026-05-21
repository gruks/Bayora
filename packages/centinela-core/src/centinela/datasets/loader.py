"""Dataset loader with caching, integrity verification, and registration.

Provides centralized management for all dataset downloads and caching.
"""

import hashlib
import json
import shutil
from pathlib import Path

import requests
from tqdm import tqdm

from centinela.datasets.base import DEFAULT_CACHE_DIR, Dataset
from centinela.datasets.types import DatasetEntry

_MANIFEST_FILE = ".manifest.json"


class DatasetLoader:
    """Manages dataset registration, loading, and caching."""

    def __init__(self, cache_dir: Path = DEFAULT_CACHE_DIR) -> None:
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._registry: dict[str, type[Dataset]] = {}
        self._manifest = self._load_manifest()

    def register_dataset(self, name: str, dataset_cls: type[Dataset]) -> None:
        """Register a dataset class for loading by name."""
        self._registry[name] = dataset_cls

    def load_dataset(self, name: str, force_download: bool = False) -> Dataset:
        """Load a registered dataset by name."""
        if name not in self._registry:
            raise ValueError(f"Dataset '{name}' not registered. Available: {list(self._registry.keys())}")

        dataset = self._registry[name]()
        dataset.load(self._cache_dir, force_download)

        cached_file = self._cache_dir / f"{dataset.name}-{dataset.version}"
        if cached_file.exists():
            self._update_manifest(name, dataset)

        return dataset

    def list_datasets(self) -> list[str]:
        """Return list of registered dataset names."""
        return list(self._registry.keys())

    def clear_cache(self, name: str | None = None) -> None:
        """Clear cache for specific dataset or all datasets."""
        if name is not None:
            if name in self._registry:
                dataset = self._registry[name]()
                dataset_dir = self._cache_dir / f"{dataset.name}-{dataset.version}"
                if dataset_dir.exists():
                    shutil.rmtree(dataset_dir)
                self._manifest.pop(name, None)
        else:
            for item in self._cache_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
            self._manifest.clear()
        self._save_manifest()

    def _load_manifest(self) -> dict:
        manifest_path = self._cache_dir / _MANIFEST_FILE
        if manifest_path.exists():
            with open(manifest_path) as f:
                return json.load(f)
        return {}

    def _save_manifest(self) -> None:
        manifest_path = self._cache_dir / _MANIFEST_FILE
        with open(manifest_path, "w") as f:
            json.dump(self._manifest, f, indent=2, default=str)

    def _update_manifest(self, name: str, dataset: Dataset) -> None:
        dataset_dir = self._cache_dir / f"{dataset.name}-{dataset.version}"
        file_hash = None
        entry_count = len(dataset)

        if dataset_dir.exists():
            for item in dataset_dir.iterdir():
                if item.is_file():
                    file_hash = compute_hash(item)
                    break

        self._manifest[name] = {
            "version": dataset.version,
            "download_date": str(dataset._entries[0].created_at) if dataset._entries else None,
            "file_hash": file_hash,
            "entry_count": entry_count,
        }
        self._save_manifest()


def download_file(url: str, dest: Path, progress: bool = True) -> Path:
    """Download file from URL with optional progress bar."""
    dest.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, stream=True, timeout=120)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))

    with open(dest, "wb") as f:
        if progress and total_size > 0:
            with tqdm(total=total_size, unit="B", unit_scale=True, desc=dest.name) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))
        else:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    return dest


def compute_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def verify_hash(file_path: Path, expected_hash: str) -> bool:
    """Verify SHA-256 hash of file matches expected."""
    return compute_hash(file_path) == expected_hash
