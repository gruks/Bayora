---
phase: 02-red-teaming-engine
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - packages/centinela-core/pyproject.toml
  - packages/centinela-core/src/centinela/core/__init__.py
  - packages/centinela-core/src/centinela/core/llm/__init__.py
  - packages/centinela-core/src/centinela/core/llm/types.py
  - packages/centinela-core/src/centinela/core/llm/base.py
  - packages/centinela-core/src/centinela/core/llm/secure_key.py
  - packages/centinela-core/src/centinela/core/llm/factory.py
autonomous: true
user_setup: []

must_haves:
  truths:
    - "Developer can import NormalizedResponse, NormalizedChunk, TokenUsage, ProviderConfig from centinela.core.llm"
    - "Developer can subclass UniversalProviderAdapter ABC — calling abstract methods raises TypeError"
    - "Developer can store API key via SecureKeyStore context manager — key is zeroed on exit (verified by is_zeroed)"
    - "Developer can register and create adapter instances via ProviderFactory.create()"
    - "Developer can list registered providers via ProviderFactory.list_providers()"
  artifacts:
    - path: "packages/centinela-core/pyproject.toml"
      provides: "centinela-core package definition with litellm dependency"
      contains: "litellm>=1.84.0"
    - path: "packages/centinela-core/src/centinela/core/__init__.py"
      provides: "centinela.core sub-package init"
    - path: "packages/centinela-core/src/centinela/core/llm/__init__.py"
      provides: "LLM adapter module public API exports"
    - path: "packages/centinela-core/src/centinela/core/llm/types.py"
      provides: "NormalizedResponse, NormalizedChunk, TokenUsage, ProviderConfig, exceptions"
    - path: "packages/centinela-core/src/centinela/core/llm/base.py"
      provides: "UniversalProviderAdapter ABC with generate(), generate_stream(), count_tokens()"
    - path: "packages/centinela-core/src/centinela/core/llm/secure_key.py"
      provides: "SecureKeyStore — bytearray + memoryview with deterministic zeroing"
    - path: "packages/centinela-core/src/centinela/core/llm/factory.py"
      provides: "ProviderFactory — decorator-based registry + create() method"
  key_links:
    - from: "centinela.core.llm.base"
      to: "centinela.core.llm.types"
      via: "import NormalizedResponse, NormalizedChunk"
      pattern: "from .types import"
    - from: "centinela.core.llm.secure_key"
      to: "bytearray + memoryview"
      via: "bytearray(self._key.encode()) -> memoryview(ba) -> mv.cast('B')"
      pattern: "bytearray\\(.*encode"
    - from: "centinela.core.llm.factory"
      to: "centinela.core.llm.base"
      via: "import UniversalProviderAdapter"
      pattern: "from .base import"
    - from: "centinela.core.llm.factory"
      to: "litellm"
      via: "litellm.num_retries=3, litellm.retry_strategy='exponential_backoff_retry'"
      pattern: "litellm\\.(num_retries|retry_strategy)"
---

<objective>
Create the core LLM infrastructure module inside `centinela-core`: normalized type system, abstract base class, secure key store with memoryview zeroing, and provider factory with decorator-based registry.

Purpose: Establishes the data contracts (what all adapters must return), the interface contract (what all adapters must implement), the security contract (how keys are held in RAM and zeroed), and the instantiation contract (how adapters are discovered and created). Every subsequent adapter depends on these foundations.

Output: 8 files — pyproject.toml (modified), 1 package init, 1 subpackage init, 4 core modules.
</objective>

<execution_context>
@C:/Users/HP/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/HP/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/phases/02-red-teaming-engine/02-CONTEXT.md
@.planning/phases/02-red-teaming-engine/02-RESEARCH.md

Key decisions from CONTEXT.md (LOCKED — do not revisit):
- **LiteLLM** is the underlying gateway library
- **memoryview** for RAM-only key storage with deterministic zeroing
- **Exponential backoff** with up to 3 retries for rate limits
- **Normalized response schema must be identical** across all 4 adapters

