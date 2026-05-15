---
phase: 02-red-teaming-engine
plan: 03
type: execute
wave: 3
depends_on: ["01", "02"]
files_modified:
  - packages/centinela-core/tests/__init__.py
  - packages/centinela-core/tests/llm/__init__.py
  - packages/centinela-core/tests/llm/test_types.py
  - packages/centinela-core/tests/llm/test_secure_key.py
  - packages/centinela-core/tests/llm/test_factory.py
  - packages/centinela-core/tests/llm/test_base.py
  - packages/centinela-core/tests/llm/test_adapters.py
autonomous: true
user_setup: []

must_haves:
  truths:
    - "All tests pass: `uv run pytest packages/centinela-core/tests/` returns exit code 0"
    - "SecureKeyStore zeroing is verified: tests prove bytes are cleared after context exit"
    - "ProviderFactory correctly registers all 4 adapters and validates unknown providers"
    - "ABC raises TypeError when instantiated directly, and all abstract methods enforced"
    - "All 4 adapter properties (model, provider) return correct values"
    - "NormalizedResponse schema is identical across all 4 adapter output paths"
    - "Provider instantiation benchmark <500ms when mocked to simulate fast path"
    - "Mypy passes on tests directory: `uv run mypy packages/centinela-core/tests/`"
  artifacts:
    - path: "packages/centinela-core/tests/__init__.py"
      provides: "Test package marker"
    - path: "packages/centinela-core/tests/llm/__init__.py"
      provides: "LLM test sub-package marker"
    - path: "packages/centinela-core/tests/llm/test_types.py"
      provides: "NormalizedResponse/NormalizedChunk/TokenUsage/ProviderConfig validation tests"
    - path: "packages/centinela-core/tests/llm/test_secure_key.py"
      provides: "SecureKeyStore lifecycle, zeroing, and safety tests"
    - path: "packages/centinela-core/tests/llm/test_factory.py"
      provides: "ProviderFactory registration, creation, and error handling tests"
    - path: "packages/centinela-core/tests/llm/test_base.py"
      provides: "ABC interface enforcement tests"
    - path: "packages/centinela-core/tests/llm/test_adapters.py"
      provides: "Adapter property tests, LiteLLM mocking, schema consistency, benchmark"
  key_links:
    - from: "test_secure_key.py"
      to: "centinela.core.llm.secure_key.SecureKeyStore"
      via: "import + lifecycle tests"
      pattern: "from centinela.core.llm import SecureKeyStore"
    - from: "test_factory.py"
      to: "centinela.core.llm.factory.ProviderFactory"
      via: "import + registration/create tests"
      pattern: "from centinela.core.llm import ProviderFactory"
    - from: "test_base.py"
      to: "centinela.core.llm.base.UniversalProviderAdapter"
      via: "ABC enforcement tests"
      pattern: "from centinela.core.llm import UniversalProviderAdapter"
    - from: "test_adapters.py"
      to: "centinela.core.llm.*_adapter"
      via: "import all 4 adapters + mock litellm"
      pattern: "from centinela.core.llm import.*Adapter"
    - from: "test_adapters.py"
      to: "litellm.completion"
      via: "mock.patch('litellm.completion')"
      pattern: "mock.patch.*litellm"
---

<objective>
Create the comprehensive test suite for the universal provider adapter module: unit tests for every component with mocked LiteLLM calls, schema consistency verification across all 4 adapters, SecureKeyStore memory zeroing validation, ProviderFactory edge case coverage, and a provider instantiation benchmark.

Purpose: Every acceptance criterion in Phase 02 must have an automated test. Tests run without real API keys (LiteLLM is mocked). The test suite integrates with the existing pytest infrastructure and verifies that all 6 acceptance criteria are met before marking Phase 02 complete.

Output: 7 test files — types, secure_key, factory, base, adapters, plus test package markers.
</objective>

<execution_context>
@C:/Users/HP/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/HP/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/02-red-teaming-engine/02-CONTEXT.md
@.planning/phases/02-red-teaming-engine/02-RESEARCH.md

Locked decisions (from CONTEXT.md):
- LiteLLM is the gateway — adapters call litellm.completion()
- memoryview for RAM-only key storage with deterministic zeroing
- Exponential backoff with up to 3 retries (configured globally in factory.py)
- Normalized response schema IDENTICAL across all 4 adapters

Adapter test strategy (from RESEARCH.md):
- Each adapter wraps LiteLLM with a model prefix: openai/, anthropic/, ollama/
- CustomEndpointAdapter uses openai/ prefix with custom api_base
- Litellm normalizes response shapes internally
- SecureKeyStore uses bytearray + memoryview + .clear() zeroing

Existing plans:
- Plan 01: Created types.py (NormalizedResponse, NormalizedChunk, TokenUsage, ProviderConfig, exceptions), base.py (UniversalProviderAdapter ABC), secure_key.py (SecureKeyStore), factory.py (ProviderFactory + litellm config)
- Plan 02: Created openai_adapter.py, anthropic_adapter.py, ollama_adapter.py, custom_adapter.py

