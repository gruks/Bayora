# Phase 2: Universal Provider Adapter — Research

**Researched:** 2026-05-15
**Domain:** LLM provider abstraction, API gateway integration, secure memory management
**Confidence:** HIGH (all findings verified against official docs and source)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Use LiteLLM as underlying gateway library** — no alternatives
- **API key must use `memoryview` for RAM-only storage with zeroing** — no alternatives
- **Exponential backoff with up to 3 retries for rate limits** — no alternatives
- **Normalized response schema must be identical across all 4 adapters** — no alternatives

### Claude's Discretion
- Exact normalized response schema structure
- Token counting implementation strategy
- Error handling patterns beyond rate limits

### Deferred Ideas (OUT OF SCOPE)
- Multi-modal support (image/audio inputs) — not in scope
</user_constraints>

## Executive Summary

1. **LiteLLM v1.84.0** (as of May 14, 2026) is the gateway — use its `completion()`/`acompletion()` with the `openai/`, `anthropic/`, `ollama/` provider prefixes. It normalizes all provider APIs under OpenAI-compatible response shapes internally.
2. **Adapter pattern**: Use abstract base class (ABC) with `generate()`, `generate_stream()`, `count_tokens()`. Each adapter wraps LiteLLM calls — NOT raw provider SDKs. A factory method instantiates the right adapter by provider type.
3. **Memoryview zeroing**: Use `bytearray` as the backing store -> wrap in `memoryview` -> pass `memoryview.cast('B')` to LiteLLM -> zero with `mv[:] = b'\x00' * len(mv)` -> `mv.release()`. This is the only Python-native way to guarantee destruction of key material.
4. **Rate limiting**: Use LiteLLM's built-in `num_retries=3` and `retry_strategy="exponential_backoff_retry"` for simplicity, OR wrap with `tenacity` (actively maintained fork of `retrying`) for finer control.
5. **Project location**: The adapter module lives in `packages/centinela-core/src/centinela/core/llm/` — matching uv workspace structure declared in `pyproject.toml`.

## LiteLLM API Deep-Dive

### Core Completion

LiteLLM provides a single `completion()` function that dispatches to the correct provider based on model name prefix:

```python
from litellm import completion

# OpenAI
response = completion(model="openai/gpt-4o", messages=[{"role": "user", "content": "Hello"}])

# Anthropic
response = completion(model="anthropic/claude-3-5-sonnet-20241022", messages=[{"role": "user", "content": "Hello"}])

# Ollama
response = completion(model="ollama/llama3", messages=[{"role": "user", "content": "Hello"}], api_base="http://localhost:11434")

# OpenAI-compatible (custom endpoint)
response = completion(model="openai/mistral", messages=[{"role": "user", "content": "Hello"}], api_base="http://0.0.0.0:4000", api_key="sk-1234")
```

**Source:** https://docs.litellm.ai/docs/providers/openai_compatible | **Confidence:** HIGH

### Streaming

Pass `stream=True` to get a `CustomStreamWrapper` that yields `ModelResponseStream` chunks:

```python
response = completion(model="openai/gpt-4o", messages=messages, stream=True)
for chunk in response:
    print(chunk.choices[0].delta.content or "")
```

Use `litellm.stream_chunk_builder(chunks, messages=messages)` to reassemble full response from chunks.

**Source:** https://docs.litellm.ai/docs/completion/stream | **Confidence:** HIGH

### Async

```python
from litellm import acompletion

response = await acompletion(model="openai/gpt-4o", messages=messages)

# Async streaming
response = await acompletion(model="openai/gpt-4o", messages=messages, stream=True)
async for chunk in response:
    print(chunk)
```

**Source:** https://docs.litellm.ai/stream | **Confidence:** HIGH

### Token Counting

LiteLLM provides `litellm.acount_tokens()` (async) with provider-specific tokenizers:

```python
import asyncio
import litellm

async def main():
    result = await litellm.acount_tokens(
        model="openai/gpt-4o",
        messages=[{"role": "user", "content": "Hello"}],
    )
    print(f"Token count: {result.total_tokens}")
    print(f"Tokenizer: {result.tokenizer_type}")

# Returns TokenCountResponse with: total_tokens, request_model, model_used, tokenizer_type, original_response
```

