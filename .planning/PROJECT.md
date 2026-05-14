# CENTINELA

## What This Is

CENTINELA is a forensically auditable, third-party AI safety validation platform that provides independent adversarial testing of any AI deployment — across any provider, any model, and any domain — and produces signed, tamper-proof safety certificates that hold up to regulatory scrutiny. Built for the Bayora Hackathon 2025, AI Safety Infrastructure Track.

## Core Value

Enable regulated companies to obtain independent, forensically defensible AI safety audits with signed certificates that satisfy compliance frameworks (HIPAA, SOX, GDPR, EU AI Act).

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Five-container isolated architecture with Docker bridge networks
- [ ] Adaptive red-teaming engine with prompt mutation
- [ ] Universal provider adapter (OpenAI, Anthropic, Ollama, custom endpoints)
- [ ] Domain-specific attack profiles (Healthcare, Finance, Legal, General)
- [ ] Signed PDF safety certificate generation
- [ ] Tamper-proof Merkle audit log with Ed25519 signing
- [ ] Side-channel mitigations (timing jitter, KV cache flush, cgroup limits)
- [ ] Budget guard for API call limits
- [ ] Single `docker compose up` deployment

### Out of Scope

- Real-time chat interface — certificate is the deliverable
- Mobile app — web-based admin interface sufficient
- Multi-party computation protocols — deferred to future
- Trusted Execution Environments — deferred to future

## Context

**Problem being solved:** Companies deploying AI in production (hospitals, banks, law firms) have zero independent safety validation. Fine-tuned deployments behave differently from base models, compliance frameworks require documented risk assessments, and shared sandbox environments produce unreliable results due to attack strategy leakage.

**Competitive gap:** Existing tools (Garak, Lakera Guard, Azure AI Content Safety) either lack isolation, have no audit trail, or are defender-only. CENTINELA is the first neutral, isolated, adaptive, provider-agnostic platform with forensically auditable results.

**Hackathon constraints:** Single delivery, time-boxed development, must demonstrate all core features working end-to-end.

## Constraints

- **Timeline**: Bayora Hackathon 2025 — single delivery event
- **Tech Stack**: Docker + gVisor, Python 3.11 + FastAPI, Redis Streams, Ollama for local testing
- **Budget**: Must work with free tier APIs where possible (Ollama for testing)
- **Security**: Cryptographic isolation mandatory — no direct network routes between containers
- **Provider Support**: Must support OpenAI, Anthropic, Ollama, and custom OpenAI-compatible endpoints

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Five-container model | Enforces network isolation at Docker level | — Pending |
| gVisor container runtime | Kernel-intercept isolation beyond standard Docker | — Pending |
| Merkle-chained audit log | Forensically defensible, tamper-proof | — Pending |
| Ed25519 signing for certificates | Modern, fast, secure signature scheme | — Pending |
| Universal provider adapter | Provider-agnostic is core value prop | — Pending |
| Adaptive red-teaming | Static attack lists insufficient for real security testing | — Pending |

---
*Last updated: 2025-05-14 after initialization*