# Project Research Summary

**Project:** CENTINELA — AI Safety Testing Platform
**Domain:** AI Safety Testing Platforms (Containerized Adversarial Testing)
**Researched:** 2026-05-14
**Confidence:** MEDIUM-HIGH

## Executive Summary

CENTINELA is an AI safety testing platform designed to validate AI systems through adversarial red-teaming, vulnerability detection, and compliance assessment. The research confirms this is a multi-agent architecture domain requiring strong isolation boundaries between components — the five-container CENTINELA architecture (orchestrator, red-agent, blue-agent, LLM-sandbox, audit) is the recommended approach for security-sensitive deployments.

The recommended stack centers on Python 3.12+ with FastAPI for async performance, LiteLLM for multi-provider LLM abstraction, and Docker Compose for container isolation. The key differentiators identified are: (1) Merkle-chained audit logs with cryptographic verification, (2) container-based network isolation to prevent attack leakage, (3) signed PDF certificates as tangible compliance deliverables, and (4) side-channel mitigations addressing emerging threat vectors.

Critical pitfalls to avoid include: single-turn testing bias (multi-turn attacks succeed 2-10x more often), static test suites that become obsolete within months, and evaluation instability blindness (single-run evaluations miss probabilistic failures). The roadmap should prioritize foundation (sandbox + audit + orchestrator), then attack engine, then adaptive capabilities. Phases 2 and 3 will likely need deeper research during planning due to the complexity of multi-turn attack profiles and adaptive mutation engines.

## Key Findings

### Recommended Stack

**Core technologies:**
- **Python 3.12+** — Primary language for AI/ML testing ecosystem, async-first libraries
- **FastAPI 0.115+** — Native async, Pydantic validation, 2-5x throughput advantage over Flask for concurrent LLM workloads
- **LiteLLM 1.84+** — Multi-provider gateway (100+ providers), unified API, 8ms P95 latency, built-in cost tracking
- **Docker Compose 2.38+** — Container orchestration with network segmentation, health checks, internal networks
- **PostgreSQL 16+** — Primary database with async SQLAlchemy support, JSONB for audit payloads
- **Redis 7.4+** — Task queue broker (Celery), session cache, rate limiting
- **Celery 5.4+** — Async task queue with retry/DLQ patterns
- **SignLedger/ads-foundation** — Merkle-chained audit logging with SHA-256 hash chains

**Key anti-patterns to avoid:**
- Flask for new AI projects (use FastAPI for async)
- SQLAlchemy sync with async engine (causes MissingGreenlet errors)
- Pickle serialization in Celery (code injection risk — use JSON)
- Docker Compose V1 (deprecated)

### Expected Features

**Must have (table stakes):**
- Automated Red-Teaming — Core to any AI safety platform, baseline expectation
- Prompt Injection Detection — OWASP LLM Top 10 #1, universal requirement
- Multi-Provider Support — Enterprise deployments span multiple LLM providers
- Evaluation/Scoring Metrics — Quantitative safety assessment
- Audit Trail/Logging — Compliance evidence, regulatory requirements

**Should have (competitive differentiators):**
- Forensically Auditable Certificates — Signed PDF with cryptographic attestation
- Merkle-Chained Audit Log with Ed25519 — Tamper-evident, cryptographically verifiable
- Five Isolated Docker Containers — Network isolation prevents attack leakage
- Adaptive Red-Teaming with Prompt Mutation — Evolving attacks find novel vulnerabilities
- Domain-Specific Attack Profiles — Targeted testing for Healthcare, Finance, Legal

**Defer (v2+):**
- Side-Channel Mitigations (timing jitter, KV cache flush) — Advanced security, niche market
- Multi-Modal Testing — High complexity, focus on text first
- Custom Attack Development Platform — Developer feature, secondary to core value

### Architecture Approach

The standard pattern is a multi-agent architecture with strong isolation boundaries:

1. **Orchestrator** — Test campaign management, workflow sequencing, resource allocation (Python/FastAPI + Celery)
2. **Red-Team Agent** — Attack generation, prompt mutation, target interaction (LLM client + mutation strategies)
3. **Blue-Team Agent** — Safety evaluation, benchmark scoring, response analysis (scoring models + evaluation harnesses)
4. **LLM Sandbox** — Isolated execution (Docker/gVisor container, network=none, resource limits)
5. **Audit System** — Immutable logging, compliance evidence, cryptographic chaining