From RESEARCH.md §Adapter Pattern Recommendation:
- Use `@dataclass` for ProviderConfig, pydantic BaseModel for response types
- ABC with abstract methods: generate(), generate_stream(), count_tokens()
- Factory with decorator-based `@ProviderFactory.register("provider_name")`
- `litellm.num_retries=3` and `litellm.retry_strategy="exponential_backoff_retry"` set globally

Existing code structure:
- centinela-core at `packages/centinela-core/src/centinela/`
- Already has `__init__.py` and `models.py`
- No `core/` subpackage exists yet — this plan creates it
</context>

<tasks>

<task type="auto">
  <name>Task 1: Module structure, type system, and abstract base class</name>
  <files>
    packages/centinela-core/pyproject.toml
    packages/centinela-core/src/centinela/core/__init__.py
    packages/centinela-core/src/centinela/core/llm/__init__.py
    packages/centinela-core/src/centinela/core/llm/types.py
    packages/centinela-core/src/centinela/core/llm/base.py
  </files>
  <action>
    **1. Modify `packages/centinela-core/pyproject.toml`:**
    Add `"litellm>=1.84.0"` to the `[project.dependencies]` list. Result should look like:
    ```toml
    dependencies = [
        "pydantic>=2.0",
        "litellm>=1.84.0",
    ]
    ```

    **2. Create `packages/centinela-core/src/centinela/core/__init__.py`:**
    ```python
    """CENTINELA core sub-package — LLM adapters, types, and provider infrastructure."""
    ```

    **3. Create `packages/centinela-core/src/centinela/core/llm/__init__.py`:**
    ```python
    """Universal provider adapter — normalized LLM access across all providers."""
    from .types import NormalizedChunk, NormalizedResponse, ProviderConfig, TokenUsage
    from .base import UniversalProviderAdapter
    from .secure_key import SecureKeyStore
    from .factory import ProviderFactory

    __all__ = [
        "NormalizedResponse",
        "NormalizedChunk",
        "TokenUsage",
        "ProviderConfig",
        "UniversalProviderAdapter",
        "SecureKeyStore",
        "ProviderFactory",
    ]
    ```

    **4. Create `packages/centinela-core/src/centinela/core/llm/types.py`:**
    This file defines ALL shared data types and exceptions. Use pydantic BaseModel for response types, dataclass for ProviderConfig.

    ```python
    from __future__ import annotations

    from dataclasses import dataclass, field
    from typing import AsyncIterator

    from pydantic import BaseModel


    # ── Normalized Response Types ──────────────────────────────────────
    # These are what every adapter returns, regardless of provider.
    # Identical schema across all 4 adapters per user decision.


    class TokenUsage(BaseModel):
        """Token usage statistics normalized across all providers."""
        prompt_tokens: int = 0
        completion_tokens: int = 0
        total_tokens: int = 0


    class NormalizedResponse(BaseModel):
        """Unified response format for all LLM provider adapters."""
        content: str
        model: str
        provider: str
        usage: TokenUsage = TokenUsage()
        cost: float | None = None


    class NormalizedChunk(BaseModel):
        """A single streaming chunk, normalized across providers."""
        content: str | None = None
        finish_reason: str | None = None


    # ── Provider Configuration ─────────────────────────────────────────


    @dataclass
    class ProviderConfig:
        """Configuration required to instantiate a provider adapter.

        The api_key is stored as a memoryview for RAM-only security.
        Pass None for Ollama (no key needed) or if key is managed externally.
        """
        model: str
        api_key: memoryview | None = None
        api_base: str | None = None
        max_retries: int = 3
        timeout: float = 60.0


    # ── Custom Exceptions ──────────────────────────────────────────────
    # Beyond these, adapters may re-raise litellm exceptions directly.


    class ProviderError(Exception):
        """Base exception for all provider adapter errors."""

    class RateLimitError(ProviderError):
        """Rate limit exceeded — retries exhausted."""

    class AuthenticationError(ProviderError):
        """Invalid or missing API key."""

    class TokenCountError(ProviderError):
        """Token counting failed for the given input."""
    ```

    **5. Create `packages/centinela-core/src/centinela/core/llm/base.py`:**
    ```python
    from __future__ import annotations

    from abc import ABC, abstractmethod
    from typing import AsyncIterator

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
        def generate(self, messages: list[dict], **kwargs: object) -> NormalizedResponse:
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
        async def generate_stream(self, messages: list[dict], **kwargs: object) -> AsyncIterator[NormalizedChunk]:
            """Streaming text generation.

            Args:
                messages: List of message dicts with 'role' and 'content' keys.
                **kwargs: Additional provider-specific parameters.

            Yields:
                NormalizedChunk for each streaming delta.
            """
            ...
            yield  # pragma: no cover — marker for async generator

        @abstractmethod
        def count_tokens(self, messages: list[dict]) -> int:
            """Count the number of tokens in the given messages.

            Args:
                messages: List of message dicts.

            Returns:
                Total token count as an integer.
            """
            ...
    ```

    IMPORTANT GUIDELINES:
    - Use `from __future__ import annotations` in every `.py` file (PEP 563 — enables forward references, avoids runtime string annotation evaluation)
    - All pydantic models use `class Config: frozen = True` to enforce immutability for security-sensitive data
    - ProviderConfig stores `api_key: memoryview | None` — the `memoryview` type hint works in Python 3.12+ without issues
    - Type hints use `str | None` (not `Optional[str]`) — project targets Python 3.12+
    - Do NOT add any provider-specific logic in base.py — it is purely abstract
  </action>
  <verify>
    python -c "from centinela.core.llm import NormalizedResponse, NormalizedChunk, TokenUsage, ProviderConfig, UniversalProviderAdapter; print('Types and ABC import OK')"
    python -c "from centinela.core.llm.base import UniversalProviderAdapter; issubclass(type('X', (UniversalProviderAdapter,), {}), UniversalProviderAdapter)"
    grep "litellm" packages/centinela-core/pyproject.toml  # Dependency added
  </verify>
  <done>
    Types module defines NormalizedResponse, NormalizedChunk, TokenUsage, ProviderConfig, and exceptions. ABC defines generate(), generate_stream(), count_tokens(). Module structure under centinela/core/llm/ is importable. litellm dependency added to centinela-core.
  </done>
