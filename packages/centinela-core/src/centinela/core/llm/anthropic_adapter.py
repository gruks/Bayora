from __future__ import annotations

from typing import AsyncIterator

import litellm

from .base import UniversalProviderAdapter
from .factory import ProviderFactory
from .types import NormalizedChunk, NormalizedResponse, ProviderConfig, TokenUsage


@ProviderFactory.register("anthropic")
class AnthropicAdapter(UniversalProviderAdapter):
    """Anthropic provider adapter via LiteLLM."""

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config
        self._litellm_model = f"anthropic/{config.model}"

    @property
    def model(self) -> str:
        return self._config.model

    @property
    def provider(self) -> str:
        return "anthropic"

    def _get_api_kwargs(self) -> dict[str, object]:
        kwargs: dict[str, object] = {"timeout": self._config.timeout}
        if self._config.api_key is not None:
            kwargs["api_key"] = bytes(self._config.api_key).decode("utf-8")
        if self._config.api_base is not None:
            kwargs["api_base"] = self._config.api_base
        return kwargs

    def generate(self, messages: list[dict[str, object]], **kwargs: object) -> NormalizedResponse:
        api_kwargs = self._get_api_kwargs()
        api_kwargs.update(kwargs)
        response = litellm.completion(
            model=self._litellm_model,
            messages=messages,
            **api_kwargs,
        )
        choice = response.choices[0]
        usage = response.usage
        return NormalizedResponse(
            content=choice.message.content or "",
            model=self._litellm_model,
            provider=self.provider,
            usage=TokenUsage(
                prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
                total_tokens=getattr(usage, "total_tokens", 0) or 0,
            ),
            cost=getattr(response, "_hidden_params", {}).get("response_cost"),
        )

    async def generate_stream(  # type: ignore[override]
        self, messages: list[dict[str, object]], **kwargs: object
    ) -> AsyncIterator[NormalizedChunk]:
        api_kwargs = self._get_api_kwargs()
        api_kwargs.update(kwargs)
        response = await litellm.acompletion(
            model=self._litellm_model,
            messages=messages,
            stream=True,
            **api_kwargs,
        )
        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            yield NormalizedChunk(
                content=delta.content if delta else None,
                finish_reason=chunk.choices[0].finish_reason if chunk.choices else None,
            )

    def count_tokens(self, messages: list[dict[str, object]]) -> int:
        result = litellm.token_counter(model=self._litellm_model, messages=messages)
        return result if isinstance(result, int) else result.total_tokens
