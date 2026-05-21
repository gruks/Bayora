"""JailbreakBench dataset downloader.

JailbreakBench contains jailbreak prompts with goal/target pairs, organized by
jailbreak technique (direct, obfuscated, roleplay, etc.).

Source: https://github.com/JailbreakBench/jailbreakbench
"""

import csv
import json
from pathlib import Path

from centinela.datasets.base import Dataset
from centinela.datasets.loader import download_file
from centinela.datasets.types import DatasetCategory, DatasetEntry

_JBB_URL = "https://raw.githubusercontent.com/JailbreakBench/jailbreakbench/main/data/jailbreakbench_v1.json"
_JBB_FALLBACK_URLS = [
    "https://raw.githubusercontent.com/JailbreakBench/jailbreakbench/main/data/jailbreakbench_v1.json",
]


class JailbreakBenchDataset(Dataset):
    """JailbreakBench dataset of jailbreak prompts.

    Contains jailbreak prompts organized by technique and difficulty.
    """

    name = "jailbreakbench"
    version = "1.0.0"

    def _download(self, dest_dir: Path) -> Path:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / "jailbreakbench_v1.json"

        for url in _JBB_FALLBACK_URLS:
            try:
                return download_file(url, dest_file, progress=True)
            except Exception:
                continue

        raise RuntimeError(f"Failed to download JailbreakBench from all sources: {_JBB_FALLBACK_URLS}")

    def _parse(self, raw_path: Path) -> list[DatasetEntry]:
        if raw_path.suffix == ".json":
            return self._parse_json(raw_path)
        elif raw_path.suffix == ".csv":
            return self._parse_csv(raw_path)
        else:
            return self._parse_json(raw_path)

    def _parse_json(self, path: Path) -> list[DatasetEntry]:
        entries = []
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        items = data if isinstance(data, list) else data.get("prompts", data.get("data", []))

        for idx, item in enumerate(items):
            prompt = self._extract_prompt(item)
            if not prompt:
                continue

            category = DatasetCategory.JAILBREAK
            severity = self._estimate_severity(prompt, item)
            technique = self._extract_technique(item)

            entries.append(
                DatasetEntry(
                    prompt=prompt,
                    label="jailbreak",
                    category=category,
                    severity=severity,
                    metadata={
                        "source": "jailbreakbench",
                        "original_index": idx,
                        "technique": technique,
                        "goal": item.get("goal", ""),
                        "target": item.get("target", ""),
                        "model": item.get("model", ""),
                    },
                )
            )
        return entries

    def _parse_csv(self, path: Path) -> list[DatasetEntry]:
        entries = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                prompt = row.get("prompt", row.get("jailbreak", row.get("text", ""))).strip()
                if not prompt:
                    continue

                category = DatasetCategory.JAILBREAK
                severity = self._estimate_severity(prompt, row)
                technique = row.get("technique", row.get("type", "direct"))

                entries.append(
                    DatasetEntry(
                        prompt=prompt,
                        label="jailbreak",
                        category=category,
                        severity=severity,
                        metadata={
                            "source": "jailbreakbench",
                            "original_index": idx,
                            "technique": technique,
                            "goal": row.get("goal", ""),
                            "target": row.get("target", ""),
                        },
                    )
                )
        return entries

    def _extract_prompt(self, item: dict) -> str:
        for key in ["prompt", "jailbreak", "text", "input", "question"]:
            if key in item and isinstance(item[key], str):
                return item[key].strip()
        return ""

    def _extract_technique(self, item: dict) -> str:
        for key in ["technique", "type", "category", "method"]:
            if key in item:
                return str(item[key])
        return "unknown"

    def _estimate_severity(self, prompt: str, item: dict) -> float:
        prompt_lower = prompt.lower()
        severity = 0.6

        technique = self._extract_technique(item).lower()
        if technique in ["direct", "base64", "encoding"]:
            severity = 0.7
        elif technique in ["roleplay", "hypothetical", "academic"]:
            severity = 0.8
        elif technique in ["multi-turn", "iterative", "crescendo"]:
            severity = 0.9

        high_severity = ["illegal", "dangerous", "harmful", "exploit", "malicious"]
        for word in high_severity:
            if word in prompt_lower:
                severity = min(severity + 0.05, 1.0)

        return severity

    def _get_source(self) -> str:
        return "https://github.com/JailbreakBench/jailbreakbench"

    def _get_description(self) -> str:
        return "JailbreakBench: Jailbreak prompts organized by technique and difficulty"
