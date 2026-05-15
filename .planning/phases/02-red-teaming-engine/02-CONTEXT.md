# Phase 2: Universal Provider Adapter

**Labels:** core, llm-integration, api
**Created:** 2026-05-15

## Objective

Build a universal provider adapter that normalizes API calls across different LLM providers into a unified interface.

## Requirements

### Provider Adapter Architecture

- Implement `UniversalProviderAdapter` abstract base class with:
  - `generate()` — synchronous text generation
  - `generate_stream()` — streaming text generation
  - `count_tokens()` — token counting for input/output
- Create OpenAI adapter (GPT-4o, GPT-4-turbo, GPT-3.5-turbo)
- Create Anthropic adapter (Claude 3.5 Sonnet, Claude 3 Opus, Claude Haiku)
- Create Ollama adapter (Mistral 7B, LLaMA 3, Phi-3)
- Create custom OpenAI-compatible endpoint adapter
- Use LiteLLM as underlying gateway for unified API
- Implement normalized response format across all providers
- Add rate limit handling with exponential backoff and retry logic

### Security Requirements

- API key held in RAM only using `memoryview` — zeroed on session end
- API key never forwarded to red or blue agents
- API key never logged in audit trail

## Acceptance Criteria

1. All 4 adapters return identical response schema
2. Rate limit retry succeeds up to 3 attempts with backoff
3. API key memory is zeroed after session end (verified with memory inspection test)
4. Token counting works for all providers
5. Custom endpoint adapter works with any OpenAI-compatible API
6. Provider instantiation takes <500ms including credential validation

## Decisions

- **Locked:** Use LiteLLM as underlying gateway library
- **Locked:** API key must use `memoryview` for RAM-only storage with zeroing
- **Locked:** Exponential backoff with up to 3 retries for rate limits
- **Locked:** Normalized response schema must be identical across all 4 adapters
- **Deferred:** Multi-modal support (image/audio inputs) — not in scope
- **Claude's Discretion:** Exact normalized response schema structure
- **Claude's Discretion:** Token counting implementation strategy
- **Claude's Discretion:** Error handling patterns beyond rate limits
