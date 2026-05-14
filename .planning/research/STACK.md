# Stack Research

**Domain:** AI Safety Testing Platforms (Containerized Adversarial Testing)
**Researched:** 2026-05-14
**Confidence:** MEDIUM-HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Python** | 3.12+ | Primary language | Ecosystem maturity for AI/ML testing, async-first libraries, LLM integration |
| **FastAPI** | 0.115+ | Web framework | Native async, Pydantic validation, auto OpenAPI docs — outperforms Flask 2-5x for concurrent AI workloads (WebSearch, 2025) |
| **LiteLLM** | 1.84+ | Multi-provider LLM gateway | Unified API across 100+ providers (OpenAI, Anthropic, Ollama, custom), 8ms P95 latency, built-in cost tracking, virtual keys (WebSearch, 2026) |
| **Docker Compose** | 2.38+ | Container orchestration | Service isolation per container, network segmentation, multi-container health checks — standard for 5-container AI stacks (WebSearch, 2025-2026) |
| **PostgreSQL** | 16+ | Primary database | AsyncSQLAlchemy support, JSONB for audit payloads, robust for multi-tenant workloads |
| **Redis** | 7.4+ | Task queue broker + cache | Celery broker, session cache, rate limiting — production-standard for async Python (WebSearch, 2025) |
| **Pydantic** | 2.10+ | Data validation | Built into FastAPI, type-safe models, reduces runtime bugs in AI pipelines |

### Agent/Orchestration Layer

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Celery** | 5.4+ | Async task queue | De facto standard for Python distributed tasks, RabbitMQ/Redis/SQS support, retry/DLQ patterns (WebSearch, 2025) |
| **pytest** | 8.3+ | Testing framework | AI red-teaming test orchestration, pytest-docker fixtures, plugin ecosystem (Garak, Promptfoo) |
| **SignLedger / ads-foundation** | latest | Tamper-proof audit logging | Merkle-chained entries, SHA-256 hash chains, cryptographic verification — aligns with audit container requirements (WebSearch, 2025) |

### Red-Teaming/Adversarial Testing Libraries

| Library | Purpose | When to Use |
|---------|---------|-------------|
| **Garak** (NVIDIA) | LLM vulnerability scanner | Prompt injection probes, safety filter assessment |
| **Promptfoo** | LLM evaluation + red team | Red team generation, OWASP LLM Top 10 coverage |
| **llm-audit** | OWASP LLM Top 10 scanner | Endpoint-based testing, CI/CD integration |
| **LANCE / Prompt Siege** | Automated red team | 195+ adversarial probes, LLM-as-judge evaluation |
| **Custom attack profiles** | Domain-specific mutation engine | Adaptive red-teaming with prompt mutation |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **SQLAlchemy** | 2.0+ | ORM + async support | `asyncpg` driver, `AsyncSession`, `selectinload` for relationships |
| **Alembic** | 1.14+ | Database migrations | Schema versioning for PostgreSQL |
| **httpx** | 0.28+ | Async HTTP client | Multi-provider LLM calls, streaming responses |
| **structlog** | 24.4+ | Structured logging | JSON audit logs, context propagation |
| **python-dotenv** | 1.0+ | Environment management | Local/dev secret handling |
| **uv** | 0.5+ | Package manager | Fast Python installs, dependency resolution |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| **uvicorn** | ASGI server (dev) | `uvicorn --reload` for local dev |
| **gunicorn + uvicorn-worker** | ASGI server (prod) | Multi-worker process management, graceful restart |
| **ruff** | Linting/formatting | Fast Python linting, replaces flake8/isort |
| **mypy** | Type checking | Catches async ORM issues (MissingGreenlet errors) |

## Installation

