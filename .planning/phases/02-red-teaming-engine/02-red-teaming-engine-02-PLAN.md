---
phase: 02-red-teaming-engine
plan: 02
type: execute
wave: 2
depends_on: ["01"]
files_modified:
  - packages/centinela-core/src/centinela/core/llm/__init__.py
  - packages/centinela-core/src/centinela/core/llm/openai_adapter.py
  - packages/centinela-core/src/centinela/core/llm/anthropic_adapter.py
  - packages/centinela-core/src/centinela/core/llm/ollama_adapter.py
  - packages/centinela-core/src/centinela/core/llm/custom_adapter.py
autonomous: true
user_setup: []

must_haves:
  truths:
    - "Developer can instantiate all 4 adapters via ProviderFactory.create()"
    - "OpenAIAdapter returns NormalizedResponse with provider='openai'"
    - "AnthropicAdapter returns NormalizedResponse with provider='anthropic'"
    - "OllamaAdapter returns NormalizedResponse with provider='ollama'"
    - "CustomEndpointAdapter returns NormalizedResponse with provider='custom'"
    - "All 4 adapters implement identical interface — generate(), generate_stream(), count_tokens()"
    - "CustomEndpointAdapter accepts config.api_base for arbitrary OpenAI-compatible endpoints"
    - "OllamaAdapter accepts config.api_base for local server URL"
  artifacts:
    - path: "packages/centinela-core/src/centinela/core/llm/openai_adapter.py"
      provides: "OpenAI adapter — wraps LiteLLM with openai/ prefix"
    - path: "packages/centinela-core/src/centinela/core/llm/anthropic_adapter.py"
      provides: "Anthropic adapter — wraps LiteLLM with anthropic/ prefix"
    - path: "packages/centinela-core/src/centinela/core/llm/ollama_adapter.py"
      provides: "Ollama adapter — wraps LiteLLM with ollama/ prefix, requires api_base"
    - path: "packages/centinela-core/src/centinela/core/llm/custom_adapter.py"
      provides: "Custom OpenAI-compatible endpoint adapter"
    - path: "packages/centinela-core/src/centinela/core/llm/__init__.py"
      provides: "Exports all 4 adapters and updated public API"
  key_links:
    - from: "openai_adapter.py"
      to: "litellm.completion()"
      via: "model='openai/gpt-4o' — LiteLLM dispatches by prefix"
      pattern: "model=\"openai/"
    - from: "anthropic_adapter.py"
      to: "litellm.completion()"
      via: "model='anthropic/claude-3-5-sonnet-20241022'"
      pattern: "model=\"anthropic/"
    - from: "ollama_adapter.py"
      to: "litellm.completion()"
      via: "model='ollama/llama3' + api_base config"
      pattern: "model=\"ollama/"
    - from: "custom_adapter.py"
      to: "litellm.completion()"
      via: "model='openai/{model}' + api_base = config.api_base"
      pattern: "model=\"openai/"
    - from: "openai_adapter.py"
      to: "ProviderFactory"
      via: "@ProviderFactory.register('openai') decorator"
      pattern: "ProviderFactory.register"
    - from: "anthropic_adapter.py"
      to: "ProviderFactory"
      via: "@ProviderFactory.register('anthropic') decorator"
    - from: "ollama_adapter.py"
      to: "ProviderFactory"
      via: "@ProviderFactory.register('ollama') decorator"
    - from: "custom_adapter.py"
      to: "ProviderFactory"
      via: "@ProviderFactory.register('custom') decorator"
---

<objective>
Implement all 4 provider adapters as thin wrappers around LiteLLM: OpenAI, Anthropic, Ollama, and custom OpenAI-compatible endpoints. Each adapter registers itself with ProviderFactory and returns identical NormalizedResponse schema.

Purpose: Each adapter is 30-50 lines — translate provider-specific differences into the unified interface. LiteLLM handles the underlying API dispatch via model name prefixes. The adapters handle config mapping, SecureKeyStore interaction, and NormalizedResponse construction.

Output: 4 adapter files + updated __init__.py exports.
</objective>

<execution_context>
@C:/Users/HP/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/HP/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/02-red-teaming-engine/02-CONTEXT.md
@.planning/phases/02-red-teaming-engine/02-RESEARCH.md

From RESEARCH.md §LiteLLM API Deep-Dive:
- Model prefix routing: `openai/gpt-4o`, `anthropic/claude-3-5-sonnet-20241022`, `ollama/llama3`
- Custom endpoints: `openai/custom-model` with `api_base` pointing to endpoint
- Streaming: pass `stream=True`, yields `ModelResponseStream` chunks
- Token counting: `litellm.token_counter(model=..., messages=...)` for sync
- Response: `response.choices[0].message.content`, `response.usage.{prompt,completion,total}_tokens`
- Error mapping: RateLimitError, ServiceUnavailableError, Timeout → retryable

