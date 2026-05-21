"""Universal provider adapter — normalized LLM access across all providers."""

from .anthropic_adapter import AnthropicAdapter
from .base import UniversalProviderAdapter
from .custom_adapter import CustomEndpointAdapter
from .factory import ProviderFactory
from .ollama_adapter import OllamaAdapter
from .openai_adapter import OpenAIAdapter
from .secure_key import SecureKeyStore
from .types import NormalizedChunk, NormalizedResponse, ProviderConfig, TokenUsage


def list_providers() -> list[str]:
    """Convenience: list registered provider names."""
    return ProviderFactory.list_providers()


def create_provider(provider: str, config: ProviderConfig) -> "UniversalProviderAdapter":
    """Convenience: create a registered provider adapter."""
    return ProviderFactory.create(provider, config)  # type: ignore[return-value]


__all__ = [
    "AnthropicAdapter",
    "CustomEndpointAdapter",
    "NormalizedChunk",
    "NormalizedResponse",
    "OllamaAdapter",
    "OpenAIAdapter",
    "ProviderConfig",
    "ProviderFactory",
    "SecureKeyStore",
    "TokenUsage",
    "UniversalProviderAdapter",
    "create_provider",
    "list_providers",
]
