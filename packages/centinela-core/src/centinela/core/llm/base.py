from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from .types import NormalizedChunk, NormalizedResponse


class UniversalProviderAdapter(ABC):
    """Abstract base for all LLM provider adapters.

    Every concrete adapter implements generate(), generate_stream(),
    and count_tokens(). The normalized response types guarantee
    identical schema across all providers.
    """

    @property
    @abstractmethod
    def model(self) -> str:
        """The model identifier (e.g. 'gpt-4o', 'claude-3-5-sonnet-20241022')."""
        ...

    @property
    @abstractmethod
    def provider(self) -> str:
        """The provider name (e.g. 'openai', 'anthropic', 'ollama')."""
        ...

    @abstractmethod
    def generate(self, messages: list[dict[str, object]], **kwargs: object) -> NormalizedResponse:
        """Synchronous text generation.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            **kwargs: Additional provider-specific parameters.

        Returns:
            NormalizedResponse with identical schema across all providers.

        Raises:
            RateLimitError: After exhausting retries.
            AuthenticationError: If credentials are invalid.
        """
        ...

    @abstractmethod
    async def generate_stream(
        self, messages: list[dict[str, object]], **kwargs: object
    ) -> AsyncIterator[NormalizedChunk]:
        """Streaming text generation.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            **kwargs: Additional provider-specific parameters.

        Yields:
            NormalizedChunk for each streaming delta.
        """
        raise NotImplementedError

    @abstractmethod
    def count_tokens(self, messages: list[dict[str, object]]) -> int:
        """Count the number of tokens in the given messages.

        Args:
            messages: List of message dicts.

        Returns:
            Total token count as an integer.
        """
        ...