Data flows as: Orchestrator → Red-Agent → LLM-Sandbox → Blue-Agent → Orchestrator → Audit, with correlation IDs linking all events for forensic reconstruction.

Build order: (1) LLM Sandbox (foundation — all interactions pass through), (2) Audit System (cross-cutting observer), (3) Orchestrator (coordination), (4) Red-Agent (attack engine), (5) Blue-Agent (evaluation).

### Critical Pitfalls

1. **Single-Turn Testing Bias** — Multi-turn jailbreak success rates reach 92.78% (10x higher than single-turn). Must implement multi-turn attack chains with context carry-over testing.

2. **Static Test Suites** — Attack effectiveness decays within months as providers update guardrails. Must maintain attack technique registry with version tracking and effectiveness monitoring.

3. **Evaluation Instability Blindness** — Models exhibit probabilistic behavior. Must run evaluations across multiple seeds, report confidence intervals, test benign perturbations.

4. **Guardrail Illusion** — Testing reflects current state, not adversarial arms race. Must test bypass techniques explicitly, evaluate "deep" vs "shallow" safety.

5. **Missing Multi-Agent Network Risks** — Agent worms, trust capture, amplification only emerge at network level. CENTINELA's five-container model must test inter-container communication.

6. **Evaluation Awareness (Sandbagging)** — Models can detect evaluation contexts and alter responses. Must implement stealth evaluation scenarios.

7. **Proxy Metric Disconnect** — Safety scores don't translate to real-world risk. Must measure capability-based evaluation, harm scenario chains.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Foundation (Sandbox + Audit + Orchestrator Core)
**Rationale:** This is the foundation all other components depend on. LLM Sandbox must exist before any agent can execute safely. Audit system must observe from day one. Orchestrator coordinates everything.

**Delivers:**
- LLM Sandbox with Docker container isolation (network=none, memory limits, no-new-privileges)
- Basic audit trail with logging infrastructure
- Orchestrator with campaign management API
- Core multi-provider support (OpenAI, Anthropic, Ollama)

**Addresses:**
- Basic Audit Trail (P1), Multi-Provider Support (P1), Evaluation/Scoring (P1)
- Compliance Framework Mapping begins here

**Avoids:**
- Pitfall 10: Incomplete audit trail — implement full capture chain from start
- Pitfall 9: No third-party path — design for auditor access from day one
- Pitfall 7: Proxy metric disconnect — build real-world scenario validation
- Pitfall 3: Evaluation instability — variance measurement in all evaluations

**Research Flags:** Deep research needed on: Docker security configurations, gVisor vs native Docker for sandbox isolation, PostgreSQL JSONB schema for audit payloads.

---

### Phase 2: Attack Profile Engine + Multi-Provider Expansion
**Rationale:** With foundation in place, build the attack engine that generates and executes tests. This is where most platforms fail — single-turn static tests.

**Delivers:**
- Red-Agent with attack profile loader
- Basic attack library (50-100 vectors)
- Prompt injection detection capabilities
- Multi-turn test scenarios (minimum 50% of test suite)
- Guardrail bypass testing scenarios

**Addresses:**
- Automated Red-Teaming (P1), Prompt Injection Detection (P1)
- Domain-Specific Profiles (P2) — Healthcare, Finance, Legal
- Adaptive Red-Teaming begins here

**Avoids:**
- Pitfall 1: Single-turn bias — implement multi-turn attack chains from day one
- Pitfall 4: Guardrail illusion — explicit bypass testing
- Pitfall 6: Evaluation awareness — stealth evaluation scenarios
- Pitfall 2: Static test suites — version tracking, attack technique registry
- Pitfall 12: Provider adapter surface gaps — provider-specific vulnerability modules

**Research Flags:** Deep research needed on: MITRE ATLAS attack techniques, OWASP LLM Top 10 attack vectors, multi-turn conversation state management, guardrail bypass techniques.

---

### Phase 3: Adaptive Red-Teaming + Evaluation Engine
**Rationale:** Build the blue-agent evaluation engine in parallel. Adaptive capabilities differentiate from static competitors.

**Delivers:**
- Blue-Agent with safety scoring models
- Adaptive prompt mutation engine
- Evaluation with confidence intervals
- Basic scoring metrics (50 core metrics)
- Compliance mapping (OWASP, NIST)