</task>

<task type="auto">
  <name>Task 2: SecureKeyStore — memoryview-backed RAM-only key storage</name>
  <files>
    packages/centinela-core/src/centinela/core/llm/secure_key.py
  </files>
  <action>
    Create `packages/centinela-core/src/centinela/core/llm/secure_key.py`:

    Implement SecureKeyStore class using the bytearray + memoryview pattern verified in research. This is the ONLY mechanism for holding API keys — never use str or bytes for key storage.

    ```python
    from __future__ import annotations


    class SecureKeyStore:
        """RAM-only API key storage using memoryview with deterministic zeroing.

        Usage:
            key = "sk-..."
            with SecureKeyStore(key) as store:
                # key is accessible via store.get_str() or store.get_view()
                api_key_str = store.get_str()
                # ... use api_key_str (e.g. pass to litellm) ...
            # After context exit: key is zeroed, get_str() returns empty string

        Security properties:
        - Key stored as bytearray (mutable, controllable memory)
        - memoryview wraps bytearray for zero-copy access
        - .clear() zeroes all bytes then releases the memoryview
        - __del__ provides safety net if context manager not used
        - is_zeroed property enables verification in tests
        """

        def __init__(self, key: str) -> None:
            if not isinstance(key, str):
                raise TypeError("API key must be a string")
            self._buf = bytearray(key.encode("utf-8"))
            self._view = memoryview(self._buf)
            self._released = False

        def get_view(self) -> memoryview:
            """Return the memoryview for zero-copy access."""
            if self._released:
                raise RuntimeError("SecureKeyStore has already been cleared")
            return self._view

        def get_str(self) -> str:
            """Reconstruct the key string from the bytearray backing store.

            Note: This creates a new str object. The caller is responsible
            for not letting this string persist beyond its useful lifetime.
            """
            if self._released:
                return ""
            return self._buf.decode("utf-8")

        def clear(self) -> None:
            """Zero all key bytes and release the memoryview.

            Safe to call multiple times — subsequent calls are no-ops.
            """
            if self._released:
                return
            # Zero every byte in the buffer
            self._view.cast("B")[:] = b"\x00" * len(self._buf)
            self._view.release()
            self._released = True
            # Also zero the backing bytearray
            self._buf[:] = b"\x00" * len(self._buf)

        @property
        def is_zeroed(self) -> bool:
            """True if memory has been cleared and view released."""
            if not self._released:
                return False
            return all(b == 0 for b in self._buf)

        @property
        def is_active(self) -> bool:
            """True if key is still accessible (not yet cleared)."""
            return not self._released

        def __enter__(self) -> SecureKeyStore:
            return self

        def __exit__(self, *args: object) -> None:
            self.clear()

        def __del__(self) -> None:
            """Safety net: clear if context manager wasn't used."""
            if not self._released:
                self.clear()

        def __repr__(self) -> str:
            status = "active" if self.is_active else "zeroed"
            return f"<SecureKeyStore: {status}>"
    ```

    IMPORTANT:
    - `memoryview.cast('B')` returns a byte-oriented view — assigning `b'\x00' * len` guarantees every byte is zeroed
    - `view.release()` detaches the memoryview from the underlying buffer, preventing further access
    - The `__del__` safety net means even if the caller forgets the context manager, the key gets cleared on garbage collection
    - Python's `bytearray` is mutable and its memory is not automatically zeroed on deallocation, so explicit zeroing is essential
    - Do NOT add any `str` caching — the key string should only exist in the bytearray and be reconstructed on demand via `get_str()`
  </verify>
  <verify>
    python -c "
    from centinela.core.llm.secure_key import SecureKeyStore
    import gc
    # Test basic lifecycle
    ks = SecureKeyStore('sk-test-key-12345')
    assert ks.is_active
    assert ks.get_str() == 'sk-test-key-12345'
    assert len(ks.get_view()) == len('sk-test-key-12345')
    ks.clear()
    assert ks.is_zeroed
    assert ks.get_str() == ''
    assert not ks.is_active
    # Test context manager
    with SecureKeyStore('sk-context-test') as ks2:
        assert ks2.get_str() == 'sk-context-test'
    assert ks2.is_zeroed
    # Test double clear is safe
    ks2.clear()  # no error
    print('All SecureKeyStore tests passed')
    "
  </verify>
  <done>
    SecureKeyStore stores key in bytearray with memoryview wrapper. Context manager zeroes on exit. Double clear is safe. Isolated in dedicated module with no side effects.
  </done>
