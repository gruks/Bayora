# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-15)

**Core value:** Enable regulated companies to obtain independent, forensically defensible AI safety audits with signed certificates that satisfy compliance frameworks (HIPAA, SOX, GDPR, EU AI Act).
**Current focus:** Phase 3 — Evaluation Engine

## Current Position

Phase: 3 of 25 — evaluation-engine
Plan: 1/4 complete
Status: Plan 01 executed — classifier foundation (types, interface, isolation, HH-RLHF classifier)
Last activity: 2026-05-16 — Phase 3 Plan 01 complete (2 tasks, 15 tests)

Progress: [████░░░░░░] 4% (Phase 1 complete, Phase 2 complete, Phase 3 in progress)

## Performance Metrics

**Velocity:**
- Total plans completed: 3
- Average duration: ~28 min/plan
- Total execution time: ~1.5 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1     | 2/2   | 2     | ~37 min   |
| 2     | 3/3   | 3     | ~23 min   |
| 3     | 1/4   | 1     | ~25 min   |

**Recent Trend:**
- Last 3 plans: Phase 2 Plan 02, Phase 3 Plan 01
- Trend: Phase 3 evaluation engine execution underway

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- **Phase 1 (unittest -> pytest)**: Test discovery works best without `__init__.py` in test directories. Named test files per service (`test_audit.py`, `test_red_agent.py`) to avoid import conflicts.
- **Phase 1 (mypy)**: Added `exclude = "tests/"` in mypy config to prevent duplicate module errors across service test directories.
- **Phase 1 (uv sync)**: Use `uv sync --all-packages --all-extras` to install workspace members and dev dependencies together.
- **Phase 2 (LLM types)**: Used pydantic BaseModel for response types with frozen=True for security-sensitive immutability.
- **Phase 2 (SecureKeyStore)**: Used memoryview + bytearray for RAM-only key storage with deterministic zeroing.
- **Phase 2 (LiteLLM config)**: Configured exponential_backoff_retry with 3 retries globally at module import.
- Phase 4: Five-container model with gVisor runtime, Merkle-chained audit, Ed25519 signing — research validated these as key differentiators
- Phase 1: Budget guard and side-channel mitigations in foundation (needed by orchestrator core)
- Phase 3: Blue-agent isolation from red-agent enforced — orchestrator strips prompts before forwarding
- **Phase 3 (models package)**: Converted models.py to models/ package directory for better organization; existing types moved to base.py
- **Phase 3 (py.typed)**: Added py.typed marker to centinela-core for mypy workspace type checking support
- **Phase 3 (BLUE-04)**: Safety classifier interface enforces prompt isolation at type level — no method accepts prompt parameter

### Roadmap Evolution

- Phase 1 complete: Python monorepo with root pyproject.toml, centinela-core shared package, 5 service stubs, ruff/mypy/pytest tooling, pre-commit, Dockerfiles, CI pipeline, docs
- Phase 2 complete: Red-teaming engine with 4 provider adapters (OpenAI, Anthropic, Ollama, CustomEndpoint)
- Phase 3 Plan 01 complete: Classifier foundation — frozen pydantic types, SafetyClassifier interface, HH-RLHF classifier, isolation layer
- Phase 5 added: Project Setup and Core Infrastructure (from Bayora)
- Phase 6 added: Dataset Management (from Bayora)
- Phase 7 added: Configuration Parser and Validator (from Bayora)
- Phase 8 added: Secrets Manager (from Bayora)
- Phase 9 added: Audit Log Service (from Bayora)
- Phase 10 added: Provenance Tracker (from Bayora)
- Phase 11 added: Checkpoint - Core Services (from Bayora)
- Phase 12 added: Anomaly Detector (from Bayora)
- Phase 13 added: Network Segmentation (from Bayora)
- Phase 13.1 added: Resource Governor (from Bayora Phase 9b)
- Phase 14 added: Container Image Security (from Bayora)
- Phase 15 added: Checkpoint - Security Services (from Bayora)
- Phase 16 added: Orchestrator - Session Management (from Bayora)
- Phase 17 added: Orchestrator - Container Orchestration (from Bayora)
- Phase 18 added: Orchestrator - LLM-Specific Isolation (from Bayora)
- Phase 19 added: Orchestrator API (from Bayora)
- Phase 20 added: Checkpoint - Orchestrator (from Bayora)
- Phase 21 added: Red Team and Blue Team Integration (from Bayora)
- Phase 22 added: Kubernetes Deployment (from Bayora)
- Phase 23 added: Threat Modeling and Security Documentation (from Bayora)
- Phase 24 added: Final Integration and Testing (from Bayora)
- Phase 25 added: Production Readiness Checkpoint (from Bayora)

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 4: gVisor (ARCH-06) requires Linux kernel — may need alternative for Windows dev environments (Docker Desktop Linux containers works)

## Session Continuity

Last session: 2026-05-16
Stopped at: Phase 3 Plan 01 execution complete — classifier foundation (2 tasks, 15 tests)
Resume file: None
