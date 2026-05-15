"""Universal provider adapter — normalized LLM access across all providers."""

from .types import NormalizedChunk, NormalizedResponse, ProviderConfig, TokenUsage
from .base import UniversalProviderAdapter
from .secure_key import SecureKeyStore
from .factory import ProviderFactory
from .openai_adapter import OpenAIAdapter
from .anthropic_adapter import AnthropicAdapter
from .ollama_adapter import OllamaAdapter
from .custom_adapter import CustomEndpointAdapter


def list_providers() -> list[str]:
    """Convenience: list registered provider names."""
    return ProviderFactory.list_providers()


def create_provider(provider: str, config: ProviderConfig) -> "UniversalProviderAdapter":
    """Convenience: create a registered provider adapter."""
    return ProviderFactory.create(provider, config)  # type: ignore[return-value]


__all__ = [
    "NormalizedResponse",
    "NormalizedChunk",
    "TokenUsage",
    "ProviderConfig",
    "UniversalProviderAdapter",
    "SecureKeyStore",
    "ProviderFactory",
    "OpenAIAdapter",
    "AnthropicAdapter",
    "OllamaAdapter",
    "CustomEndpointAdapter",
    "list_providers",
    "create_provider",
]