Fallback to local `tiktoken` counting when provider API key is unavailable. Also provides `token_counter()` (sync) for simple counting.

**Source:** https://docs.litellm.ai/docs/count_tokens | **Confidence:** HIGH

### Response Shape

LiteLLM normalizes all provider responses to the OpenAI `ModelResponse` structure:

```python
# Non-streaming response object:
response = completion(model="openai/gpt-4o", messages=messages)
response.choices[0].message.content   # str
response.usage.prompt_tokens          # int
response.usage.completion_tokens      # int
response.usage.total_tokens           # int
response._hidden_params["response_cost"]  # float (USD)

# Streaming response chunk:
chunk.choices[0].delta.content  # str or None
chunk.choices[0].finish_reason  # "stop" | "length" | None
```

**Source:** https://docs.litellm.ai/docs/completion/token_usage | **Confidence:** HIGH

### Error Types (all mirror OpenAI)

| LiteLLM Exception | HTTP Status | Should Retry |
|-------------------|-------------|--------------|
| `RateLimitError` | 429 | Yes |
| `ServiceUnavailableError` | 503 | Yes |
| `Timeout` | 408 | Yes |
| `InternalServerError` | 500 | Yes |
| `AuthenticationError` | 401 | No |
| `BadRequestError` | 400 | No |
| `ContentPolicyViolationError` | - | No |

**Source:** https://docs.litellm.ai/docs/exception_mapping | **Confidence:** HIGH

## Adapter Pattern Recommendation

### Architecture: Abstract Base + Factory

Do NOT have each adapter call its own SDK. Since LiteLLM normalizes everything, each adapter is a thin wrapper that:
1. Stores provider-specific config (model name, api key, api base, params)
2. Calls `litellm.completion()` with the correct model prefix
3. Translates LiteLLM's response into the normalized schema
4. Handles errors according to provider-specific retry policy

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator
import litellm

@dataclass
class ProviderConfig:
    model: str
    api_key: memoryview | None = None
    api_base: str | None = None
    max_retries: int = 3

class UniversalProviderAdapter(ABC):
    """Abstract base for all LLM provider adapters."""

    @abstractmethod
    def generate(self, messages: list[dict], **kwargs) -> NormalizedResponse:
        ...

    @abstractmethod
    def generate_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[NormalizedChunk]:
        ...

    @abstractmethod
    def count_tokens(self, messages: list[dict]) -> int:
        ...
```

### Factory Pattern

```python
class ProviderFactory:
    _registry: dict[str, type[UniversalProviderAdapter]] = {}

    @classmethod
    def register(cls, provider: str):
        def inner(wrapper: type[UniversalProviderAdapter]):
            cls._registry[provider] = wrapper
            return wrapper
        return inner

    @classmethod
    def create(cls, provider: str, config: ProviderConfig) -> UniversalProviderAdapter:
        adapter_cls = cls._registry.get(provider)
        if not adapter_cls:
            raise ValueError(f"Unknown provider: {provider}")
        return adapter_cls(config)
```

### Adapter Implementations

Each adapter sets the `model` prefix LiteLLM expects:

| Adapter | Provider Prefix | Example Model |
|---------|----------------|---------------|
| OpenAIAdapter | `openai/` | `openai/gpt-4o` |
| AnthropicAdapter | `anthropic/` | `anthropic/claude-3-5-sonnet-20241022` |
| OllamaAdapter | `ollama/` | `ollama/llama3` (requires `api_base`) |
| CustomEndpointAdapter | `openai/` | `openai/custom-model` (requires `api_base`) |

**Pattern inspiration:** https://github.com/LiteObject/llm-provider-abstraction, https://github.com/ankithreddi/universal-llm-adapter | **Confidence:** MEDIUM

### Anti-Patterns to Avoid

- Each adapter managing its own HTTP client -- LiteLLM handles tran
