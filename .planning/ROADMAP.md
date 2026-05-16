# Roadmap: CENTINELA

## Overview

CENTINELA is an AI safety validation platform that delivers independent adversarial testing across any AI provider and produces forensically auditable signed certificates. The roadmap builds foundation infrastructure (provider adapter, orchestrator, audit system), then attack and evaluation engines, and completes with full five-container deployment and certificate generation. Each phase is independently verifiable and unlocks the next capability.

## Phases

- [x] **Phase 1: Foundation** - Python monorepo skeleton, tooling, Docker, CI
- [ ] **Phase 2: Red-Teaming Engine** - Red-agent with adversarial attack datasets, adaptive mutation, domain-specific profiles
- [ ] **Phase 3: Evaluation Engine** - Blue-agent with safety classifiers, multi-seed evaluation, scoring metrics
- [ ] **Phase 4: Container Integration + Certificates** - Five-container deployment, Merkle audit chain, signed PDF certificates
- [ ] **Phase 5: Project Setup & Core Infrastructure** - Python package structure, core data models, testing framework
- [ ] **Phase 6: Dataset Management** - Adversarial testing datasets for red/blue team operations
- [ ] **Phase 7: Configuration Parser & Validator** - Declarative security policy management
- [ ] **Phase 8: Secrets Manager** - Cryptographic key and credential management
- [ ] **Phase 9: Audit Log Service** - Tamper-evident cryptographic logging
- [ ] **Phase 10: Provenance Tracker** - Forensic data lineage tracking
- [ ] **Phase 11: Checkpoint - Core Services** - Validation checkpoint
- [ ] **Phase 12: Anomaly Detector** - Real-time security monitoring
- [ ] **Phase 13: Network Segmentation** - WireGuard-based network isolation
- [ ] **Phase 13.1: Resource Governor** - cgroup v2 resource controls
- [ ] **Phase 14: Container Image Security** - Supply chain security
- [ ] **Phase 15: Checkpoint - Security Services** - Validation checkpoint
- [ ] **Phase 16: Orchestrator - Session Management** - Session lifecycle orchestration
- [ ] **Phase 17: Orchestrator - Container Orchestration** - Kubernetes pod management
- [ ] **Phase 18: Orchestrator - LLM-Specific Isolation** - AI-specific security controls
- [ ] **Phase 19: Orchestrator API** - REST API with FastAPI
- [ ] **Phase 20: Checkpoint - Orchestrator** - End-to-end orchestrator validation
- [ ] **Phase 21: Red Team & Blue Team Integration** - Attackers and defenders
- [ ] **Phase 22: Kubernetes Deployment** - Production-ready deployment artifacts
- [ ] **Phase 23: Threat Modeling & Security Documentation** - Risk transparency and compliance
- [ ] **Phase 24: Final Integration & Testing** - End-to-end validation
- [ ] **Phase 25: Production Readiness Checkpoint** - Final validation

## Phase Details

### Phase 1: Foundation
**Goal**: Project skeleton — root workspace, shared package, 5 service stubs, tool config, quality gates, containerization
**Depends on**: Nothing (first phase)
**Requirements**: PROV-01, PROV-02, PROV-03, PROV-04, PROV-05, PROV-06, PROV-07, PROV-08, PROV-09, ORCH-01, ORCH-02, ORCH-03, ORCH-04, ORCH-05, ORCH-06, AUDT-01, AUDT-02, AUDT-03, AUDT-04, AUDT-05, AUDT-06, AUDT-07, BUDG-01, BUDG-02, BUDG-03, BUDG-04, BUDG-05, SIDE-01, SIDE-02, SIDE-03
**Success Criteria** (what must be TRUE):
   1. Developer can install all dependencies with `uv sync` — no errors
   2. `ruff check .`, `ruff format --check .`, `mypy services/ packages/`, `pytest` all pass with zero errors
   3. 5 service stubs exist and are importable: red-agent, orchestrator, blue-agent, llm-sandbox, audit
   4. centinela-core shared package exists with pydantic BaseModel types
   5. Pre-commit hooks run on git commit with ruff and mypy
   6. GitHub Actions CI pipeline defines lint → type-check → test → build
