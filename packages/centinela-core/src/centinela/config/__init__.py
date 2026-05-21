"""Configuration loading and validation for platform security policies."""

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from .models import PlatformConfig, ResourceLimits, SecurityConfig, substitute_env_vars_in_dict
from .policy import CircularDependencyError, PolicyParser, PolicyRegistry, SecurityPolicy


class ConfigLoader:
    """Loads and validates platform configuration from various sources.

    Supports loading from:
    - YAML files
    - JSON strings
    - Python dictionaries

    Performs env var substitution before validation.
    """

    @staticmethod
    def load_from_file(path: str) -> PlatformConfig:
        """Load configuration from a YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            Validated PlatformConfig instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If configuration is invalid
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return ConfigLoader.load_from_dict(data or {})

    @staticmethod
    def load_from_json(json_str: str) -> PlatformConfig:
        """Load configuration from a JSON string.

        Args:
            json_str: JSON configuration string

        Returns:
            Validated PlatformConfig instance

        Raises:
            ValueError: If JSON is invalid or configuration fails validation
        """
        data = json.loads(json_str)
        return ConfigLoader.load_from_dict(data)

    @staticmethod
    def load_from_dict(data: dict[str, Any]) -> PlatformConfig:
        """Load configuration from a dictionary.

        Performs env var substitution on string values before validation.

        Args:
            data: Configuration dictionary

        Returns:
            Validated PlatformConfig instance

        Raises:
            ValueError: If configuration fails validation
        """
        # Substitute env vars in string values
        processed_data = substitute_env_vars_in_dict(data)
        return PlatformConfig.model_validate(processed_data)


def load_config(path: str) -> PlatformConfig:
    """Convenience function to load configuration from a file.

    Args:
        path: Path to YAML configuration file

    Returns:
        Validated PlatformConfig instance

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If configuration is invalid
    """
    return ConfigLoader.load_from_file(path)


__all__ = [
    "CircularDependencyError",
    "ConfigLoader",
    "PlatformConfig",
    "PolicyParser",
    "PolicyRegistry",
    "ResourceLimits",
    "SecurityConfig",
    "SecurityPolicy",
    "load_config",
]