```bash
# Core AI/ML + HTTP
uv add fastapi uvicorn[standard] pydantic httpx structlog python-dotenv

# LLM multi-provider gateway
uv add litellm

# Database
uv add sqlalchemy[asyncio] asyncpg alembic psycopg

# Task queue
uv add celery[redis] redis

# Red-teaming / testing
uv add pytest pytest-docker pytest-asyncio
uv add garak promptfoo

# Audit / tamper-proof logging
uv add signledger ads-foundation

# Development tools
uv add --dev ruff mypy

# For local LLM (optional)
uv add ollama  # or run via Docker
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| FastAPI | Flask | Existing Flask codebase, simple sync-only workflows |
| LiteLLM | Direct provider SDKs | Single provider, no multi-model fallback needed |
| Docker Compose | Kubernetes (k3s) | Multi-host production, enterprise scaling |
| Celery + Redis | RabbitMQ | Higher delivery guarantees, transactional patterns |
| PostgreSQL | SQLite | Single-container dev, no concurrency requirements |
| SignLedger | Custom hash chain | Need zero-dependency, specific cryptographic primitives |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **Flask (for new AI projects)** | WSGI sync-only, no native async, 2-5x lower throughput for concurrent LLM calls (WebSearch, 2025) | FastAPI |
| **Django** | Over-engineered for isolated container services, slower startup, ORM overhead | FastAPI + SQLAlchemy |
| **SQLAlchemy sync with async engine** | MissingGreenlet runtime errors when lazy loading in async context | `selectinload()` eager loading or write-only relationships |
| **Pickle serialization (Celery)** | Code injection vulnerability | JSON serialization |
| **docker-compose V1** | Deprecated July 2023, no updates | Docker Compose V2 (`docker compose`) |
| **gunicorn with uvicorn.workers module** | Deprecated, removed in future release | `uvicorn-worker` package or Gunicorn ASGI worker |
| **Global Celery visibility timeout < ETA** | Task redelivery loop for long-running AI tasks | Set to match longest ETA (43200s max) |

## Stack Patterns by Variant

**If single-container prototype:**
- FastAPI + SQLite + in-memory audit
- `uvicorn.run()` for dev
- Skip LiteLLM, use direct provider SDKs

**If five-container production (CENTINELA architecture):**
- Orchestrator: FastAPI + Celery (Redis broker) + PostgreSQL
- Red-agent: Python + LiteLLM + Garak/Promptfoo
- Blue-agent: Python + LiteLLM + evaluation logic
- LLM-sandbox: Isolated container with network restriction
- Audit: SignLedger + PostgreSQL (Merkle chain)
- Use Docker Compose with `depends_on`, `healthcheck`, `internal` networks

**If high-scale multi-tenant:**
- Add PgBouncer for connection pooling
- Replace Celery Redis broker with RabbitMQ
- LiteLLM proxy server mode for centralized auth/keys
- Redis Cluster for queue/cache

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| FastAPI 0.115+ | Python 3.9+ | Full async support |
| SQLAlchemy 2.0+ | asyncpg 0.30+, Python 3.9+ | Use `postgresql+asyncpg://` URL scheme |
| LiteLLM 1.84+ | Python 3.9+ | 100+ provider support, OpenAI-compatible |
| Celery 5.4+ | Redis 6.2+, Python 3.9+ | JSON serializer for security |
| pytest 8.3+ | Python 3.9+ | Async fixtures via pytest-asyncio |
| SignLedger 1.0+ | Python 3.10+ | SHA-256/Ed25519, multiple backends |

**Critical compatibility warnings:**
- Never use `psycopg` (sync) with `create_async_engine` — use `asyncpg`
- Never use `postgresql://` (sync) with async session — must be `postgresql+asyncpg://`
- Gunicorn ASGI worker: `--worker-class asgi` not `uvicorn.workers.*`

## Architecture Alignment

The five-container CENTINELA architecture maps to this stack:

```
┌─────────────────────────────────────────────────────────────────┐
│  Docker Compose Network (internal, isolated)                    │
│                                                                  │
│  ┌──────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │  red-agent   │  │   orchestrator   │  │   blue-agent     │  │
│  │  Python      │  │  FastAPI + Celery│  │  Python + LiteLLM│  │
│  │  Garak       │  │  PostgreSQL      │  │  Evaluation      │  │
│  │  LiteLLM     │  │  Redis          │  │  LiteLLM         │  │
│  └──────────────┘  └─────────────────┘  └──────────────────┘  │
│                          │                                       │
│  ┌──────────────┐       │         ┌────────────────────────┐   │
│  │ llm-sandbox  │       │         │       audit           │   │
│  │ Isolated     │◄──────┼────────►│  SignLedger           │   │
│  │ Container    │       │         │  PostgreSQL           │   │
│  │ (no network) │       │         │  (Merkle chain)       │   │
│  └──────────────┘       └─────────┴────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Network isolation:**
- `internal: true` on compose network — containers cannot reach internet
- LLM-sandbox: restricted outbound, only provider API calls allowed via credential proxy
- Each container has unique credentials via environment variables
- Health checks + auto-restart on failure

## Sources

- **FastAPI vs Flask for AI**: WebSearch (multiple 2025) — FastAPI 2-5x throughput advantage, native async
- **LiteLLM v1.84**: Official docs, GitHub (25k+ stars) — 100+ providers, 8ms P95 latency
- **Docker Compose AI patterns**: WebSearch (Docker official, 2025-2026) — multi-container orchestration best practices
- **Merkle audit logging**: SignLedger, ads-foundation, viraxlog — WebSearch (2025-2026) — cryptographic tamper-proof logs
- **Celery + Redis**: Official docs, WebSearch (2025) — distributed task queue patterns
- **AI red-teaming**: Garak (NVIDIA), Promptfoo, LANCE, llm-audit — GitHub/WebSearch (2025-2026)
- **SQLAlchemy async**: Official docs, WebSearch (2025-2026) — greenlet errors, eager loading patterns
- **Uvicorn/Gunicorn**: Official deployment docs (2025) — production ASGI patterns

---
*Stack research for: AI Safety Testing Platforms*
*Researched: 2026-05-14*