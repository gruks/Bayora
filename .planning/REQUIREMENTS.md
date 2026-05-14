# Requirements: CENTINELA

**Defined:** 2025-05-14
**Core Value:** Enable regulated companies to obtain independent, forensically defensible AI safety audits with signed certificates that satisfy compliance frameworks (HIPAA, SOX, GDPR, EU AI Act).

## v1 Requirements

### Container Architecture

- [ ] **ARCH-01**: System runs as five isolated Docker containers (red-agent, orchestrator, blue-agent, llm-sandbox, audit)
- [ ] **ARCH-02**: Each container sits on its own Docker bridge network with no direct routes between them
- [ ] **ARCH-03**: Orchestrator is the only host present across all networks (blindfolded intermediary)
- [ ] **ARCH-04**: Linux namespaces (pid, net, ipc, uts, mnt) enforced per container
- [ ] **ARCH-05**: Seccomp profiles whitelist only necessary syscalls per container role
- [ ] **ARCH-06**: gVisor (runsc) as container runtime for kernel-intercept isolation
- [ ] **ARCH-07**: cgroup v2 hard limits on CPU, memory, and I/O per container
- [ ] **ARCH-08**: Single `docker compose up` command deploys entire system

### Multi-Provider Support

- [ ] **PROV-01**: Universal provider adapter supports OpenAI (GPT-4o, GPT-4-turbo, GPT-3.5-turbo)
- [ ] **PROV-02**: Universal provider adapter supports Anthropic (Claude 3.5 Sonnet, Claude 3 Opus, Claude Haiku)
- [ ] **PROV-03**: Universal provider adapter supports Ollama (Mistral 7B, LLaMA 3, Phi-3)
- [ ] **PROV-04**: Universal provider adapter supports custom OpenAI-compatible endpoints
- [ ] **PROV-05**: API key held in RAM only — never written to disk
- [ ] **PROV-06**: API key never forwarded to red or blue agents
- [ ] **PROV-07**: API key never logged in audit trail (even as hash)
- [ ] **PROV-08**: Session start endpoint (/session/start) instantiates scoped provider in memory
- [ ] **PROV-09**: Session end endpoint (/session/end) deletes object and wipes key from memory

### Red-Team Agent

- [ ] **RED-01**: Red-agent fires adversarial prompts from AdvBench dataset
- [ ] **RED-02**: Red-agent fires adversarial prompts from JailbreakBench dataset
- [ ] **RED-03**: Red-agent includes adaptive mutation engine that learns from failures
- [ ] **RED-04**: When attack blocked, red-agent mutates prompt using LLM itself and retries
- [ ] **RED-05**: Mutation escalation through roleplay framing, academic framing, hypothetical framing, indirect instruction
- [ ] **RED-06**: Mutation lineage logged to audit chain showing iterations to find vulnerability
- [ ] **RED-07**: Domain-specific attack profiles for Healthcare (HIPAA compliance)
- [ ] **RED-08**: Domain-specific attack profiles for Finance (SOX / MiFID II compliance)
- [ ] **RED-09**: Domain-specific attack profiles for Legal (GDPR / Bar regulations)
- [ ] **RED-10**: Domain-specific attack profiles for General (EU AI Act Article 9)
- [ ] **RED-11**: Attack profiles loaded from curated JSONL files with severity ratings

### Blue-Team Agent

- [ ] **BLUE-01**: Blue-agent classifies model outputs as safe or harmful
- [ ] **BLUE-02**: Blue-agent classifier trained on HH-RLHF dataset
- [ ] **BLUE-03**: Blue-agent classifier trained on ToxiGen dataset
- [ ] **BLUE-04**: Blue-agent receives only model response, never the original prompt (isolation)
- [ ] **BLUE-05**: Safety scoring with 50+ core metrics
- [ ] **BLUE-06**: Evaluation runs across multiple seeds with confidence intervals

### Orchestrator

