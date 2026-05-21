from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel

# ── Normalized Response Types ──────────────────────────────────────
# These are what every adapter returns, regardless of provider.
# Identical schema across all 4 adapters per user decision.


class TokenUsage(BaseModel):
    """Token usage statistics normalized across all providers."""

    model_config = {"frozen": True}
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class NormalizedResponse(BaseModel):
    """Unified response format for all LLM provider adapters."""

    model_config = {"frozen": True}
    content: str
    model: str
    provider: str
    usage: TokenUsage = TokenUsage()
    cost: float | None = None


class NormalizedChunk(BaseModel):
    """A single streaming chunk, normalized across providers."""

    model_config = {"frozen": True}
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
