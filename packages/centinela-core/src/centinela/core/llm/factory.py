from __future__ import annotations

import litellm
from typing import Callable, TypeVar

# ── Global LiteLLM Configuration ──────────────────────────────
litellm.num_retries = 3
litellm.retry_strategy = "exponential_backoff_retry"

T = TypeVar("T")


class ProviderFactory:
    """Decorator-based registry for LLM provider adapters.

    Uses late imports to avoid circular dependencies:
    adapters import factory (for @register), factory imports base (for type hints).
    """

    _registry: dict[str, type] = {}

    @classmethod
    def register(cls, provider: str) -> Callable[[type[T]], type[T]]:
        """Decorator that registers an adapter class for the given provider name."""

        def inner(wrapper: type[T]) -> type[T]:
            cls._registry[provider] = wrapper
            return wrapper

        return inner

    @classmethod
    def create(cls, provider: str, config: object) -> object:
        """Instantiate a registered adapter for the given provider.

        Args:
            provider: Provider name.
            config: ProviderConfig instance.

        Returns:
            Configured UniversalProviderAdapter instance.

        Raises:
            ValueError: If provider is not registered.
        """
        from .base import UniversalProviderAdapter
        from .types import ProviderConfig

        if not isinstance(config, ProviderConfig):
            raise TypeError("config must be a ProviderConfig instance")

        adapter_cls = cls._registry.get(provider)
        if adapter_cls is None:
            registered = ", ".join(sorted(cls._registry))
            raise ValueError(f"Unknown provider: '{provider}'. Registered providers: {registered}")
        if not issubclass(adapter_cls, UniversalProviderAdapter):
            raise TypeError(f"'{provider}' adapter does not implement UniversalProviderAdapter")
        return adapter_cls(config)  # type: ignore[call-arg]

    @classmethod
    def list_providers(cls) -> list[str]:
        """Return sorted list of registered provider names."""
        return sorted(cls._registry)