Phase 1 project structure:
- Root-level testpaths = ["tests"] in pyproject.toml (but no root tests/ dir exists)
- Services have their tests at services/*/tests/test_stub.py
- centinela-core tests go in packages/centinela-core/tests/ — run via explicit path

Mocking approach:
- Use unittest.mock.patch to mock litellm.completion() and litellm.acompletion()
- Each mocked call returns a minimal response with .choices[0].message.content and .usage
- Token counting tests mock litellm.token_counter() to return an int
- No real API keys needed — tests use dummy key strings
</context>

<tasks>

<task type="auto">
  <name>Task 1: Core infrastructure tests — types, SecureKeyStore, ProviderFactory, ABC</name>
  <files>
    packages/centinela-core/tests/__init__.py
    packages/centinela-core/tests/llm/__init__.py
    packages/centinela-core/tests/llm/test_types.py
    packages/centinela-core/tests/llm/test_secure_key.py
    packages/centinela-core/tests/llm/test_factory.py
    packages/centinela-core/tests/llm/test_base.py
  </files>
  <action>
    Create 6 files for the core infrastructure test suite.

    **1. `packages/centinela-core/tests/__init__.py`:**
    ```python
    """Tests for centinela-core package."""
    ```

    **2. `packages/centinela-core/tests/llm/__init__.py`:**
    ```python
    """Tests for centinela.core.llm — universal provider adapter."""
    ```

    **3. `packages/centinela-core/tests/llm/test_types.py`:**
    Tests for NormalizedResponse, NormalizedChunk, TokenUsage, ProviderConfig dataclasses/models:

    ```python
    """Tests for normalized types and configuration models."""

    from __future__ import annotations

    from centinela.core.llm import NormalizedChunk, NormalizedResponse, TokenUsage
    from centinela.core.llm.types import ProviderConfig


    class TestTokenUsage:
        """TokenUsage pydantic model validation."""

        def test_defaults(self) -> None:
            usage = TokenUsage()
            assert usage.prompt_tokens == 0
            assert usage.completion_tokens == 0
            assert usage.total_tokens == 0

        def test_all_fields(self) -> None:
            usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
            assert usage.prompt_tokens == 10
            assert usage.completion_tokens == 20
            assert usage.total_tokens == 30


    class TestNormalizedResponse:
        """NormalizedResponse — the unified return type for all adapters."""

        def test_minimal(self) -> None:
            resp = NormalizedResponse(content="Hello", model="gpt-4o", provider="openai")
            assert resp.content == "Hello"
            assert resp.model == "gpt-4o"
            assert resp.provider == "openai"
            assert resp.usage.prompt_tokens == 0
            assert resp.cost is None

        def test_with_usage_and_cost(self) -> None:
            resp = NormalizedResponse(
                content="Test response",
                model="claude-3-5-sonnet-20241022",
                provider="anthropic",
                usage=TokenUsage(prompt_tokens=15, completion_tokens=25, total_tokens=40),
                cost=0.002,
            )
            assert resp.cost == 0.002
            assert resp.usage.total_tokens == 40

        def test_serialization(self) -> None:
            """Verify pydantic model_dump() works (needed for JSON serialization)."""
            resp = NormalizedResponse(content="Hi", model="llama3", provider="ollama")
            data = resp.model_dump()
            assert data["content"] == "Hi"
            assert data["provider"] == "ollama"


    class TestNormalizedChunk:
        """Streaming chunk type."""

        def test_content_chunk(self) -> None:
            chunk = NormalizedChunk(content="Hello")
            assert chunk.content == "Hello"
            assert chunk.finish_reason is None

        def test_finish_chunk(self) -> None:
            chunk = NormalizedChunk(content=None, finish_reason="stop")
            assert chunk.content is None
            assert chunk.finish_reason == "stop"

        def test_empty_chunk(self) -> None:
            chunk = NormalizedChunk()
            assert chunk.content is None
            assert chunk.finish_reason is None


    class TestProviderConfig:
        """Provider configuration dataclass."""

        def test_minimal(self) -> None:
            config = ProviderConfig(model="gpt-4o")
            assert config.model == "gpt-4o"
            assert config.api_key is None
            assert config.api_base is None
            assert config.max_retries == 3
            assert config.timeout == 60.0

        def test_with_api_key(self) -> None:
            import memoryview  # noqa: F401 — type-only check
            key = memoryview(b"sk-test-key")
            config = ProviderConfig(model="gpt-4o", api_key=key)
            assert bytes(config.api_key) == b"sk-test-key"  # type: ignore[arg-type]

        def test_with_all_fields(self) -> None:
            config = ProviderConfig(
                model="mistral",
                api_base="http://localhost:11434",
                max_retries=5,
                timeout=120.0,
            )
            assert config.api_base == "http://localhost:11434"
            assert config.max_retries == 5
            assert config.timeout == 120.0
    ```

    **4. `packages/centinela-core/tests/llm/test_secure_key.py`:**
    Tests for SecureKeyStore — the critical security primitive. Must prove memory zeroing works.

    ```python
    """Tests for SecureKeyStore — memoryview-backed RAM-only API key storage.

    These tests verify the security contract:
    - Key is stored in mutable bytearray (not immutable str/bytes)
    - memoryview wraps for zero-copy access
    - .clear() zeroes ALL bytes deterministically
    - Context manager guarantees cleanup on scope exit
    - Double clear is safe (idempotent)
    - __del__ provides safety net if context manager forgotten
    """

    from __future__ import annotations

    import gc

    from centinela.core.llm import SecureKeyStore


    class TestSecureKeyStoreLifecycle:
        """Full lifecycle: create → use → clear → verify zeroed."""

        def test_store_and_retrieve(self) -> None:
            ks = SecureKeyStore("sk-test-key-12345")
            assert ks.is_active
            assert ks.get_str() == "sk-test-key-12345"
            assert len(ks.get_view()) == len("sk-test-key-12345")
            ks.clear()
            assert ks.is_zeroed

        def test_get_str_after_clear_returns_empty(self) -> None:
            ks = SecureKeyStore("sk-secret")
            ks.clear()
            assert ks.get_str() == ""

        def test_get_view_after_clear_raises(self) -> None:
            ks = SecureKeyStore("sk-secret")
            ks.clear()
            import pytest
            with pytest.raises(RuntimeError, match="SecureKeyStore has already been cleared"):
                ks.get_view()

        def test_cannot_instantiate_with_non_string(self) -> None:
            import pytest
            with pytest.raises(TypeError, match="API key must be a string"):
                SecureKeyStore(123)  # type: ignore[arg-type]


    class TestSecureKeyStoreZeroing:
        """Memory zeroing verification — this is a security test."""

        def test_all_bytes_zeroed_after_clear(self) -> None:
            ks = SecureKeyStore("sk-this-is-a-test-key-with-enough-length")
            original_len = len(ks.get_str())
            ks.clear()
            # After clear, the underlying bytearray should be all zeros
            assert ks.is_zeroed
            # Verify the buffer length is preserved (not truncated)
            assert len(ks._buf) == original_len
            # Prove every byte is actually zero
            assert all(b == 0 for b in ks._buf)

        def test_memoryview_released_after_clear(self) -> None:
            ks = SecureKeyStore("sk-test")
            view = ks.get_view()
            ks.clear()
            # memoryview should be released — accessing it raises ValueError
            import pytest
            with pytest.raises(ValueError):
                _ = view[0]  # released memoryview access

        def test_multiple_keys_independent_zeroing(self) -> None:
            """Each SecureKeyStore manages its own buffer independently."""
            ks1 = SecureKeyStore("sk-key-one")
            ks2 = SecureKeyStore("sk-key-two")
            ks1.clear()
            assert ks1.is_zeroed
            assert ks2.is_active  # ks2 should NOT be affected
            assert ks2.get_str() == "sk-key-two"
            ks2.clear()
            assert ks2.is_zeroed


    class TestSecureKeyStoreContextManager:
        """Context manager guarantees cleanup on scope exit."""

        def test_context_manager_zeroes_on_exit(self) -> None:
            with SecureKeyStore("sk-context-key") as ks:
                assert ks.get_str() == "sk-context-key"
            assert ks.is_zeroed

        def test_context_manager_zeroes_even_on_error(self) -> None:
            """Even if an exception occurs inside the context, the key is zeroed."""
            try:
                with SecureKeyStore("sk-error-key") as ks:
                    assert ks.is_active
                    raise ValueError("simulated error")
            except ValueError:
                pass
            assert ks.is_zeroed

        def test_double_clear_is_safe(self) -> None:
            ks = SecureKeyStore("sk-double")
            ks.clear()
            ks.clear()  # Should not raise
            assert ks.is_zeroed

        def test_repr_active(self) -> None:
            ks = SecureKeyStore("sk-repr")
            assert repr(ks) == "<SecureKeyStore: active>"

        def test_repr_zeroed(self) -> None:
            ks = SecureKeyStore("sk-repr")
            ks.clear()
            assert repr(ks) == "<SecureKeyStore: zeroed>"


    class TestSecureKeyStoreDel:
        """__del__ safety net — key zeroed if context manager not used.

        NOTE: This tests best-effort behavior. CPython's GC may not call
        __del__ immediately, but when it does, the key must be zeroed.
        """

        def test_del_clears_key(self) -> None:
            ks = SecureKeyStore("sk-del-test")
            ks_ref = ks
            del ks
            gc.collect()
            assert ks_ref.is_zeroed

        def test_del_after_manual_clear_no_double_free(self) -> None:
            """If already cleared, __del__ should be a no-op."""
            ks = SecureKeyStore("sk-del-clear")
            ks.clear()
            del ks  # Should not raise
            gc.collect()
    ```

    **5. `packages/centinela-core/tests/llm/test_factory.py`:**
    Tests for ProviderFactory registry, create(), error handling, and litellm global config.

    ```python
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

        def test_starts_empty(self) -> None:
            assert ProviderFactory.list_providers() == []

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
                def __init__(self, config: ProviderConfig) -> None: self._config = config
                @property
                def model(self) -> str: return self._config.model
                @property
                def provider(self) -> str: return "first"
                def generate(self, messages: list[dict], **kwargs: object) -> object: return None
                async def generate_stream(self, messages: list[dict], **kwargs: object) -> object:
                    return None
                    yield  # pragma: no cover
                def count_tokens(self, messages: list[dict]) -> int: return 0

            @ProviderFactory.register("overwrite_test")
            class SecondAdapter(UniversalProviderAdapter):
                def __init__(self, config: ProviderConfig) -> None: self._config = config
                @property
                def model(self) -> str: return self._config.model
                @property
                def provider(self) -> str: return "second"
                def generate(self, messages: list[dict], **kwargs: object) -> object: return None
                async def generate_stream(self, messages: list[dict], **kwargs: object) -> object:
                    return None
                    yield  # pragma: no cover
                def count_tokens(self, messages: list[dict]) -> int: return 0

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
    ```

    **6. `packages/centinela-core/tests/llm/test_base.py`:**
    Tests for UniversalProviderAdapter ABC — verifies abstract methods are enforced.

    ```python
    """Tests for UniversalProviderAdapter abstract base class."""

    from __future__ import annotations

    from centinela.core.llm import UniversalProviderAdapter


    class TestUniversalProviderAdapter:
        """ABC enforcement — cannot instantiate directly, abstract methods enforced."""

        def test_cannot_instantiate_abc(self) -> None:
            """Direct instantiation of ABC must raise TypeError."""
            import pytest
            with pytest.raises(TypeError, match="Can't instantiate abstract class"):
                UniversalProviderAdapter()  # type: ignore[abstract]

        def test_missing_generate_raises(self) -> None:
            """Subclass without generate() must raise TypeError."""
            import pytest
            with pytest.raises(TypeError, match="Can't instantiate abstract class"):
                type("BadAdapter", (UniversalProviderAdapter,), {})()

        def test_missing_generate_stream_raises(self) -> None:
            """Subclass without generate_stream() must raise TypeError."""
            import pytest
            with pytest.raises(TypeError, match="Can't instantiate abstract class"):
                type("BadAdapter", (UniversalProviderAdapter,), {
                    "generate": lambda self, m, **kw: None,
                })()

        def test_missing_count_tokens_raises(self) -> None:
            """Subclass without count_tokens() must raise TypeError."""
            import pytest
            with pytest.raises(TypeError, match="Can't instantiate abstract class"):
                type("BadAdapter", (UniversalProviderAdapter,), {
                    "generate": lambda self, m, **kw: None,
                    "generate_stream": lambda self, m, **kw: None,
                })()

        def test_all_abstract_methods_enforced(self) -> None:
            """Implementing all 3 abstract methods should allow instantiation."""
            adapter = type("GoodAdapter", (UniversalProviderAdapter,), {
                "_config": None,
                "model": property(lambda self: "test"),
                "provider": property(lambda self: "test"),
                "generate": lambda self, m, **kw: None,
                "generate_stream": lambda self, m, **kw: None,
                "count_tokens": lambda self, m: 0,
            })()
            assert hasattr(adapter, "generate")
            assert hasattr(adapter, "generate_stream")
            assert hasattr(adapter, "count_tokens")
            assert adapter.model == "test"
            assert adapter.provider == "test"

        def test_abstract_method_signatures(self) -> None:
            """Verify the ABC defines correct method signatures (duck-type check)."""
            required = {"generate", "generate_stream", "count_tokens"}
            methods = {
                name for name in dir(UniversalProviderAdapter)
                if not name.startswith("_")
            }
            assert required.issubset(methods), (
                f"Missing abstract methods: {required - methods}"
            )
    ```

    IMPORTANT GUIDELINES:
    - Use `from __future__ import annotations` in every test file (PEP 563)
    - Use descriptive class names with `Test` prefix (pytest convention)
    - Each test function is a single, focused assertion
    - SecureKeyStore tests must prove actual byte-level zeroing, not just is_zeroed property
    - ProviderFactory tests clean up registry entries after themselves to avoid cross-test pollution
    - Test `test_get_view_after_clear_raises` expects `RuntimeError` — this matches SecureKeyStore's implementation
    - The `gc.collect()` in `test_del_clears_key` is needed because CPython may not call __del__ immediately
    - Memoryview availability check: Python 3.12 has `memoryview` as builtin (no import needed)
    - In `test_provider_config.py` (test_types), the memoryview test imports `memoryview` module which is the builtin — this is fine for type hint context
  </action>
  <verify>
    # Verify test infrastructure exists and imports work
    uv run python -c "from centinela.core.llm import SecureKeyStore, ProviderFactory, UniversalProviderAdapter, NormalizedResponse; print('Core infrastructure imports OK')"
    
    # Run core tests (these should pass without any mocking — they test standalone modules)
    uv run pytest packages/centinela-core/tests/llm/test_types.py packages/centinela-core/tests/llm/test_secure_key.py packages/centinela-core/tests/llm/test_factory.py packages/centinela-core/tests/llm/test_base.py -v --tb=short
    
    # Run with coverage
    uv run pytest packages/centinela-core/tests/llm/test_types.py packages/centinela-core/tests/llm/test_secure_key.py packages/centinela-core/tests/llm/test_factory.py packages/centinela-core/tests/llm/test_base.py --cov=packages/centinela-core --cov-report=term-missing
  </verify>
  <done>
    6 test files created covering types (NormalizedResponse, NormalizedChunk, TokenUsage, ProviderConfig), SecureKeyStore (lifecycle, zeroing, context manager, __del__), ProviderFactory (registration, create, error cases, litellm config), and UniversalProviderAdapter ABC (abstract method enforcement). All core tests pass without mocking.
  </done>
</task>

<task type="auto">
  <name>Task 2: Adapter unit tests — LiteLLM mocking, schema consistency, benchmark</name>
  <files>
    packages/centinela-core/tests/llm/test_adapters.py
  </files>
  <action>
    Create `packages/centinela-core/tests/llm/test_adapters.py` with comprehensive adapter tests.

    This file mocks LiteLLM to test adapter behavior without real API keys. The critical tests are:
    - Every adapter's `.model` and `.provider` properties return correct values
    - `_get_api_kwargs()` produces correct kwargs dict for each adapter type
    - `generate()` returns a properly constructed `NormalizedResponse`
    - `count_tokens()` delegates to `litellm.token_counter()`
    - All 4 adapters produce the same NormalizedResponse schema shape
    - Provider instantiation takes <500ms (benchmark test)

    ```python
    """Tests for all 4 provider adapters with mocked LiteLLM.

    These tests verify:
    1. Adapter properties (model, provider) return correct values
    2. _get_api_kwargs() builds correct kwargs for different configs
    3. generate() returns properly shaped NormalizedResponse
    4. count_tokens() delegates correctly
    5. All 4 adapters produce identical schema (Acceptance Criterion 1)
    6. Provider instantiation completes within 500ms (Acceptance Criterion 6)
    """

    from __future__ import annotations

    from typing import Any, AsyncIterator
    from unittest import mock

    import pytest

    from centinela.core.llm import (
        AnthropicAdapter,
        CustomEndpointAdapter,
        NormalizedResponse,
        OllamaAdapter,
        OpenAIAdapter,
        ProviderFactory,
    )
    from centinela.core.llm.types import ProviderConfig


    # ── Mock LiteLLM Response Helpers ──────────────────────────────────────


    def _make_mock_choice(message_content: str, finish_reason: str | None = "stop") -> mock.MagicMock:
        """Build a mock LiteLLM choice object."""
        choice = mock.MagicMock()
        choice.message.content = message_content
        choice.finish_reason = finish_reason
        return choice


    def _make_mock_chunk_delta(content: str | None, finish_reason: str | None = None) -> mock.MagicMock:
        """Build a mock LiteLLM streaming chunk delta."""
        delta = mock.MagicMock()
        delta.content = content
        return delta


    def _make_mock_usage(
        prompt_tokens: int = 10,
        completion_tokens: int = 20,
        total_tokens: int = 30,
    ) -> mock.MagicMock:
        """Build a mock LiteLLM usage object."""
        usage = mock.MagicMock()
        usage.prompt_tokens = prompt_tokens
        usage.completion_tokens = completion_tokens
        usage.total_tokens = total_tokens
        return usage


    def _make_mock_completion_response(
        content: str = "Test response",
        model: str = "openai/gpt-4o",
        finish_reason: str = "stop",
        prompt_tokens: int = 10,
        completion_tokens: int = 20,
        total_tokens: int = 30,
    ) -> mock.MagicMock:
        """Build a complete mock LiteLLM completion response."""
        response = mock.MagicMock()
        response.choices = [_make_mock_choice(content, finish_reason)]
        response.usage = _make_mock_usage(prompt_tokens, completion_tokens, total_tokens)
        response._hidden_params = {"response_cost": 0.0015}
        return response


    # ── Shared Adapter Instances ───────────────────────────────────────────


    @pytest.fixture
    def openai_config() -> ProviderConfig:
        return ProviderConfig(model="gpt-4o")


    @pytest.fixture
    def anthropic_config() -> ProviderConfig:
        return ProviderConfig(model="claude-3-5-sonnet-20241022")


    @pytest.fixture
    def ollama_config() -> ProviderConfig:
        return ProviderConfig(model="llama3", api_base="http://localhost:11434")


    @pytest.fixture
    def custom_config() -> ProviderConfig:
        return ProviderConfig(
            model="mistral",
            api_base="http://0.0.0.0:4000",
            api_key=memoryview(b"sk-custom-key"),
        )


    # ── Property Tests ────────────────────────────────────────────────────


    class TestOpenAIAdapterProperties:
        def test_model(self, openai_config: ProviderConfig) -> None:
            adapter = OpenAIAdapter(openai_config)
            assert adapter.model == "gpt-4o"

        def test_provider(self, openai_config: ProviderConfig) -> None:
            adapter = OpenAIAdapter(openai_config)
            assert adapter.provider == "openai"


    class TestAnthropicAdapterProperties:
        def test_model(self, anthropic_config: ProviderConfig) -> None:
            adapter = AnthropicAdapter(anthropic_config)
            assert adapter.model == "claude-3-5-sonnet-20241022"

        def test_provider(self, anthropic_config: ProviderConfig) -> None:
            adapter = AnthropicAdapter(anthropic_config)
            assert adapter.provider == "anthropic"


    class TestOllamaAdapterProperties:
        def test_model(self, ollama_config: ProviderConfig) -> None:
            adapter = OllamaAdapter(ollama_config)
            assert adapter.model == "llama3"

        def test_provider(self, ollama_config: ProviderConfig) -> None:
            adapter = OllamaAdapter(ollama_config)
            assert adapter.provider == "ollama"

        def test_requires_api_base(self, ollama_config: ProviderConfig) -> None:
            """OllamaAdapter must have api_base set (local URL)."""
            assert ollama_config.api_base == "http://localhost:11434"


    class TestCustomEndpointAdapterProperties:
        def test_model(self, custom_config: ProviderConfig) -> None:
            adapter = CustomEndpointAdapter(custom_config)
            assert adapter.model == "mistral"

        def test_provider(self, custom_config: ProviderConfig) -> None:
            adapter = CustomEndpointAdapter(custom_config)
            assert adapter.provider == "custom"

        def test_requires_api_base(self, custom_config: ProviderConfig) -> None:
            assert custom_config.api_base == "http://0.0.0.0:4000"


    # ── API Kwargs Construction Tests ─────────────────────────────────────


    class TestOpenAIAdapterKwargs:
        def test_without_key(self, openai_config: ProviderConfig) -> None:
            adapter = OpenAIAdapter(openai_config)
            kwargs = adapter._get_api_kwargs()
            assert "timeout" in kwargs
            assert kwargs["timeout"] == 60.0
            assert "api_key" not in kwargs

        def test_with_key(self) -> None:
            config = ProviderConfig(
                model="gpt-4o",
                api_key=memoryview(b"sk-openai-key"),
            )
            adapter = OpenAIAdapter(config)
            kwargs = adapter._get_api_kwargs()
            assert kwargs["api_key"] == "sk-openai-key"

        def test_with_api_base(self) -> None:
            config = ProviderConfig(
                model="gpt-4o",
                api_base="https://custom-openai.example.com",
            )
            adapter = OpenAIAdapter(config)
            kwargs = adapter._get_api_kwargs()
            assert kwargs["api_base"] == "https://custom-openai.example.com"

        def test_timeout_custom(self) -> None:
            config = ProviderConfig(model="gpt-4o", timeout=120.0)
            adapter = OpenAIAdapter(config)
            kwargs = adapter._get_api_kwargs()
            assert kwargs["timeout"] == 120.0


    class TestAnthropicAdapterKwargs:
        def test_with_key(self) -> None:
            config = ProviderConfig(
                model="claude-3-5-sonnet-20241022",
                api_key=memoryview(b"sk-ant-key"),
            )
            adapter = AnthropicAdapter(config)
            kwargs = adapter._get_api_kwargs()
            assert kwargs["api_key"] == "sk-ant-key"


    class TestOllamaAdapterKwargs:
        def test_no_api_key(self, ollama_config: ProviderConfig) -> None:
            """Ollama runs locally — no API key needed."""
            adapter = OllamaAdapter(ollama_config)
            kwargs = adapter._get_api_kwargs()
            assert "api_key" not in kwargs
            assert kwargs["api_base"] == "http://localhost:11434"

        def test_without_api_base(self) -> None:
            config = ProviderConfig(model="llama3")
            adapter = OllamaAdapter(config)
            kwargs = adapter._get_api_kwargs()
            assert "api_base" not in kwargs


    class TestCustomEndpointAdapterKwargs:
        def test_full_config(self, custom_config: ProviderConfig) -> None:
            adapter = CustomEndpointAdapter(custom_config)
            kwargs = adapter._get_api_kwargs()
            assert kwargs["api_key"] == "sk-custom-key"
            assert kwargs["api_base"] == "http://0.0.0.0:4000"
            assert kwargs["timeout"] == 60.0

        def test_without_key(self) -> None:
            config = ProviderConfig(
                model="mistral",
                api_base="http://0.0.0.0:4000",
            )
            adapter = CustomEndpointAdapter(config)
            kwargs = adapter._get_api_kwargs()
            assert "api_key" not in kwargs
            assert kwargs["api_base"] == "http://0.0.0.0:4000"


    # ── Generate() Tests (mocked LiteLLM) ─────────────────────────────────


    class MockAdapterMixin:
        """Provides a patched litellm.completion for generate() tests."""

        PATCH_PATH = "litellm.completion"

        @pytest.fixture
        def mock_completion(self) -> mock.MagicMock:
            with mock.patch(self.PATCH_PATH) as mocked:
                mocked.return_value = _make_mock_completion_response(
                    content="Hello from mock",
                    model="openai/gpt-4o",
                )
                yield mocked


    class TestOpenAIAdapterGenerate(MockAdapterMixin):
        PATCH_PATH = "litellm.completion"

        def test_generate_returns_normalized_response(
            self, openai_config: ProviderConfig, mock_completion: mock.MagicMock
        ) -> None:
            adapter = OpenAIAdapter(openai_config)
            result = adapter.generate([{"role": "user", "content": "Hi"}])
            assert isinstance(result, NormalizedResponse)
            assert result.content == "Hello from mock"
            assert result.provider == "openai"
            # Verify LiteLLM was called correctly
            mock_completion.assert_called_once()
            call_kwargs = mock_completion.call_args[1]
            assert call_kwargs["model"] == "openai/gpt-4o"
            assert call_kwargs["messages"] == [{"role": "user", "content": "Hi"}]

        def test_generate_with_cost(
            self, openai_config: ProviderConfig, mock_completion: mock.MagicMock
        ) -> None:
            adapter = OpenAIAdapter(openai_config)
            result = adapter.generate([{"role": "user", "content": "Hi"}])
            assert result.cost == 0.0015


    class TestAnthropicAdapterGenerate(MockAdapterMixin):
        PATCH_PATH = "litellm.completion"

        def test_generate_returns_normalized_response(
            self, anthropic_config: ProviderConfig, mock_completion: mock.MagicMock
        ) -> None:
            adapter = AnthropicAdapter(anthropic_config)
            result = adapter.generate([{"role": "user", "content": "Hello"}])
            assert isinstance(result, NormalizedResponse)
            assert result.provider == "anthropic"
            mock_completion.assert_called_once()
            call_kwargs = mock_completion.call_args[1]
            assert "anthropic/" in call_kwargs["model"]


    class TestOllamaAdapterGenerate(MockAdapterMixin):
        PATCH_PATH = "litellm.completion"

        def test_generate_returns_normalized_response(
            self, ollama_config: ProviderConfig, mock_completion: mock.MagicMock
        ) -> None:
            adapter = OllamaAdapter(ollama_config)
            result = adapter.generate([{"role": "user", "content": "Hello"}])
            assert isinstance(result, NormalizedResponse)
            assert result.provider == "ollama"
            mock_completion.assert_called_once()
            call_kwargs = mock_completion.call_args[1]
            assert call_kwargs["model"] == "ollama/llama3"

        def test_generate_without_api_base(self, mock_completion: mock.MagicMock) -> None:
            """Ollama without api_base should call LiteLLM without it."""
            config = ProviderConfig(model="phi3")
            adapter = OllamaAdapter(config)
            adapter.generate([{"role": "user", "content": "Hi"}])
            call_kwargs = mock_completion.call_args[1]
            assert "api_base" not in call_kwargs


    class TestCustomEndpointAdapterGenerate(MockAdapterMixin):
        PATCH_PATH = "litellm.completion"

        def test_generate_returns_normalized_response(
            self, custom_config: ProviderConfig, mock_completion: mock.MagicMock
        ) -> None:
            adapter = CustomEndpointAdapter(custom_config)
            result = adapter.generate([{"role": "user", "content": "Hello"}])
            assert isinstance(result, NormalizedResponse)
            assert result.provider == "custom"
            mock_completion.assert_called_once()
            call_kwargs = mock_completion.call_args[1]
            assert call_kwargs["model"] == "openai/mistral"
            assert call_kwargs["api_base"] == "http://0.0.0.0:4000"
            assert call_kwargs["api_key"] == "sk-custom-key"


    # ── Schema Consistency Tests (Acceptance Criterion 1) ──────────────────


    class TestSchemaConsistency:
        """ALL 4 adapters must return identical NormalizedResponse schema.

        This is a LOCKED user decision: "Normalized response schema must be
        identical across all 4 adapters."
        """

        @pytest.fixture(autouse=True)
        def _mock_litellm(self) -> mock.MagicMock:
            with mock.patch("litellm.completion") as mocked:
                mocked.return_value = _make_mock_completion_response(
                    content="Consistent schema test",
                    model="test/model",
                    prompt_tokens=5,
                    completion_tokens=10,
                    total_tokens=15,
                )
                yield mocked

        def _get_response_fields(self, response: NormalizedResponse) -> set[str]:
            """Return the set of field names in a NormalizedResponse."""
            return set(response.model_dump().keys())

        def test_all_responses_have_same_fields(self) -> None:
            """The set of field names must be identical across all adapters."""
            configs = [
                ("openai", ProviderConfig(model="gpt-4o")),
                ("anthropic", ProviderConfig(model="claude-3-5-sonnet-20241022")),
                ("ollama", ProviderConfig(model="llama3", api_base="http://localhost:11434")),
                ("custom", ProviderConfig(model="mistral", api_base="http://0.0.0.0:4000")),
            ]
            responses: list[NormalizedResponse] = []
            for provider, config in configs:
                adapter = ProviderFactory.create(provider, config)
                resp = adapter.generate([{"role": "user", "content": "test"}])
                responses.append(resp)

            # All field sets must be identical
            field_sets = [self._get_response_fields(r) for r in responses]
            for i in range(1, len(field_sets)):
                assert field_sets[i] == field_sets[0], (
                    f"Provider {configs[i][0]} returns different fields than {configs[0][0]}: "
                    f"{field_sets[i]} vs {field_sets[0]}"
                )

        def test_all_responses_have_same_types(self) -> None:
            """Field types must be consistent — content is str, usage is TokenUsage, etc."""
            adapter = OpenAIAdapter(ProviderConfig(model="gpt-4o"))
            resp = adapter.generate([{"role": "user", "content": "test"}])
            assert isinstance(resp.content, str)
            assert isinstance(resp.model, str)
            assert isinstance(resp.provider, str)
            assert isinstance(resp.usage.prompt_tokens, int)
            assert resp.cost is None or isinstance(resp.cost, float)


    # ── Count Tokens Tests (Acceptance Criterion 4) ───────────────────────


    class TestTokenCounting:
        """Token counting delegates to litellm.token_counter()."""

        @pytest.fixture(autouse=True)
        def _mock_token_counter(self) -> mock.MagicMock:
            with mock.patch("litellm.token_counter") as mocked:
                mocked.return_value = 42
                yield mocked

        def test_openai_count_tokens(
            self, openai_config: ProviderConfig, _mock_token_counter: mock.MagicMock
        ) -> None:
            adapter = OpenAIAdapter(openai_config)
            count = adapter.count_tokens([{"role": "user", "content": "Hello"}])
            assert count == 42
            _mock_token_counter.assert_called_once_with(
                model="openai/gpt-4o",
                messages=[{"role": "user", "content": "Hello"}],
            )

        def test_anthropic_count_tokens(
            self, anthropic_config: ProviderConfig, _mock_token_counter: mock.MagicMock
        ) -> None:
            adapter = AnthropicAdapter(anthropic_config)
            count = adapter.count_tokens([{"role": "user", "content": "Hello"}])
            assert count == 42
            _mock_token_counter.assert_called_once_with(
                model="anthropic/claude-3-5-sonnet-20241022",
                messages=[{"role": "user", "content": "Hello"}],
            )

        def test_ollama_count_tokens(
            self, ollama_config: ProviderConfig, _mock_token_counter: mock.MagicMock
        ) -> None:
            adapter = OllamaAdapter(ollama_config)
            count = adapter.count_tokens([{"role": "user", "content": "Hello"}])
            assert count == 42
            _mock_token_counter.assert_called_once_with(
                model="ollama/llama3",
                messages=[{"role": "user", "content": "Hello"}],
            )

        def test_custom_count_tokens(
            self, custom_config: ProviderConfig, _mock_token_counter: mock.MagicMock
        ) -> None:
            adapter = CustomEndpointAdapter(custom_config)
            count = adapter.count_tokens([{"role": "user", "content": "Hello"}])
            assert count == 42
            _mock_token_counter.assert_called_once_with(
                model="openai/mistral",
                messages=[{"role": "user", "content": "Hello"}],
            )


    # ── Provider Instantiation Benchmark (Acceptance Criterion 6) ─────────


    class TestProviderInstantiationBenchmark:
        """Provider instantiation must complete within 500ms.

        This test creates all 4 adapter types multiple times to verify
        that construction + registration lookup is fast.
        """

        INSTANTIATION_COUNT = 10
        MAX_MS = 500

        def test_openai_instantiation_time(self) -> None:
            import time
            config = ProviderConfig(model="gpt-4o")
            start = time.perf_counter()
            for _ in range(self.INSTANTIATION_COUNT):
                ProviderFactory.create("openai", config)
            elapsed_ms = (time.perf_counter() - start) / self.INSTANTIATION_COUNT * 1000
            assert elapsed_ms < self.MAX_MS, (
                f"OpenAIAdapter instantiation took {elapsed_ms:.1f}ms "
                f"(max: {self.MAX_MS}ms)"
            )

        def test_anthropic_instantiation_time(self) -> None:
            import time
            config = ProviderConfig(model="claude-3-5-sonnet-20241022")
            start = time.perf_counter()
            for _ in range(self.INSTANTIATION_COUNT):
                ProviderFactory.create("anthropic", config)
            elapsed_ms = (time.perf_counter() - start) / self.INSTANTIATION_COUNT * 1000
            assert elapsed_ms < self.MAX_MS

        def test_ollama_instantiation_time(self) -> None:
            import time
            config = ProviderConfig(model="llama3", api_base="http://localhost:11434")
            start = time.perf_counter()
            for _ in range(self.INSTANTIATION_COUNT):
                ProviderFactory.create("ollama", config)
            elapsed_ms = (time.perf_counter() - start) / self.INSTANTIATION_COUNT * 1000
            assert elapsed_ms < self.MAX_MS

        def test_custom_instantiation_time(self) -> None:
            import time
            config = ProviderConfig(model="mistral", api_base="http://0.0.0.0:4000")
            start = time.perf_counter()
            for _ in range(self.INSTANTIATION_COUNT):
                ProviderFactory.create("custom", config)
            elapsed_ms = (time.perf_counter() - start) / self.INSTANTIATION_COUNT * 1000
            assert elapsed_ms < self.MAX_MS

        def test_all_providers_bulk_instantiation(self) -> None:
            """Instantiate all 4 adapters 100 times total — must stay under 500ms avg."""
            import time
            configs = [
                ("openai", ProviderConfig(model="gpt-4o")),
                ("anthropic", ProviderConfig(model="claude-3-5-sonnet-20241022")),
                ("ollama", ProviderConfig(model="llama3", api_base="http://localhost:11434")),
                ("custom", ProviderConfig(model="mistral", api_base="http://0.0.0.0:4000")),
            ]
            total = 0
            n = 0
            start = time.perf_counter()
            for provider, config in configs:
                for _ in range(self.INSTANTIATION_COUNT):
                    ProviderFactory.create(provider, config)
                    n += 1
            elapsed_ms = (time.perf_counter() - start) / n * 1000
            assert elapsed_ms < self.MAX_MS, (
                f"Average instantiation across {n} creates: {elapsed_ms:.1f}ms "
                f"(max: {self.MAX_MS}ms)"
            )


    # ── Edge Case Tests ────────────────────────────────────────────────────


    class TestEdgeCases:
        """Edge cases and error handling."""

        def test_openai_with_empty_messages(self) -> None:
            """Empty messages list should not crash (LiteLLM handles validation)."""
            with mock.patch("litellm.completion") as mocked:
                mocked.return_value = _make_mock_completion_response(content="")
                adapter = OpenAIAdapter(ProviderConfig(model="gpt-4o"))
                result = adapter.generate([])
                assert isinstance(result, NormalizedResponse)
                assert result.content == ""

        def test_anthropic_with_none_content(self) -> None:
            """Handle when LiteLLM returns None for content."""
            with mock.patch("litellm.completion") as mocked:
                response = mock.MagicMock()
                response.choices = [_make_mock_choice(None, "stop")]
                response.usage = _make_mock_usage()
                response._hidden_params = {}
                mocked.return_value = response
                adapter = AnthropicAdapter(ProviderConfig(model="claude-3-5-sonnet-20241022"))
                result = adapter.generate([{"role": "user", "content": "test"}])
                assert result.content == ""  # Should coerce None to ""

        def test_custom_endpoint_without_api_base(self) -> None:
            """Custom endpoint WITHOUT api_base — uses LiteLLM's default OpenAI endpoint."""
            config = ProviderConfig(model="mistral")
            adapter = CustomEndpointAdapter(config)
            kwargs = adapter._get_api_kwargs()
            assert "api_base" not in kwargs  # Should not be set
    ```

    IMPORTANT GUIDELINES:
    - ALL tests mock `litellm.completion`, `litellm.acompletion`, or `litellm.token_counter` — no real API calls
    - The `_make_mock_*` helper functions build LiteLLM-like mock objects from scratch
    - Schema consistency tests (`TestSchemaConsistency`) verify that ALL 4 adapters produce the SAME field names and types — this directly tests the locked user decision
    - Benchmark tests measure average instantiation time across multiple iterations, not a single call (avoids noise from CPU scheduler)
    - The `MockAdapterMixin` class provides shared `mock_completion` fixture — `PATCH_PATH` is set per subclass to target the correct module
    - Each test function tests ONE behavior — descriptive names tell you exactly what's being tested
    - Edge case tests handle: empty messages, None content, missing optional config fields
    - Do NOT test `generate_stream()` with mocks in this task — streaming requires async testing infrastructure that's added in later phases. The sync generate() tests + property tests are sufficient for now.
    - ProviderFactory tests from Task 1 registered temporary adapters — those are cleaned up. The actual adapters (openai, anthropic, ollama, custom) are registered by importing their modules (which happens when the import statements at the top of this file execute).
  </action>
  <verify>
    # Run ALL adapter tests
    uv run pytest packages/centinela-core/tests/llm/test_adapters.py -v --tb=short

    # Run the full LLM test suite
    uv run pytest packages/centinela-core/tests/llm/ -v --tb=short

    # Run with coverage
    uv run pytest packages/centinela-core/tests/llm/ --cov=packages/centinela-core --cov-report=term-missing

    # Verify mypy passes on tests
    uv run mypy packages/centinela-core/tests/
  </verify>
  <done>
    All 4 adapter unit tests pass with mocked LiteLLM. Schema consistency verified across all adapters. Benchmark confirms instantiation <500ms. Edge cases handled (empty messages, None content, missing config). Full test suite for the llm module is operational.
  </done>
</task>

</tasks>

<verification>
Run the complete LLM test suite. ALL tests must pass:

```bash
# 1. Run the full test suite with verbose output
uv run pytest packages/centinela-core/tests/llm/ -v --tb=short

# 2. Run with coverage
uv run pytest packages/centinela-core/tests/llm/ --cov=packages/centinela-core --cov-report=term-missing

# 3. Mypy on test files
uv run mypy packages/centinela-core/tests/

# 4. Verify all acceptance criteria are test-covered:
#    AC-1: test_schema_consistency (identical response schema)
#    AC-2: test_factory.py (rate limit retry config: num_retries=3, exponential_backoff)
#    AC-3: test_secure_key.py (memory zeroing verified)
#    AC-4: test_adapters token counting tests
#    AC-5: CustomEndpointAdapter generate + kwargs tests
#    AC-6: Benchmark tests (<500ms instantiation)
echo "---"
echo "Acceptance criteria coverage:"
echo "  AC-1 (identical schema): test_schema_consistency"
echo "  AC-2 (rate limit retry): test_litellm_global_config"
echo "  AC-3 (memory zeroing):   test_secure_key.py (all tests)"
echo "  AC-4 (token counting):   test_token_counting"
echo "  AC-5 (custom endpoint):  test_custom_endpoint_adapter_*"
echo "  AC-6 (<500ms):           test_provider_instantiation_benchmark"
```
</verification>

<success_criteria>
- ALL 7 test files exist in packages/centinela-core/tests/llm/
- `uv run pytest packages/centinela-core/tests/llm/ -v` returns exit code 0 with all tests passing
- Coverage report shows >80% coverage for centinela.core.llm module
- `uv run mypy packages/centinela-core/tests/` returns zero type errors
- SecureKeyStore zeroing is proven: `test_all_bytes_zeroed_after_clear` and `test_memoryview_released_after_clear` pass
- Schema consistency test proves all 4 adapters return identical NormalizedResponse field sets
- Provider instantiation benchmark confirms <500ms average for all 4 adapter types
- Every acceptance criterion (AC-1 through AC-6) has at least one automated test covering it
- All tests run without real API keys (LiteLLM is mocked)
</success_criteria>

<output>
After completion, create `.planning/phases/02-red-teaming-engine/02-red-teaming-engine-03-SUMMARY.md`
</output>
