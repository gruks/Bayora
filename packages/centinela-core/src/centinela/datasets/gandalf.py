"""Gandalf/Lakera dataset downloader.

Gandalf (Lakera) contains password extraction and prompt injection challenges
across multiple difficulty levels (L1-L8), designed to test AI security.

Source: https://github.com/lakeraai/gandalf
"""

import json
from pathlib import Path

from centinela.datasets.base import Dataset
from centinela.datasets.loader import download_file
from centinela.datasets.types import DatasetCategory, DatasetEntry

_GANDALF_URL = "https://raw.githubusercontent.com/lakeraai/gandalf/main/data/challenges.json"
_GANDALF_FALLBACK_URLS = [
    "https://raw.githubusercontent.com/lakeraai/gandalf/main/data/challenges.json",
]


class GandalfDataset(Dataset):
    """Gandalf challenge dataset from Lakera.

    Contains password extraction and prompt injection challenges with difficulty levels.
    """

    name = "gandalf"
    version = "1.0.0"

    def _download(self, dest_dir: Path) -> Path:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / "challenges.json"

        for url in _GANDALF_FALLBACK_URLS:
            try:
                return download_file(url, dest_file, progress=True)
            except Exception:
                continue

        raise RuntimeError(f"Failed to download Gandalf dataset from all sources: {_GANDALF_FALLBACK_URLS}")

    def _parse(self, raw_path: Path) -> list[DatasetEntry]:
        with open(raw_path, encoding="utf-8") as f:
            data = json.load(f)

        entries = []
        challenges = data if isinstance(data, list) else data.get("challenges", data.get("data", []))

        for idx, challenge in enumerate(challenges):
            prompt = self._extract_prompt(challenge)
            if not prompt:
                continue

            level = self._extract_level(challenge)
            category = DatasetCategory.DOMAIN_SPECIFIC
            severity = self._level_to_severity(level)

            entries.append(
                DatasetEntry(
                    prompt=prompt,
                    label="challenge",
                    category=category,
                    severity=severity,
                    metadata={
                        "source": "gandalf",
                        "original_index": idx,
                        "level": level,
                        "challenge_type": self._extract_type(challenge),
                        "password_hint": challenge.get("password_hint", ""),
                    },
                )
            )

        return entries

    def _extract_prompt(self, challenge: dict) -> str:
        for key in ["prompt", "question", "challenge", "text", "input"]:
            if key in challenge and isinstance(challenge[key], str):
                return challenge[key].strip()
        return ""

    def _extract_level(self, challenge: dict) -> str:
        for key in ["level", "difficulty", "tier", "stage"]:
            if key in challenge:
                return str(challenge[key])
        return "unknown"

    def _extract_type(self, challenge: dict) -> str:
        for key in ["type", "category", "challenge_type", "kind"]:
            if key in challenge:
                return str(challenge[key])
        return "password_extraction"

    def _level_to_severity(self, level: str) -> float:
        level_num = 0
        for char in level:
            if char.isdigit():
                level_num = int(char)
                break

        severity_map = {
            1: 0.2,
            2: 0.3,
            3: 0.4,
            4: 0.5,
            5: 0.6,
            6: 0.7,
            7: 0.8,
            8: 0.9,
        }

        return severity_map.get(level_num, 0.5)

    def _get_source(self) -> str:
        return "https://github.com/lakeraai/gandalf"

    def _get_description(self) -> str:
        return "Gandalf: Password extraction and prompt injection challenges (Lakera, L1-L8)"