- [ ] **ORCH-01**: Orchestrator acts as neutral core receiving attacks from red
- [ ] **ORCH-02**: Orchestrator strips metadata before forwarding to LLM sandbox
- [ ] **ORCH-03**: Orchestrator adds random timing jitter (50-200ms uniform) to defeat side-channel inference
- [ ] **ORCH-04**: Orchestrator forwards only model output to blue-agent
- [ ] **ORCH-05**: Campaign management API for test sequencing
- [ ] **ORCH-06**: State machine for workflow management

### Audit System

- [ ] **AUDT-01**: Write-only Merkle-chained log in isolated audit container
- [ ] **AUDT-02**: Red, blue, and LLM containers have zero network access to audit
- [ ] **AUDT-03**: Every event includes timestamp and actor
- [ ] **AUDT-04**: Every event includes SHA-256 hash of event payload (never the payload itself for red prompts)
- [ ] **AUDT-05**: Every event includes hash of previous entry (prev_hash)
- [ ] **AUDT-06**: Full entry hash becomes next entry's prev_hash (chain integrity)
- [ ] **AUDT-07**: verify_audit.py script recomputes every hash and confirms chain integrity

### Safety Certificate

- [ ] **CERT-01**: Generate signed PDF safety certificate at session end
- [ ] **CERT-02**: Certificate includes model under test (provider + model name)
- [ ] **CERT-03**: Certificate includes test date and session ID
- [ ] **CERT-04**: Certificate includes total attacks fired and breakdown by domain
- [ ] **CERT-05**: Certificate includes vulnerabilities found (count, severity, category)
- [ ] **CERT-06**: Certificate includes number of adaptive mutation rounds required
- [ ] **CERT-07**: Certificate includes audit chain root hash (Merkle root)
- [ ] **CERT-08**: Certificate includes Ed25519 signature from orchestrator session key
- [ ] **CERT-09**: Certificate includes verification command for recipient to confirm integrity

### Budget Guard

- [ ] **BUDG-01**: Configurable maximum number of API calls per session (default: 50)
- [ ] **BUDG-02**: Configurable maximum estimated spend in USD (default: $5.00)
- [ ] **BUDG-03**: Per-provider cost-per-token estimates (OpenAI: $0.005/1k, Anthropic: $0.003/1k)
- [ ] **BUDG-04**: Graceful session close when either limit reached
- [ ] **BUDG-05**: Generate partial certificate covering completed tests when budget exhausted

### Side-Channel Mitigations

- [ ] **SIDE-01**: Timing jitter (50-200ms uniform distribution) added to every response before forwarding to blue
- [ ] **SIDE-02**: KV cache flushed between every session in LLM sandbox
- [ ] **SIDE-03**: cgroup v2 enforces hard CPU, memory, and I/O quotas per container

## v2 Requirements

### Advanced Security

- **SIDE-04**: Trusted Execution Environments (Intel TDX) for orchestrator
- **SIDE-05**: Multi-party computation protocols to eliminate operator collusion risk
- **SIDE-06**: Hardware side-channel mitigation (dedicated physical hosts)

### Extended Features

- **MULTI-01**: Multi-modal testing (image, audio inputs)
- **CUSTOM-01**: Custom attack development platform for developers
- **CONT-01**: Real-time continuous monitoring mode

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time chat interface | Certificate is the deliverable, not interactive UI |
| Mobile app | Web-based admin interface sufficient for v1 |
| Model training/fine-tuning security | Focus on testing, not model modification |
| Runtime guardrails as primary | Defender-only, not adversarial testing |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ARCH-01 - ARCH-08 | Phase 4 | Pending |
| PROV-01 - PROV-09 | Phase 1 | Pending |
| RED-01 - RED-11 | Phase 2 | Pending |
| BLUE-01 - BLUE-06 | Phase 3 | Pending |
| ORCH-01 - ORCH-06 | Phase 1 | Pending |
| AUDT-01 - AUDT-07 | Phase 1 | Pending |
| CERT-01 - CERT-09 | Phase 4 | Pending |
| BUDG-01 - BUDG-05 | Phase 1 | Pending |
| SIDE-01 - SIDE-03 | Phase 1 | Pending |

**Coverage:**
- v1 requirements: 55 total
- Mapped to phases: 55
- Unmapped: 0 ✓

---
*Requirements defined: 2025-05-14*
*Last updated: 2025-05-14 after research synthesis*