**Plans**: 2 plans

Plans:
- [x] 01-foundation-01-PLAN.md — Project skeleton: root pyproject.toml, shared package, 5 service stubs, tool config (ruff, mypy, pytest)
- [x] 01-foundation-02-PLAN.md — Quality gates: pre-commit hooks, Dockerfiles, CI pipeline, env template, contributing guide

### Phase 2: Universal Provider Adapter
**Goal**: Developers can call any LLM provider (OpenAI, Anthropic, Ollama, custom) through a unified adapter interface with identical response schemas, RAM-only API key storage, and automatic rate-limit retry
**Depends on**: Phase 1
**Requirements**: PROV-01, PROV-02, PROV-03, PROV-04, PROV-05, PROV-06, PROV-07, PROV-08, PROV-09, RED-01 (lite), RED-02 (lite)
**Success Criteria** (what must be TRUE):
   1. All 4 adapters return identical NormalizedResponse schema (identical field names and types)
   2. Rate limit retry succeeds up to 3 attempts with exponential backoff
   3. API key memory is zeroed after session end (verified with byte-level memory inspection test)
   4. Token counting works for all providers via litellm.token_counter()
   5. Custom endpoint adapter works with any OpenAI-compatible API (configurable api_base)
   6. Provider instantiation completes in <500ms
   7. All tests pass without real API keys (LiteLLM is mocked)
**Plans**: 3 plans

Plans:
- [ ] 02-red-teaming-engine-01-PLAN.md — Core LLM infrastructure: types, ABC, SecureKeyStore, ProviderFactory
- [ ] 02-red-teaming-engine-02-PLAN.md — All 4 adapters: OpenAI, Anthropic, Ollama, CustomEndpoint
- [ ] 02-red-teaming-engine-03-PLAN.md — Comprehensive test suite: unit tests, schema verification, benchmark

### Phase 3: Evaluation Engine
**Goal**: Users can classify model outputs as safe or harmful with quantitative scoring across 50+ metrics
**Depends on**: Phase 1
**Requirements**: BLUE-01, BLUE-02, BLUE-03, BLUE-04, BLUE-05, BLUE-06
**Success Criteria** (what must be TRUE):
  1. User can classify model outputs as safe or harmful using HH-RLHF and ToxiGen trained classifiers
  2. Blue-agent receives only the model response — never the original adversarial prompt (enforced isolation)
  3. User can run evaluations across multiple seeds and receive confidence intervals
  4. User can obtain safety scores across 50+ core metrics with breakdown by category
**Plans**: TBD

### Phase 4: Container Integration + Certificates
**Goal**: Users can deploy the complete five-container architecture with forensically auditable signed certificates
**Depends on**: Phase 3
**Requirements**: ARCH-01, ARCH-02, ARCH-03, ARCH-04, ARCH-05, ARCH-06, ARCH-07, ARCH-08, CERT-01, CERT-02, CERT-03, CERT-04, CERT-05, CERT-06, CERT-07, CERT-08, CERT-09
**Success Criteria** (what must be TRUE):
  1. User can deploy entire system with single `docker compose up` command
  2. System runs as five isolated containers (red-agent, orchestrator, blue-agent, llm-sandbox, audit) each on separate Docker bridge networks
  3. LLM sandbox uses gVisor runtime with seccomp profiles and cgroup v2 hard limits
  4. Audit chain verification confirms cryptographic integrity across all logged events
  5. User receives signed PDF safety certificate including model info, test date, session ID, vulnerability counts, mutation rounds, Merkle root hash, and Ed25519 signature
  6. Recipient can verify certificate integrity using the included verification command
**Plans**: TBD

## Progress

