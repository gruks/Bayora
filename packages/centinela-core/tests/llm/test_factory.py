"""Tests for ProviderFactory — decorator registry, create(), litellm config."""

from __future__ import annotations

import litellm

from centinela.core.llm import ProviderFactory
from centinela.core.llm.base import UniversalProviderAdapter
from centinela.core.llm.types import ProviderConfig


class TestLiteLLMGlobalConfig:
    """Verify litellm.num_retries and retry_strategy are set at module import."""

    def test_num_retries(self) -> None:
        assert litellm.num_retries == 3

    def test_retry_strategy(self) -> None:
        assert litellm.retry_strategy == "exponential_backoff_retry"


class TestProviderFactoryRegistry:
    """Decorator-based registration."""

    def test_register_decorator(self) -> None:
        """A test adapter should register via the decorator."""

        @ProviderFactory.register("test_provider")
        class TestAdapter(UniversalProviderAdapter):
            def __init__(self, config: ProviderConfig) -> None:
                self._config = config

            @property
            def model(self) -> str:
                return self._config.model

            @property
            def provider(self) -> str:
                return "test_provider"

            def generate(self, messages: list[dict], **kwargs: object) -> object:
                return None

            async def generate_stream(self, messages: list[dict], **kwargs: object) -> object:
                return None
                yield  # pragma: no cover

            def count_tokens(self, messages: list[dict]) -> int:
                return 0

        assert "test_provider" in ProviderFactory.list_providers()
        # Clean up registry
        ProviderFactory._registry.pop("test_provider", None)

    def test_register_overwrites(self) -> None:
        """Registering same provider name overwrites previous entry."""

        @ProviderFactory.register("overwrite_test")
        class FirstAdapter(UniversalProviderAdapter):
            def __init__(self, config: ProviderConfig) -> None:
                self._config = config

            @property
            def model(self) -> str:
                return self._config.model

            @property
            def provider(self) -> str:
                return "first"

            def generate(self, messages: list[dict], **kwargs: object) -> None:
                return None

            async def generate_stream(self, messages: list[dict], **kwargs: object) -> None:
                return None
                yield  # pragma: no cover

            def count_tokens(self, messages: list[dict]) -> int:
                return 0

        @ProviderFactory.register("overwrite_test")
        class SecondAdapter(UniversalProviderAdapter):
            def __init__(self, config: ProviderConfig) -> None:
                self._config = config

            @property
            def model(self) -> str:
                return self._config.model

            @property
            def provider(self) -> str:
                return "second"

            def generate(self, messages: list[dict], **kwargs: object) -> None:
                return None

            async def generate_stream(self, messages: list[dict], **kwargs: object) -> None:
                return None
                yield  # pragma: no cover

            def count_tokens(self, messages: list[dict]) -> int:
                return 0

        adapter = ProviderFactory.create("overwrite_test", ProviderConfig(model="test"))
        assert adapter.provider == "second"  # Overwritten
        ProviderFactory._registry.pop("overwrite_test", None)


class TestProviderFactoryCreate:
    """Factory create() method and error handling."""

    def _make_dummy_adapter(self, provider_name: str = "dummy") -> type:
        """Helper to create and register a minimal adapter for testing."""

        @ProviderFactory.register(provider_name)
        class DummyAdapter(UniversalProviderAdapter):
            def __init__(self, config: ProviderConfig) -> None:
                self._config = config
                self._model = config.model

            @property
            def model(self) -> str:
                return self._config.model

            @property
            def provider(self) -> str:
                return provider_name

            def generate(self, messages: list[dict], **kwargs: object) -> object:
                return None

            async def generate_stream(self, messages: list[dict], **kwargs: object) -> object:
                return None
                yield  # pragma: no cover

            def count_tokens(self, messages: list[dict]) -> int:
                return 0

        return DummyAdapter

    def test_create_valid_provider(self) -> None:
        self._make_dummy_adapter("test_create")
        config = ProviderConfig(model="test-model")
        adapter = ProviderFactory.create("test_create", config)
        assert adapter.model == "test-model"
        assert adapter.provider == "test_create"
        ProviderFactory._registry.pop("test_create", None)

    def test_create_unknown_provider_raises(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="Unknown provider"):
            ProviderFactory.create("nonexistent", ProviderConfig(model="x"))

    def test_create_with_invalid_config_type(self) -> None:
        self._make_dummy_adapter("test_config_type")
        import pytest

        with pytest.raises(TypeError, match="config must be a ProviderConfig"):
            ProviderFactory.create("test_config_type", {"model": "x"})  # type: ignore[arg-type]
        ProviderFactory._registry.pop("test_config_type", None)

    def test_list_providers_returns_sorted(self) -> None:
        self._make_dummy_adapter("zzz_last")
        self._make_dummy_adapter("aaa_first")
        self._make_dummy_adapter("mmm_middle")
        providers = ProviderFactory.list_providers()
        assert providers == sorted(providers)
        ProviderFactory._registry.pop("zzz_last", None)
        ProviderFactory._registry.pop("aaa_first", None)
        ProviderFactory._registry.pop("mmm_middle", None)
