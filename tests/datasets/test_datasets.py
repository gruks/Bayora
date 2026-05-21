"""Tests for the datasets module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from centinela.datasets import DatasetLoader, compute_hash, verify_hash
from centinela.datasets.base import Dataset
from centinela.datasets.types import DatasetCategory, DatasetEntry, DatasetMetadata


class TestDatasetEntry:
    def test_create_entry(self):
        entry = DatasetEntry(prompt="test prompt")
        assert entry.prompt == "test prompt"
        assert entry.label is None
        assert entry.category == DatasetCategory.GENERAL
        assert entry.severity == 0.5

    def test_entry_is_frozen(self):
        entry = DatasetEntry(prompt="test prompt")
        with pytest.raises(Exception):
            entry.prompt = "modified"

    def test_entry_with_all_fields(self):
        entry = DatasetEntry(
            prompt="test",
            label="harmful",
            category=DatasetCategory.VIOLENCE,
            severity=0.8,
            metadata={"source": "test"},
        )
        assert entry.label == "harmful"
        assert entry.category == DatasetCategory.VIOLENCE
        assert entry.severity == 0.8
        assert entry.metadata["source"] == "test"


class TestDatasetABC:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            Dataset()

    def test_concrete_implementation(self):
        class MockDataset(Dataset):
            name = "mock"
            version = "1.0.0"

            def _download(self, dest_dir: Path) -> Path:
                dest_dir.mkdir(parents=True, exist_ok=True)
                file_path = dest_dir / "data.json"
                file_path.write_text(json.dumps([{"prompt": "test"}]))
                return file_path

            def _parse(self, raw_path: Path) -> list[DatasetEntry]:
                data = json.loads(raw_path.read_text())
                return [DatasetEntry(prompt=item["prompt"]) for item in data]

        dataset = MockDataset()
        with tempfile.TemporaryDirectory() as tmpdir:
            entries = dataset.load(Path(tmpdir))
            assert len(entries) == 1
            assert entries[0].prompt == "test"

    def test_filter_by_category(self):
        class MockDataset(Dataset):
            name = "mock"
            version = "1.0.0"

            def _download(self, dest_dir: Path) -> Path:
                return dest_dir / "data.json"

            def _parse(self, raw_path: Path) -> list[DatasetEntry]:
                return [
                    DatasetEntry(prompt="v1", category=DatasetCategory.VIOLENCE, label="harmful"),
                    DatasetEntry(prompt="j1", category=DatasetCategory.JAILBREAK, label="jailbreak"),
                ]

        dataset = MockDataset()
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset.load(Path(tmpdir))
            violent = dataset.filter(category=DatasetCategory.VIOLENCE)
            assert len(violent) == 1
            assert violent[0].category == DatasetCategory.VIOLENCE

    def test_filter_by_label(self):
        class MockDataset(Dataset):
            name = "mock"
            version = "1.0.0"

            def _download(self, dest_dir: Path) -> Path:
                return dest_dir / "data.json"

            def _parse(self, raw_path: Path) -> list[DatasetEntry]:
                return [
                    DatasetEntry(prompt="p1", label="harmful"),
                    DatasetEntry(prompt="p2", label="safe"),
                ]

        dataset = MockDataset()
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset.load(Path(tmpdir))
            harmful = dataset.filter(label="harmful")
            assert len(harmful) == 1

    def test_sample_with_seed(self):
        class MockDataset(Dataset):
            name = "mock"
            version = "1.0.0"

            def _download(self, dest_dir: Path) -> Path:
                return dest_dir / "data.json"

            def _parse(self, raw_path: Path) -> list[DatasetEntry]:
                return [DatasetEntry(prompt=f"p{i}") for i in range(10)]

        dataset = MockDataset()
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset.load(Path(tmpdir))
            sample1 = dataset.sample(3, seed=42)
            sample2 = dataset.sample(3, seed=42)
            assert len(sample1) == 3
            assert sample1 == sample2

    def test_len_and_iter(self):
        class MockDataset(Dataset):
            name = "mock"
            version = "1.0.0"

            def _download(self, dest_dir: Path) -> Path:
                return dest_dir / "data.json"

            def _parse(self, raw_path: Path) -> list[DatasetEntry]:
                return [DatasetEntry(prompt=f"p{i}") for i in range(5)]

        dataset = MockDataset()
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset.load(Path(tmpdir))
            assert len(dataset) == 5
            assert list(dataset) == dataset._entries


class TestDatasetLoader:
    def test_register_and_list(self):
        class MockDataset(Dataset):
            name = "mock"
            version = "1.0.0"

            def _download(self, dest_dir: Path) -> Path:
                return dest_dir / "data.json"

            def _parse(self, raw_path: Path) -> list[DatasetEntry]:
                return [DatasetEntry(prompt="test")]

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = DatasetLoader(Path(tmpdir))
            loader.register_dataset("mock", MockDataset)
            assert loader.list_datasets() == ["mock"]

    def test_load_dataset(self):
        class MockDataset(Dataset):
            name = "mock"
            version = "1.0.0"

            def _download(self, dest_dir: Path) -> Path:
                dest_dir.mkdir(parents=True, exist_ok=True)
                file_path = dest_dir / "data.json"
                file_path.write_text("[]")
                return file_path

            def _parse(self, raw_path: Path) -> list[DatasetEntry]:
                return [DatasetEntry(prompt="test")]

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = DatasetLoader(Path(tmpdir))
            loader.register_dataset("mock", MockDataset)
            dataset = loader.load_dataset("mock")
            assert dataset.name == "mock"
            assert len(dataset) == 1

    def test_load_unregistered_dataset(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = DatasetLoader(Path(tmpdir))
            with pytest.raises(ValueError, match="not registered"):
                loader.load_dataset("nonexistent")

    def test_clear_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = DatasetLoader(Path(tmpdir))
            cache_file = Path(tmpdir) / "test.txt"
            cache_file.write_text("test")

            loader.clear_cache()
            assert not cache_file.exists()


class TestHashFunctions:
    def test_compute_hash(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            f.flush()
            file_path = Path(f.name)

            hash1 = compute_hash(file_path)
            hash2 = compute_hash(file_path)
            assert hash1 == hash2
            assert len(hash1) == 64

    def test_verify_hash(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            f.flush()
            file_path = Path(f.name)

            correct_hash = compute_hash(file_path)
            assert verify_hash(file_path, correct_hash)
            assert not verify_hash(file_path, "wrong_hash")