| Phase | Requirements | Status | Completed |
|-------|--------------|--------|-----------|
| 1. Foundation | 30 | ✓ Executed | 2026-05-15 |
| 2. Universal Provider Adapter | 9 | Planned (3 plans) | - |
| 3. Evaluation Engine | 6 | Not started | - |
| 4. Container Integration + Certificates | 17 | Not started | - |
| 5. Project Setup & Core Infrastructure | 0 | Not started | - |
| 6. Dataset Management | 0 | Not started | - |
| 7. Configuration Parser & Validator | 0 | Not started | - |
| 8. Secrets Manager | 0 | Not started | - |
| 9. Audit Log Service | 7 | Planned (3 plans) | - |
| 10. Provenance Tracker | 0 | Not started | - |
| 11. Checkpoint - Core Services | 0 | Not started | - |
| 12. Anomaly Detector | 0 | Not started | - |
| 13. Network Segmentation | 0 | Not started | - |
| 13.1. Resource Governor | 0 | Not started | - |
| 14. Container Image Security | 0 | Not started | - |
| 15. Checkpoint - Security Services | 0 | Not started | - |
| 16. Orchestrator - Session Management | 0 | Not started | - |
| 17. Orchestrator - Container Orchestration | 0 | Not started | - |
| 18. Orchestrator - LLM-Specific Isolation | 0 | Not started | - |
| 19. Orchestrator API | 0 | Not started | - |
| 20. Checkpoint - Orchestrator | 0 | Not started | - |
| 21. Red Team & Blue Team Integration | 0 | Not started | - |
| 22. Kubernetes Deployment | 0 | Not started | - |
| 23. Threat Modeling & Security Documentation | 0 | Not started | - |
| 24. Final Integration & Testing | 0 | Not started | - |
| 25. Production Readiness Checkpoint | 0 | Not started | - |

**Total:** 55 v1 requirements across 25 phases (original 4 CENTINELA + 21 Bayora phases)

## Coverage Map

| Requirement | Phase | Requirement | Phase |
|-------------|-------|-------------|-------|
| PROV-01 | Phase 1 | AUDT-01 | Phase 1 |
| PROV-02 | Phase 1 | AUDT-02 | Phase 1 |
| PROV-03 | Phase 1 | AUDT-03 | Phase 1 |
| PROV-04 | Phase 1 | AUDT-04 | Phase 1 |
| PROV-05 | Phase 1 | AUDT-05 | Phase 1 |
| PROV-06 | Phase 1 | AUDT-06 | Phase 1 |
| PROV-07 | Phase 1 | AUDT-07 | Phase 1 |
| PROV-08 | Phase 1 | BUDG-01 | Phase 1 |
| PROV-09 | Phase 1 | BUDG-02 | Phase 1 |
| ORCH-01 | Phase 1 | BUDG-03 | Phase 1 |
| ORCH-02 | Phase 1 | BUDG-04 | Phase 1 |
| ORCH-03 | Phase 1 | BUDG-05 | Phase 1 |
| ORCH-04 | Phase 1 | SIDE-01 | Phase 1 |
| ORCH-05 | Phase 1 | SIDE-02 | Phase 1 |
| ORCH-06 | Phase 1 | SIDE-03 | Phase 1 |
| RED-01 | Phase 2 | CERT-05 | Phase 4 |
| RED-02 | Phase 2 | CERT-06 | Phase 4 |
| RED-03 | Phase 2 | CERT-07 | Phase 4 |
| RED-04 | Phase 2 | CERT-08 | Phase 4 |
| RED-05 | Phase 2 | CERT-09 | Phase 4 |
| RED-06 | Phase 2 | ARCH-01 | Phase 4 |
| RED-07 | Phase 2 | ARCH-02 | Phase 4 |
| RED-08 | Phase 2 | ARCH-03 | Phase 4 |
| RED-09 | Phase 2 | ARCH-04 | Phase 4 |
| RED-10 | Phase 2 | ARCH-05 | Phase 4 |
| RED-11 | Phase 2 | ARCH-06 | Phase 4 |
| BLUE-01 | Phase 3 | ARCH-07 | Phase 4 |
| BLUE-02 | Phase 3 | ARCH-08 | Phase 4 |
| BLUE-03 | Phase 3 | CERT-01 | Phase 4 |
| BLUE-04 | Phase 3 | CERT-02 | Phase 4 |
| BLUE-05 | Phase 3 | CERT-03 | Phase 4 |
| BLUE-06 | Phase 3 | CERT-04 | Phase 4 |