**Addresses:**
- Adaptive Red-Teaming with Prompt Mutation (P2), Evaluation/Scoring (P1)
- Budget Guard feature (P2) — cost tracking

**Avoids:**
- Pitfall 8: Benchmark over-reliance — real-world scenario testing > benchmark coverage
- Pitfall 11: Human variable underestimation — automated reduces dependency

**Research Flags:** Standard patterns — evaluation methodologies well-documented in research. Skip research-phase for this.

---

### Phase 4: Container Integration + Advanced Audit
**Rationale:** Deploy the full five-container architecture. This is where multi-agent network risks become testable.

**Delivers:**
- Full five-container Docker Compose deployment
- Inter-container network isolation testing
- Agent-to-agent communication path testing
- Merkle-chained audit log with Ed25519 signing
- Signed PDF safety certificates

**Addresses:**
- Five Isolated Docker Containers (P3), Merkle-Chained Audit (P2), PDF Certificates (P2)

**Avoids:**
- Pitfall 5: Missing multi-agent network risks — test propagation, amplification, trust capture, invisibility

**Research Flags:** Deep research needed on: Docker Compose network isolation configurations, Merkle tree implementation, certificate generation with cryptographic attestation.

---

### Phase Ordering Rationale

- **Foundation first:** Sandbox and audit are prerequisites — no other component works without isolation
- **Attack before evaluation:** Need something to evaluate; red drives blue
- **Adaptive after baseline:** Build static first, then add mutation capabilities
- **Integration last:** Full five-container model only after individual components validated
- **Avoids pitfalls:** Each phase explicitly addresses specific pitfalls identified in research

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** Docker security hardening, gVisor vs native container performance trade-offs
- **Phase 2:** Multi-turn conversation state management, MITRE ATLAS integration patterns
- **Phase 4:** Merkle tree batch commit performance, certificate chain verification

Phases with standard patterns (skip research-phase):
- **Phase 3:** Evaluation methodologies well-documented in academic literature

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM-HIGH | Based on WebSearch results, official docs, GitHub statistics. FastAPI/LiteLLM well-established. Docker Compose patterns standard. |
| Features | HIGH | Competitor analysis provides strong signal. OWASP LLM Top 10, NIST AI RMF provide framework alignment. Clear differentiation strategy. |
| Architecture | HIGH | Multi-agent patterns consistent across platforms (AISafetyLab, RedAmon, DeepRed). Build order validated by dependency analysis. |
| Pitfalls | MEDIUM | Based on incident databases (500+ failures), research papers (Cisco, Microsoft, Anthropic). Some gaps in multi-agent network testing patterns. |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **Multi-turn attack chain implementation:** Research is strong on the problem (Cisco data), but implementation patterns are emerging. Plan to validate during Phase 2.
- **Adaptive mutation engine:** Noma Security and EvalGuard have published approaches, but no canonical implementation pattern. Plan to iterate.
- **Side-channel mitigations:** Very niche, limited published research. Defer to v2+ as planned.
- **Provider-specific vulnerability profiles:** Different providers have different profiles, but data is sparse. Plan to build through testing.

## Sources

### Primary (HIGH confidence)
- **FastAPI vs Flask:** WebSearch multiple sources (2025) — 2-5x throughput advantage, native async
- **LiteLLM:** Official docs, GitHub (25k+ stars) — 100+ providers, 8ms P95 latency
- **Docker Compose AI patterns:** WebSearch Docker official (2025-2026)
- **Merkle audit logging:** SignLedger, ads-foundation, viraxlog — WebSearch (2025-2026)
- **AI red-teaming:** Garak (NVIDIA), Promptfoo, LANCE, llm-audit — GitHub/WebSearch (2025-2026)

### Secondary (MEDIUM confidence)
- **Competitor analysis:** EvalGuard, Giskard, HiddenLayer, VirtueRed feature comparisons
- **OWASP LLM Top 10 (2025):** Framework standards
- **NIST AI RMF, MITRE ATLAS:** Compliance framework mapping

### Tertiary (LOW confidence)
- **Side-channel mitigations:** Very limited published research — needs validation during implementation
- **Multi-turn attack effectiveness:** Cisco data strong but specific implementation patterns emerging

---

*Research completed: 2026-05-14*
*Ready for roadmap: yes*
