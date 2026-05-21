"""AdvBench dataset downloader.

AdvBench (Zou et al., 2023) contains ~500 harmful instructions across categories:
violence, drugs, hate speech, malicious use, privacy violations, etc.

Source: https://github.com/llm-attacks/llm-attacks
"""

import csv
import json
from pathlib import Path

from centinela.datasets.base import Dataset
from centinela.datasets.loader import download_file
from centinela.datasets.types import DatasetCategory, DatasetEntry

_ADVBNCH_URL = "https://raw.githubusercontent.com/llm-attacks/llm-attacks/main/data/advbench/harmful_behaviors.csv"
_ADVBNCH_FALLBACK_URLS = [
    "https://raw.githubusercontent.com/llm-attacks/llm-attacks/main/data/advbench/harmful_behaviors.csv",
]


class AdvBenchDataset(Dataset):
    """AdvBench harmful behaviors dataset.

    Contains ~500 adversarial prompts designed to elicit harmful responses.
    """

    name = "advbench"
    version = "1.0.0"

    def _download(self, dest_dir: Path) -> Path:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / "harmful_behaviors.csv"

        for url in _ADVBNCH_FALLBACK_URLS:
            try:
                return download_file(url, dest_file, progress=True)
            except Exception:
                continue

        raise RuntimeError(f"Failed to download AdvBench from all sources: {_ADVBNCH_FALLBACK_URLS}")

    def _parse(self, raw_path: Path) -> list[DatasetEntry]:
        entries = []

        if raw_path.suffix == ".csv":
            entries = self._parse_csv(raw_path)
        elif raw_path.suffix == ".json":
            entries = self._parse_json(raw_path)
        else:
            entries = self._parse_csv(raw_path)

        return entries

    def _parse_csv(self, path: Path) -> list[DatasetEntry]:
        entries = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                prompt = row.get("goal", row.get("prompt", row.get("text", ""))).strip()
                if not prompt:
                    continue

                category = self._categorize_prompt(prompt)
                severity = self._estimate_severity(prompt)

                entries.append(
                    DatasetEntry(
                        prompt=prompt,
                        label="harmful",
                        category=category,
                        severity=severity,
                        metadata={
                            "source": "advbench",
                            "original_index": idx,
                            "target": row.get("target", ""),
                        },
                    )
                )
        return entries

    def _parse_json(self, path: Path) -> list[DatasetEntry]:
        entries = []
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        for idx, item in enumerate(data):
            prompt = item.get("goal", item.get("prompt", item.get("text", ""))).strip()
            if not prompt:
                continue

            category = self._categorize_prompt(prompt)
            severity = self._estimate_severity(prompt)

            entries.append(
                DatasetEntry(
                    prompt=prompt,
                    label="harmful",
                    category=category,
                    severity=severity,
                    metadata={
                        "source": "advbench",
                        "original_index": idx,
                        "target": item.get("target", ""),
                    },
                )
            )
        return entries

    def _categorize_prompt(self, prompt: str) -> DatasetCategory:
        prompt_lower = prompt.lower()

        if any(word in prompt_lower for word in ["kill", "murder", "bomb", "weapon", "suicide", "die"]):
            return DatasetCategory.VIOLENCE
        if any(word in prompt_lower for word in ["drug", "cocaine", "heroin", "meth", "illegal substance"]):
            return DatasetCategory.DRUGS
        if any(word in prompt_lower for word in ["racist", "hate", "ethnic", "inferior", "superior"]):
            return DatasetCategory.HATE_SPEECH
        if any(word in prompt_lower for word in ["hack", "exploit", "malware", "phishing", "steal"]):
            return DatasetCategory.MALICIOUS_USE
        if any(word in prompt_lower for word in ["private", "password", "ssn", "credit card", "personal data"]):
            return DatasetCategory.PRIVACY
        if any(word in prompt_lower for word in ["sexual", "porn", "nude", "explicit"]):
            return DatasetCategory.SEXUAL_CONTENT
        if any(word in prompt_lower for word in ["self-harm", "self harm", "cutting", "eating disorder"]):
            return DatasetCategory.SELF_HARM

        return DatasetCategory.GENERAL

    def _estimate_severity(self, prompt: str) -> float:
        prompt_lower = prompt.lower()
        severity = 0.5

        high_severity_indicators = [
            "step by step",
            "detailed instructions",
            "how to create",
            "how to make",
            "how to kill",
            "how to hack",
            "tutorial",
            "guide",
        ]

        for indicator in high_severity_indicators:
            if indicator in prompt_lower:
                severity = min(severity + 0.1, 1.0)

        return severity

    def _get_source(self) -> str:
        return "https://github.com/llm-attacks/llm-attacks"

    def _get_description(self) -> str:
        return "AdvBench: ~500 harmful behaviors for adversarial testing (Zou et al., 2023)"