### Phase 5: Project Setup and Core Infrastructure

**Goal:** Foundation for the entire platform — Python package structure with 8 core modules (orchestrator, config, secrets, audit, provenance, anomaly, network, resources), dependencies (Kubernetes client, Docker SDK, FastAPI, cryptography, SQLAlchemy, Prometheus, WireGuard), testing framework (pytest, coverage, K8s mocks), core data models, and enums
**Depends on:** Phase 4
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 5 to break down)

### Phase 6: Dataset Management

**Goal:** Adversarial testing datasets for red/blue team operations — downloads and prepares 5 datasets (AdvBench, JailbreakBench, Gandalf/Lakera, ToxiGen optional, Anthropic HH-RLHF optional) with unified DatasetManager CLI
**Depends on:** Phase 5
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 6 to break down)

### Phase 7: Configuration Parser and Validator

**Goal:** Declarative security policy management — YAML/JSON parser with schema validation, resource limit validation (CPU 0.1-32 cores, Memory 128MB-64GB), circular dependency detection, pretty printer, env var substitution
**Depends on:** Phase 6
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 7 to break down)

### Phase 8: Secrets Manager

**Goal:** Cryptographic key and credential management — AES-256-GCM encryption, PBKDF2 key derivation, ABAC policy DSL, mutual TLS, automatic 24-hour rotation, tmpfs secret injection, HashiCorp Vault or encrypted SQLite backend
**Depends on:** Phase 7
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 8 to break down)

### Phase 9: Audit Log Service

**Goal:** Tamper-evident cryptographic logging — SHA-256 hash chaining, Ed25519 batch signing every 60s, tamper detection with 5s alert SLA, append-only storage, geo-replication to 2+ regions within 10s
**Depends on:** Phase 8
**Plans:** 3 plans

Plans:
- [ ] 09-audit-log-service-01-PLAN.md — Core audit log: schema, SHA-256 Merkle chain, append-only storage (PostgreSQL/SQLite), non-blocking async writer
- [ ] 09-audit-log-service-02-PLAN.md — Verification CLI: verify_audit.py script, chain integrity verification, correlation ID queries, performance (<1s for 10K entries)
- [ ] 09-audit-log-service-03-PLAN.md — Query API + RBAC: FastAPI read-only endpoints, role-based access control (admin/auditor/orchestrator)

### Phase 10: Provenance Tracker

**Goal:** Forensic data lineage tracking — graph-based storage (NetworkX or adjacency list), parent-child relationship tracking, backward tracing (origin of any artifact), forward tracing (all derived artifacts), isolation boundary crossing detection
**Depends on:** Phase 9
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 10 to break down)

### Phase 11: Checkpoint - Core Services

**Goal:** Validation checkpoint ensuring all core services (Setup, Datasets, Config, Secrets, Audit, Provenance) pass tests
**Depends on:** Phase 10
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 11 to break down)

### Phase 12: Anomaly Detector

**Goal:** Real-time security monitoring — syscall monitoring (seccomp/eBPF), network traffic monitoring (exfiltration detection), container escape detection, ML-based adversarial prompt detection, timing side-channel detection; alert thresholds >3σ deviation, >10 MB/min traffic, <1s escape termination
**Depends on:** Phase 11
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 12 to break down)

### Phase 13: Network Segmentation

**Goal:** WireGuard-based network isolation — tunnel setup with keypair generation per tenant, Kubernetes NetworkPolicy for inter-tenant traffic blocking, egress filtering with endpoint whitelisting, DNS tunneling prevention, network boundary crossing logging
**Depends on:** Phase 12
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 13 to break down)

### Phase 13.1: Resource Governor