</task>

<task type="auto">
  <name>Task 3: ProviderFactory — decorator-based registry with LiteLLM retry configuration</name>
  <files>
    packages/centinela-core/src/centinela/core/llm/factory.py
  </files>
  <action>
    Create `packages/centinela-core/src/centinela/core/llm/factory.py`:

    ProviderFactory uses a class-level registry populated by a decorator on each adapter. This allows adapters to be defined in separate files and auto-register themselves.

    Configure LiteLLM's global retry settings at module import time per user decision (exponential backoff, 3 retries).

    ```python
    from __future__ import annotations

    import litellm
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from .base import UniversalProviderAdapter
        from .types import ProviderConfig

    # ── Global LiteLLM Configuration ──────────────────────────────
    # Per user decision: exponential backoff with up to 3 retries for rate limits.
    # These are set at module import time so all adapters inherit them.
    litellm.num_retries = 3
    litellm.retry_strategy = "exponential_backoff_retry"
    # ── Retryable status codes ──
    # RateLimitError (429), ServiceUnavailableError (503), Timeout (408), InternalServerError (500)
    # litellm handles these internally based on exception mapping.


    class ProviderFactory:
        """Decorator-based registry for LLM provider adapters.

        Usage:
            @ProviderFactory.register("openai")
            class OpenAIAdapter(UniversalProviderAdapter):
                ...

            @ProviderFactory.register("anthropic")
            class AnthropicAdapter(UniversalProviderAdapter):
                ...

            # Later:
            adapter = ProviderFactory.create("openai", config)
        """

        _registry: dict[str, type[UniversalProviderAdapter]] = {}

        @classmethod
        def register(cls, provider: str) -> type["UniversalProviderAdapter"]:
            """Decorator that registers an adapter class for the given provider name.

            Usage:
                @ProviderFactory.register("openai")
                class OpenAIAdapter(UniversalProviderAdapter): ...

            The provider name becomes the key used in create().
            """
            def inner(wrapper: type[UniversalProviderAdapter]) -> type[UniversalProviderAdapter]:
                cls._registry[provider] = wrapper
                return wrapper
            return inner

        @classmethod
        def create(cls, provider: str, config: "ProviderConfig") -> "UniversalProviderAdapter":
            """Instantiate a registered adapter for the given provider.

            Args:
                provider: Provider name (e.g. 'openai', 'anthropic', 'ollama', 'custom').
                config: ProviderConfig with model, api_key, api_base, etc.

            Returns:
                Configured adapter instance ready for generate() calls.

            Raises:
                ValueError: If provider is not registered.
            """
            adapter_cls = cls._registry.get(provider)
            if adapter_cls is None:
                registered = ", ".join(sorted(cls._registry))
                raise ValueError(
                    f"Unknown provider: '{provider}'. "
                    f"Registered providers: {registered}"
                )
            return adapter_cls(config)

        @classmethod
        def list_providers(cls) -> list[str]:
            """Return sorted list of registered provider names."""
            return sorted(cls._registry)
    ```

    IMPORTANT:
    - Set `litellm.num_retries = 3` and `litellm.retry_strategy = "exponential_backoff_retry"` at module level — research confirms these are the correct LiteLLM attributes for exponential backoff with retries
    - The `# type: ignore` on `if TYPE_CHECKING` block is NOT needed — the module correctly uses runtime imports only for litellm (which we need at runtime)
    - Use `TYPE_CHECKING` guard for base and types imports to avoid circular imports (adapters import from base, factory imports from base — circular!)

    Wait — let me reconsider. The factory module needs to import the ABC and ProviderConfig at runtime for type hints and create(). But the adapters also import from factory (to use the decorator). This creates a circular dependency:
    - base.py → types.py (no cycle)
    - factory.py → types.py, base.py
    - openai_adapter.py → base.py, types.py, factory.py (factory imports base, adapter imports factory = cycle!)

    To avoid the circular import, use late-binding in the factory:
    - Import `UniversalProviderAdapter` and `ProviderConfig` inside the `create()` method body, not at the top of the module
    - Only import `litellm` at the top level (needed for global config at import time)

    Here's the corrected approach (use this instead of the code above):

    ```python
    from __future__ import annotations

    import litellm

    # ── Global LiteLLM Configuration ──────────────────────────────
    litellm.num_retries = 3
    litellm.retry_strategy = "exponential_backoff_retry"


    class ProviderFactory:
        """Decorator-based registry for LLM provider adapters.

        Uses late imports to avoid circular dependencies:
        adapters import factory (for @register), factory imports base (for type hints).
        """

        _registry: dict[str, type] = {}

        @classmethod
        def register(cls, provider: str):
            """Decorator that registers an adapter class for the given provider name."""
            def inner(wrapper: type) -> type:
                cls._registry[provider] = wrapper
                return wrapper
            return inner

        @classmethod
        def create(cls, provider: str, config: object):
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
                raise ValueError(
                    f"Unknown provider: '{provider}'. "
                    f"Registered providers: {registered}"
                )
            if not issubclass(adapter_cls, UniversalProviderAdapter):
                raise TypeError(f"'{provider}' adapter does not implement UniversalProviderAdapter")
            return adapter_cls(config)

        @classmethod
        def list_providers(cls) -> list[str]:
            """Return sorted list of registered provider names."""
            return sorted(cls._registry)
    ```

    This uses late imports in `create()` to break the cycle while still enforcing type safety via runtime isinstance checks.

    Double-check this solves the circular import:
    - openai_adapter.py imports: base.py (ABC), types.py (types), factory.py (register decorator)
    - factory.py does NOT import base.py or types.py at module level — only inside method bodies
    - Result: NO cycle ✓
  </action>
  <verify>
    python -c "
    from centinela.core.llm import ProviderFactory
    # Verify litellm global config was set
    import litellm
    assert litellm.num_retries == 3, f'Expected 3 got {litellm.num_retries}'
    assert litellm.retry_strategy == 'exponential_backoff_retry', f'Expected exponential_backoff_retry got {litellm.retry_strategy}'
    # Verify empty registry
    assert ProviderFactory.list_providers() == []
    # Verify create raises ValueError for unknown provider
    from centinela.core.llm.types import ProviderConfig
    try:
        ProviderFactory.create('unknown', ProviderConfig(model='test'))
        assert False, 'Should have raised ValueError'
    except ValueError:
        pass
    print('Factory and litellm config verified')
    "
  </verify>
  <done>
    ProviderFactory correctly reads LiteLLM global config. Registry starts empty. create() validates input and raises ValueError + TypeError for invalid providers/config. Late imports prevent circular dependency.
  </done>
