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