**Goal:** cgroup v2 resource controls — CPU quota enforcement with pinning (prevent cache side-channels), memory limit enforcement with OOM killer isolation, I/O bandwidth limits, timing jitter (50-200ms random delay), Prometheus metrics per tenant
**Depends on:** Phase 13
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 13.1 to break down)

### Phase 14: Container Image Security

**Goal:** Supply chain security — Trivy integration for CVE scanning (reject critical/high), cosign integration for image signature verification, base image whitelist enforcement, image digest logging, private registry authentication
**Depends on:** Phase 13
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 14 to break down)

### Phase 15: Checkpoint - Security Services

**Goal:** Validation checkpoint for anomaly detection, network, resource, and image scanning services
**Depends on:** Phase 14
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 15 to break down)

### Phase 16: Orchestrator - Session Management

**Goal:** Session lifecycle orchestration — session creation with secret allocation (UUID v4, <5s SLA), state tracking (CREATED, RUNNING, COMPLETED, TERMINATED), termination with cleanup (<10s archive, <30s memory scrub), automatic timeout enforcement (3600s max), Prometheus metrics
**Depends on:** Phase 15
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 16 to break down)

### Phase 17: Orchestrator - Container Orchestration

**Goal:** Kubernetes pod management — pod creation with security context (rootless, seccomp, minimal capabilities), namespace isolation (PID, network, IPC, UTS), resource allocation with cgroup v2 controls, network policy application with WireGuard tunnels, pod lifecycle management
**Depends on:** Phase 16
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 17 to break down)

### Phase 18: Orchestrator - LLM-Specific Isolation

**Goal:** AI-specific security controls — KV cache clearing between sessions (vLLM/TGI integration), prompt artifact isolation, output sanitization (strip control characters, prevent prompt injection), model weight isolation (copy-on-write per Client_LLM), output sandboxing
**Depends on:** Phase 17
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 18 to break down)

### Phase 19: Orchestrator API

**Goal:** REST API with FastAPI — endpoints: POST /sessions, GET /sessions/{id}, DELETE /sessions/{id}, POST /sessions/{id}/execute (<10s SLA), GET /health (K8s probes), GET /metrics (Prometheus); authentication via JWT or mutual TLS
**Depends on:** Phase 18
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 19 to break down)

### Phase 20: Checkpoint - Orchestrator

**Goal:** End-to-end orchestrator validation checkpoint
**Depends on:** Phase 19
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 20 to break down)

### Phase 21: Red Team and Blue Team Integration

**Goal:** Red Team (attackers) — adversarial prompt execution, rate limiting (100 prompts/min), batch execution from AdvBench/JailbreakBench/HarmBench; Blue Team (defenders) — classifier deployment, prompt filtering/blocking, A/B testing, training on ToxiGen/HH-RLHF, performance metrics (precision, recall, F1)
**Depends on:** Phase 20
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 21 to break down)

### Phase 22: Kubernetes Deployment

**Goal:** Production-ready deployment artifacts — Helm charts for orchestrator (StatefulSet) and tenant pods, Terraform modules for AWS EKS/GCP GKE/Azure AKS, RBAC policies (least privilege), monitoring stack (Prometheus, Grafana, Loki/ELK), dashboards, deployment validation tests (kind cluster, dry-run)
**Depends on:** Phase 21
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 22 to break down)

### Phase 23: Threat Modeling and Security Documentation

**Goal:** Risk transparency and compliance — threat model using STRIDE methodology, CVSS v3.1 risk scoring for all threats, mitigation documentation for threats with risk score >4.0, residual risk documentation, security runbook
**Depends on:** Phase 22
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 23 to break down)

### Phase 24: Final Integration and Testing

**Goal:** End-to-end validation — test scenarios (Red Team attacks Client LLM, Blue Team blocks attack, multi-tenant isolation, complete session lifecycle); performance benchmarks (<5s session creation, <10s prompt execution, <30s termination, <10s audit replication); security validation; target >80% code coverage
**Depends on:** Phase 23
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 24 to break down)

### Phase 25: Production Readiness Checkpoint

**Goal:** Final validation before production deployment
**Depends on:** Phase 24
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 25 to break down)