</task>

</tasks>

<verification>
Run these in sequence after `uv sync`:

```bash
# 1. Verify all type imports work
python -c "
from centinela.core.llm import (
    NormalizedResponse, NormalizedChunk, TokenUsage,
    ProviderConfig, UniversalProviderAdapter, SecureKeyStore, ProviderFactory
)
print('All imports OK')
"

# 2. Verify SecureKeyStore lifecycle
python -c "
from centinela.core.llm import SecureKeyStore
with SecureKeyStore('sk-test-key') as ks:
    assert ks.get_str() == 'sk-test-key'
assert ks.is_zeroed
print('SecureKeyStore lifecycle OK')
"

# 3. Verify Factory + litellm config
python -c "
from centinela.core.llm import ProviderFactory
import litellm
assert litellm.num_retries == 3
assert litellm.retry_strategy == 'exponential_backoff_retry'
assert ProviderFactory.list_providers() == []
print('Factory + litellm config OK')
"

# 4. Verify ABC cannot be instantiated directly
python -c "
from centinela.core.llm import UniversalProviderAdapter
try:
    UniversalProviderAdapter()
    assert False, 'ABC should raise TypeError'
except TypeError:
    print('ABC protection OK')
"

# 5. Verify mypy passes
uv run mypy packages/centinela-core/
```
</verification>

<success_criteria>
- All imports from `centinela.core.llm` resolve without errors
- SecureKeyStore passes lifecycle test: create → use → clear → verify zeroed
- ProviderFactory registers nothing initially, litellm retry config set to 3 retries + exponential backoff
- UniversalProviderAdapter ABC raises TypeError on direct instantiation
- `uv run mypy packages/centinela-core/` returns zero type errors
- 7 new files + 1 modified pyproject.toml all exist on disk
</success_criteria>

<output>
After completion, create `.planning/phases/02-red-teaming-engine/02-red-teaming-engine-01-SUMMARY.md`
</output>