Locked decisions (from CONTEXT.md):
- LiteLLM is the gateway — adapters call litellm.completion() not provider SDKs
- Normalized response schema IDENTICAL across all 4 adapters
- Exponential backoff + 3 retries already configured globally in factory.py

All adapters follow the same pattern:
1. Constructor accepts ProviderConfig, stores config
2. @ProviderFactory.register("name") decorator
3. generate() → call litellm.completion() with correct prefix + config → construct NormalizedResponse
4. generate_stream() → call litellm.completion(stream=True) → yield NormalizedChunk per chunk
5. count_tokens() → call litellm.token_counter() → return int
6. Properties: model (from config), provider (hardcoded string)
</context>

<tasks>

<task type="auto">
  <name>Task 1: OpenAI + Anthropic adapters</name>
  <files>
    packages/centinela-core/src/centinela/core/llm/openai_adapter.py
    packages/centinela-core/src/centinela/core/llm/anthropic_adapter.py
  </files>
  <action>
    Create two adapter files following the same structural pattern.

    **`openai_adapter.py`:**
    - Register via `@ProviderFactory.register("openai")`
    - Config mapping:
      - `litellm_model`: `f"openai/{config.model}"` (e.g. "openai/gpt-4o")
      - `api_key`: from `config.api_key` via `SecureKeyStore.get_str()` (if not None)
      - `api_base`: from `config.api_base` (if not None)
      - `timeout`: from `config.timeout`
    - Constructor: unpack config, create SecureKeyStore if api_key exists
    - `generate()`: call `litellm.completion(model=..., messages=..., api_key=..., api_base=..., timeout=...)`
      → extract response fields → return `NormalizedResponse(...)`
    - `generate_stream()`: call `litellm.acompletion(model=..., messages=..., stream=True, ...)` (use async)
      → async for chunk in response → yield `NormalizedChunk(content=..., finish_reason=...)`
    - `count_tokens()`: call `litellm.token_counter(model=litellm_model, messages=messages)` → return int

    **`anthropic_adapter.py`:**
    - Register via `@ProviderFactory.register("anthropic")`
    - Same pattern but model prefix is `anthropic/`
    - Example model: `anthropic/claude-3-5-sonnet-20241022`
    - LiteLLM handles all Anthropic-specific API transforms
    - Uses `acompletion()` for streaming (LiteLLM normalizes)

    **Common implementation details for BOTH adapters:**

    ```python
    # Pattern for each adapter file:
    from __future__ import annotations

    from typing import AsyncIterator

    import litellm

    from .types import (
        NormalizedChunk,
        NormalizedResponse,
        ProviderConfig,
        TokenUsage,
    )
    from .base import UniversalProviderAdapter
    from .factory import ProviderFactory
    from .secure_key import SecureKeyStore


    @ProviderFactory.register("{provider_name}")
    class {ProviderName}Adapter(UniversalProviderAdapter):

        def __init__(self, config: ProviderConfig) -> None:
            self._config = config
            self._litellm_model = f"{prefix}/{config.model}"
            # SecureKeyStore wraps the API key if provided
            self._key_store: SecureKeyStore | None = (
                SecureKeyStore(bytes(config.api_key).decode("utf-8"))
                if config.api_key is not None
                else None
            )
            # NOTE: config.api_key is memoryview — we convert to string for key_store
            # Actually, the key comes in as a memoryview from ProviderConfig,
            # but SecureKeyStore expects a str. So we decode at construction time.

        @property
        def model(self) -> str:
            return self._config.model

        @property
        def provider(self) -> str:
            return "{provider_name}"

        def _get_api_kwargs(self) -> dict:
            kwargs: dict = {"timeout": self._config.timeout}
            if self._key_store is not None:
                kwargs["api_key"] = self._key_store.get_str()
            if self._config.api_base is not None:
                kwargs["api_base"] = self._config.api_base
            return kwargs

        def generate(self, messages: list[dict], **kwargs: object) -> NormalizedResponse:
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
                    prompt_tokens=usage.prompt_tokens or 0,
                    completion_tokens=usage.completion_tokens or 0,
                    total_tokens=usage.total_tokens or 0,
                ),
                cost=getattr(response, "_hidden_params", {}).get("response_cost"),
            )

        async def generate_stream(
            self, messages: list[dict], **kwargs: object
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

        def count_tokens(self, messages: list[dict]) -> int:
            result = litellm.token_counter(model=self._litellm_model, messages=messages)
            return result if isinstance(result, int) else result.total_tokens
    ```

    **WAIT — IMPORTANT CORRECTION on the key passing:**

    The `config.api_key` comes in as `memoryview | None` (from ProviderConfig). We cannot directly construct a SecureKeyStore from a memoryview. Instead:
    - If `config.api_key` is not None: decode the memoryview to get the key string, pass that to SecureKeyStore
    - Actually, since memoryview is a view into the original key bytes, the key is ALREADY in RAM-only storage. The SecureKeyStore is designed for FRESH key strings.
    - Better approach: The adapter's constructor receives a ProviderConfig where `api_key` is already a memoryview. The adapter should convert this to a string for LiteLLM and manage the lifecycle.

    **SIMPLER CORRECT APPROACH:**
    Since ProviderConfig already holds the key as memoryview (from SecureKeyStore), the adapter just needs to extract the key string for LiteLLM and NOT create a SECOND SecureKeyStore. The memory lifecycle is managed by whoever created the ProviderConfig.

    ```python
    def _get_api_kwargs(self) -> dict:
        kwargs: dict = {"timeout": self._config.timeout}
        if self._config.api_key is not None:
            kwargs["api_key"] = bytes(self._config.api_key).decode("utf-8")
        if self._config.api_base is not None:
            kwargs["api_base"] = self._config.api_base
        return kwargs
    ```

    This is the correct approach. The ProviderConfig holds the memoryview. The adapter extracts the string temporarily to pass to LiteLLM. The memoryview owner (the session orchestrator) is responsible for zeroing.

    **FINAL implementation (use this for both adapters):**

    ```python
    from __future__ import annotations

    from typing import AsyncIterator

    import litellm

    from .base import UniversalProviderAdapter
    from .factory import ProviderFactory
    from .types import NormalizedChunk, NormalizedResponse, ProviderConfig, TokenUsage


    @ProviderFactory.register("openai")
    class OpenAIAdapter(UniversalProviderAdapter):
        """OpenAI provider adapter via LiteLLM."""

        def __init__(self, config: ProviderConfig) -> None:
            self._config = config
            self._litellm_model = f"openai/{config.model}"

        @property
        def model(self) -> str:
            return self._config.model

        @property
        def provider(self) -> str:
            return "openai"

        def _get_api_kwargs(self) -> dict:
            kwargs: dict = {"timeout": self._config.timeout}
            if self._config.api_key is not None:
                kwargs["api_key"] = bytes(self._config.api_key).decode("utf-8")
            if self._config.api_base is not None:
                kwargs["api_base"] = self._config.api_base
            return kwargs

        def generate(self, messages: list[dict], **kwargs: object) -> NormalizedResponse:
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

        async def generate_stream(
            self, messages: list[dict], **kwargs: object
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

        def count_tokens(self, messages: list[dict]) -> int:
            result = litellm.token_counter(model=self._litellm_model, messages=messages)
            return result if isinstance(result, int) else result.total_tokens
    ```

    For **AnthropicAdapter**, the same pattern with:
    - `@ProviderFactory.register("anthropic")`
    - `self._litellm_model = f"anthropic/{config.model}"`
    - `provider` property returns `"anthropic"`

    IMPORTANT NOTES:
    - `bytes(memoryview).decode("utf-8")` extracts the key string from memoryview — this creates a temporary str, which is unavoidable since LiteLLM expects a string
    - Do NOT cache the extracted key string in `self` — always extract on demand from the memoryview
    - Streaming uses `await litellm.acompletion(... stream=True)` (LiteLLM's async API), NOT `litellm.completion`
    - `response._hidden_params.get("response_cost")` gives the cost in USD — LiteLLM calculates this
    - Use `getattr(usage, "prompt_tokens", 0) or 0` pattern to handle cases where LiteLLM returns 0 or None for token counts
    - Do NOT import litellm exceptions explicitly — let them propagate naturally; the caller handles them
  </action>
  <verify>
    python -c "
    from centinela.core.llm import OpenAIAdapter, AnthropicAdapter, ProviderFactory
    from centinela.core.llm.types import ProviderConfig
    # Verify registration
    assert 'openai' in ProviderFactory.list_providers()
    assert 'anthropic' in ProviderFactory.list_providers()
    # Verify properties
    config = ProviderConfig(model='gpt-4o')
    adapter = OpenAIAdapter(config)
    assert adapter.model == 'gpt-4o'
    assert adapter.provider == 'openai'
    config2 = ProviderConfig(model='claude-3-5-sonnet-20241022')
    adapter2 = AnthropicAdapter(config2)
    assert adapter2.model == 'claude-3-5-sonnet-20241022'
    assert adapter2.provider == 'anthropic'
    print('OpenAI + Anthropic adapters verified')
    "
  </verify>
  <done>
    OpenAIAdapter and AnthropicAdapter registered with ProviderFactory. Properties return correct model and provider names. Both implement generate(), generate_stream(), count_tokens(). LiteLLM handles API dispatch via model prefix.
  </done>
</task>

<task type="auto">
  <name>Task 2: Ollama + CustomEndpoint adapters and namespace update</name>
  <files>
    packages/centinela-core/src/centinela/core/llm/ollama_adapter.py
    packages/centinela-core/src/centinela/core/llm/custom_adapter.py
    packages/centinela-core/src/centinela/core/llm/__init__.py
  </files>
  <action>
    Create two more adapters and update the __init__.py exports.

    **`ollama_adapter.py`:**
    - Register via `@ProviderFactory.register("ollama")`
    - Model prefix: `ollama/`
    - Requires `config.api_base` (e.g. "http://localhost:11434") — Ollama's local server URL
    - Does NOT require api_key (Ollama runs locally, no auth)
    - LiteLLM supported models: ollama/llama3, ollama/mistral, ollama/phi3
    - Same pattern as OpenAI/Anthropic but without api_key in kwargs

    ```python
    from __future__ import annotations

    from typing import AsyncIterator

    import litellm

    from .base import UniversalProviderAdapter
    from .factory import ProviderFactory
    from .types import NormalizedChunk, NormalizedResponse, ProviderConfig, TokenUsage


    @ProviderFactory.register("ollama")
    class OllamaAdapter(UniversalProviderAdapter):

        def __init__(self, config: ProviderConfig) -> None:
            self._config = config
            self._litellm_model = f"ollama/{config.model}"

        @property
        def model(self) -> str:
            return self._config.model

        @property
        def provider(self) -> str:
            return "ollama"

        def _get_api_kwargs(self) -> dict:
            kwargs: dict = {"timeout": self._config.timeout}
            if self._config.api_base is not None:
                kwargs["api_base"] = self._config.api_base
            return kwargs

        def generate(self, messages: list[dict], **kwargs: object) -> NormalizedResponse:
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

        async def generate_stream(
            self, messages: list[dict], **kwargs: object
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

        def count_tokens(self, messages: list[dict]) -> int:
            result = litellm.token_counter(model=self._litellm_model, messages=messages)
            return result if isinstance(result, int) else result.total_tokens
    ```

    **`custom_adapter.py`:**
    - Register via `@ProviderFactory.register("custom")`
    - Model prefix: `openai/` (LiteLLM convention: use "openai/" prefix for ANY OpenAI-compatible API)
    - Requires `config.api_base` (the custom endpoint URL)
    - Requires `config.api_key` if the endpoint requires auth
    - Same generate/generate_stream/count_tokens pattern

    ```python
    from __future__ import annotations

    from typing import AsyncIterator

    import litellm

    from .base import UniversalProviderAdapter
    from .factory import ProviderFactory
    from .types import NormalizedChunk, NormalizedResponse, ProviderConfig, TokenUsage


    @ProviderFactory.register("custom")
    class CustomEndpointAdapter(UniversalProviderAdapter):

        def __init__(self, config: ProviderConfig) -> None:
            self._config = config
            self._litellm_model = f"openai/{config.model}"

        @property
        def model(self) -> str:
            return self._config.model

        @property
        def provider(self) -> str:
            return "custom"

        def _get_api_kwargs(self) -> dict:
            kwargs: dict = {"timeout": self._config.timeout}
            if self._config.api_key is not None:
                kwargs["api_key"] = bytes(self._config.api_key).decode("utf-8")
            if self._config.api_base is not None:
                kwargs["api_base"] = self._config.api_base
            return kwargs

        def generate(self, messages: list[dict], **kwargs: object) -> NormalizedResponse:
            # Same body as OpenAIAdapter
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

        async def generate_stream(
            self, messages: list[dict], **kwargs: object
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

        def count_tokens(self, messages: list[dict]) -> int:
            result = litellm.token_counter(model=self._litellm_model, messages=messages)
            return result if isinstance(result, int) else result.total_tokens
    ```

    **Update `packages/centinela-core/src/centinela/core/llm/__init__.py`:**
    Add the 4 adapter classes and factory helper to the exports:

    ```python
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

    def create_provider(provider: str, config: ProviderConfig) -> UniversalProviderAdapter:
        """Convenience: create a registered provider adapter."""
        return ProviderFactory.create(provider, config)

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
    ```

    IMPORTANT NOTES:
    - OllamaAdapter does NOT extract api_key — it only passes api_base. If both are None, LiteLLM uses its defaults.
    - CustomEndpointAdapter uses `openai/` prefix (LiteLLM convention) + custom api_base pointing to the endpoint
    - The `generate()`, `generate_stream()`, and `count_tokens()` bodies follow EXACTLY the same pattern across all 4 adapters — this is intentional to guarantee identical behavior
    - Do NOT factor out a shared base class beyond UniversalProviderAdapter — duplicated method bodies are acceptable and make each adapter independently testable
    - LiteLLM's `token_counter()` handles provider-specific tokenization automatically based on the model prefix
  </verify>
  <verify>
    python -c "
    from centinela.core.llm import (
        ProviderFactory, create_provider, list_providers,
        OpenAIAdapter, AnthropicAdapter, OllamaAdapter, CustomEndpointAdapter
    )
    # Verify all 4 providers registered
    providers = list_providers()
    assert 'openai' in providers
    assert 'anthropic' in providers
    assert 'ollama' in providers
    assert 'custom' in providers
    assert len(providers) >= 4
    # Verify factory creates correct types
    from centinela.core.llm.types import ProviderConfig
    oa = create_provider('openai', ProviderConfig(model='gpt-4o'))
    assert isinstance(oa, OpenAIAdapter)
    an = create_provider('anthropic', ProviderConfig(model='claude-3-5-sonnet-20241022'))
    assert isinstance(an, AnthropicAdapter)
    ol = create_provider('ollama', ProviderConfig(model='llama3', api_base='http://localhost:11434'))
    assert isinstance(ol, OllamaAdapter)
    cu = create_provider('custom', ProviderConfig(model='mistral', api_base='http://0.0.0.0:4000'))
    assert isinstance(cu, CustomEndpointAdapter)
    # Verify providers match
    assert oa.provider == 'openai'
    assert an.provider == 'anthropic'
    assert ol.provider == 'ollama'
    assert cu.provider == 'custom'
    print('All 4 adapters registered and factory creates correct types')
    "
  </verify>
  <done>
    All 4 adapters registered with ProviderFactory. Factory.create() returns correct type for each provider. Convenience functions list_providers() and create_provider() exported from module namespace.
  </done>
</task>

</tasks>

<verification>
Run after `uv sync`:

```bash
# 1. Verify all 4 adapters import and register
python -c "
from centinela.core.llm import list_providers
providers = list_providers()
assert 'openai' in providers
assert 'anthropic' in providers
assert 'ollama' in providers
assert 'custom' in providers
print(f'Registered providers: {providers}')
"

# 2. Verify adapter properties
python -c "
from centinela.core.llm import OpenAIAdapter, AnthropicAdapter, OllamaAdapter, CustomEndpointAdapter
from centinela.core.llm.types import ProviderConfig

# Each adapter type should be instantiable
adapters = [
    OpenAIAdapter(ProviderConfig(model='gpt-4o')),
    AnthropicAdapter(ProviderConfig(model='claude-3-5-sonnet-20241022')),
    OllamaAdapter(ProviderConfig(model='llama3', api_base='http://localhost:11434')),
    CustomEndpointAdapter(ProviderConfig(model='mistral', api_base='http://0.0.0.0:4000')),
]
for a in adapters:
    assert hasattr(a, 'generate')
    assert hasattr(a, 'generate_stream')
    assert hasattr(a, 'count_tokens')
    assert a.model != ''
    assert a.provider != ''
print('All 4 adapters implement full interface')
"

# 3. Verify mypy passes
uv run mypy packages/centinela-core/
```

NOTE: Tests that call generate() with real LiteLLM will fail without API keys. That's expected — this plan only verifies structure, type, and registration. Actual generate() behavior is tested in Plan 03 with mocks.
</verification>

<success_criteria>
- All 4 adapters registered with ProviderFactory (list_providers() returns 4 providers)
- Factory.create('openai', ...) returns OpenAIAdapter instance
- Factory.create('anthropic', ...) returns AnthropicAdapter instance
- Factory.create('ollama', ...) returns OllamaAdapter instance
- Factory.create('custom', ...) returns CustomEndpointAdapter instance
- All 4 adapters implement generate(), generate_stream(), count_tokens()
- All 4 adapter `.provider` properties return correct strings
- `uv run mypy packages/centinela-core/` returns zero type errors
- 4 adapter files + 1 updated __init__.py exist on disk
</success_criteria>

<output>
After completion, create `.planning/phases/02-red-teaming-engine/02-red-teaming-engine-02-SUMMARY.md`
</output>
