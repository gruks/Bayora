# Architecture Research

**Domain:** AI Safety Testing Platforms
**Researched:** 2026-05-14
**Confidence:** HIGH

## Standard Architecture

### System Overview

AI safety testing platforms follow a multi-agent architecture pattern with strong isolation boundaries. The ecosystem research reveals consistent component patterns across platforms like AISafetyLab, RedAmon, DeepRed, and commercial red-teaming systems.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Orchestrator Layer                          │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              Workflow Engine / Campaign Manager              │    │
│  │   - Test scheduling    - Test prioritization    - Resource  │    │
│  └─────────────────────────────┬───────────────────────────────┘    │
└────────────────────────────────┼────────────────────────────────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           │                     │                     │
           ▼                     ▼                     ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│  Red-Team Agent   │  │  Blue-Team Agent  │  │    Audit System   │
│  (Attack Engine) │  │ (Evaluation/Def)  │  │  (Logging/Compl)  │
├───────────────────┤  ├───────────────────┤  ├───────────────────┤
│ - Attack profiles│  │ - Safety scoring  │  │ - Decision logs  │
│ - Prompt mutation│  │ - Benchmark eval  │  │ - Tool invocation│
│ - Target config  │  │ - Response eval   │  │ - Tamper-evidence│
└────────┬──────────┘  └────────┬──────────┘  └────────┬──────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                │
                                ▼
               ┌───────────────────────────────────┐
               │        LLM Sandbox (Isolation)     │
               ├───────────────────────────────────┤
               │ - Docker/gVisor container          │
               │ - Network isolation               │
               │ - Resource limits (CPU/memory)    │
               │ - Egress filtering                │
               │ - Syscall filtering               │
               └───────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Orchestrator** | Test campaign management, workflow sequencing, resource allocation | Python/FastAPI + task queue (Celery/Redis), state machine for test phases |
| **Red-Team Agent** | Attack generation, prompt mutation, target interaction | LLM client wrapper + mutation strategies + attack profile loader |
| **Blue-Team Agent** | Safety evaluation, benchmark scoring, response analysis | Scoring models (rule-based + ML) + evaluation harnesses |
| **LLM Sandbox** | Isolated execution of untrusted code/LLM interactions | Docker containers with gVisor, network=none, memory limits, no-new-privileges |
| **Audit System** | Immutable logging, compliance evidence, forensic reconstruction | Append-only store (S3/WORM), cryptographic chaining, correlation ID tracking |

## Recommended Project Structure

```
centinela/
├── orchestrator/           # Test orchestration engine
│   ├── workflows/          # Campaign definitions, test sequences
│   ├── scheduler/         # Test timing, prioritization
│   └── state/              # Campaign state management
├── red-agent/             # Red-team attack engine
│   ├── profiles/           # Domain-specific attack profiles
│   ├── mutation/          # Prompt mutation strategies
│   └── targets/           # Target configuration management
├── blue-agent/            # Evaluation and scoring
│   ├── scorers/           # Safety evaluation models
│   ├── benchmarks/        # Standard benchmark integrations
│   └── reports/           # Results aggregation
├── llm-sandbox/           # Execution isolation layer
│   ├── containers/        # Container templates/configs
│   ├── security/         # Network/egress filters
│   └── monitoring/        # Resource monitoring
├── audit/                 # Compliance and logging
│   ├── logs/              # Immutable audit store
│   ├── chains/           # Hash chain verification
│   └── api/              # Audit query API
└── docker/                # Container orchestration
    ├── networks/          # Network isolation configs
    └── volumes/           # Shared data volumes
```

### Structure Rationale

- **orchestrator/:** Central workflow coordinator - drives all other components, must exist first
- **red-agent/:** Depends on orchestrator for test campaigns, needs sandbox for target interaction
- **blue-agent/:** Independent evaluation - can run in parallel with red-team
- **llm-sandbox/:** Foundation layer - all LLM interactions pass through it, no dependencies on other components
- **audit/:** Cross-cutting - receives events from all components, no outgoing dependencies
- **docker/:** Infrastructure definition - must exist before any component deployment

## Architectural Patterns

### Pattern 1: Container Isolation with Defense-in-Depth

**What:** Multi-layer sandboxing where each LLM interaction passes through isolated containers with network, filesystem, and syscall restrictions.

**When to use:** Always - this is the baseline security pattern for AI safety testing. Without it, prompt injection or tool misuse can compromise the host system.

**Trade-offs:**
- Pros: Prevents data exfiltration, limits blast radius from attacks, enables safe testing of harmful prompts
- Cons: Performance overhead (~200-500ms per execution), complexity in debugging, potential for container escape (recent research shows frontier models can escape misconfigured containers)

**Example:**
```python
# Docker sandbox configuration from RLM and llm-sandbox patterns
sandbox_config = {
    "image": "python:3.11-slim",
    "memory_limit": "512m",
    "cpus": 1,
    "network_mode": "none",           # Blocks data exfiltration
    "read_only_filesystem": True,      # Prevents file writes
    "user": "nobody",                  # Non-root execution
    "security_opt": "no-new-privileges",  # Blocks escalation
    "tmpfs": "/tmp:size=50m"           # Ephemeral storage
}
```

### Pattern 2: Event-Driven Orchestration

**What:** Components communicate through an event bus (message queue) rather than direct API calls, enabling loose coupling and parallel execution.

**When to use:** When red-team and blue-team can run simultaneously, when audit needs to observe all traffic without coupling to other components.

**Trade-offs:**
- Pros: Decouples components, enables independent scaling, natural audit trail via message topics
- Cons: Event ordering complexity, eventual consistency challenges, more infrastructure

**Example:**
```python
# Event flow pattern
test_request = {
    "campaign_id": "uuid",
    "test_type": "prompt_injection",
    "payload": "...",
    "correlation_id": "uuid"  # Links all events in a test run
}

# Red-team publishes attack attempt
event_bus.publish("attack.started", test_request)

# LLM sandbox processes and returns
event_bus.publish("sandbox.executed", {
    "correlation_id": test_request["correlation_id"],
    "output": "...",
    "metadata": {...}
})

# Blue-team evaluates
event_bus.publish("evaluation.complete", {
    "correlation_id": test_request["correlation_id"],
    "safety_score": 0.85,
    "flags": []
})

# Audit always observes (even if others fail)
audit_log.write({
    "correlation_id": test_request["correlation_id"],
    "event": "attack.started",
    "timestamp": "..."
})
```

### Pattern 3: Hash-Chained Immutable Audit

**What:** Each audit entry includes a hash of the previous entry, creating a tamper-evident chain. Modifying any record breaks the chain and is detectable.

**When to use:** When regulatory compliance is required (EU AI Act, SOC 2, HIPAA), when forensic reconstruction is needed for incident response.

**Trade-offs:**
- Pros: Detects tampering, satisfies compliance requirements, enables forensic reconstruction
- Cons: Storage overhead (~40 bytes per entry), append-only (no updates), complex to implement correctly

**Example:**
```python
# Hash chain implementation pattern
def append_audit_entry(previous_hash: str, entry: dict) -> str:
    entry["previous_hash"] = previous_hash
    entry["timestamp"] = iso8601_now()
    entry_json = json.dumps(entry, sort_keys=True)
    entry_hash = sha256(entry_json.encode()).hexdigest()
    return entry_hash

# Verification - any modification breaks chain
def verify_chain(entries: list[dict]) -> bool:
    for i, entry in enumerate(entries):
        computed = sha256(json.dumps({
            "previous_hash": entry.get("previous_hash"),
            "event": entry["event"],
            "timestamp": entry["timestamp"]
        }, sort_keys=True).encode()).hexdigest()
        if computed != entry.get("hash"):
            return False  # Tampering detected
    return True
```

### Pattern 4: Universal Provider Adapter

**What:** Abstraction layer that normalizes API calls across different LLM providers (OpenAI, Anthropic, Google, local models) into a unified interface.

**When to use:** When testing multiple LLM targets, when provider availability varies, when comparing cross-provider safety characteristics.

**Trade-offs:**
- Pros: Provider flexibility, easier testing across targets, abstracts API differences
- Cons: Feature parity gaps between providers, rate limit handling complexity, cost optimization challenges

**Example:**
```python
class UniversalProviderAdapter:
    def __init__(self, provider: str, config: dict):
        self.client = self._create_client(provider, config)

    def _create_client(self, provider: str, config: dict):
        adapters = {
            "openai": OpenAIClient,
            "anthropic": AnthropicClient,
            "google": GoogleClient,
            "local": LocalClient
        }
        return adapters[provider](config)

    def generate(self, prompt: str, **kwargs) -> Response:
        # Normalized response format across all providers
        return self.client.complete(prompt, **kwargs)

    def get_token_count(self, text: str) -> int:
        return self.client.count_tokens(text)
```

## Data Flow

### Request Flow

```
[Test Campaign Request]
         │
         ▼
┌─────────────────┐
│   Orchestrator │ ← Receives campaign config, test list
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────┐
│ Red   │ │ Audit │ ← Always logs campaign start
│ Agent │ └───────┘
└───┬───┘
    │ attack_payload={prompt, target, profile}
    ▼
┌──────────────┐
│ LLM Sandbox  │ ← Isolated execution
└────┬─────────┘
     │ response={output, metrics}
     ▼
┌───────┐ ┌───────┐
│ Blue  │ │ Audit │ ← Logs prompt/response pair
│ Agent │ └───────┘
└───┬───┘
    │ evaluation={score, flags, report}
    ▼
┌──────────────┐
│ Orchestrator │ ← Aggregates results, updates campaign
└────┬─────────┘
     │
     ▼
┌───────┐ ┌───────┐
│ Audit │ ← Final report, compliance evidence
│ Store │
└───────┘
```

### State Management

```
┌────────────────────────────────────────────────────────────┐
│                    Orchestrator State                       │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Campaign States: pending → running → completed        │ │
│  │ Test States: pending → executing → evaluated → done   │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌────────────────┐   ┌────────────────┐   ┌────────────────┐
│  Red-Agent     │   │  Blue-Agent   │   │  Audit System  │
│  State         │   │  State        │   │  State         │
│  - active tests│   │  - pending    │   │  - entry count │
│  - queue       │   │  - complete   │   │  - chain head  │
└────────────────┘   └────────────────┘   └────────────────┘
```

### Key Data Flows

1. **Test Campaign Flow:** Orchestrator → Red-Agent → LLM-Sandbox → Blue-Agent → Orchestrator → Audit
   - Correlation ID links all events
   - Each component adds its own event to audit

2. **Evaluation Flow:** LLM-Sandbox returns output → Blue-Agent scores → Score attached to audit entry
   - Enables pass/fail decision per test
   - Aggregates to campaign-level metrics

3. **Audit Observation Flow:** All components publish to audit bus (async, non-blocking)
   - Audit never blocks test execution
   - Audit failures do not halt testing

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-1k tests/day | Single orchestrator, local Docker, SQLite audit store - monolith is fine |
| 1k-100k tests/day | Separate orchestrator service, Redis queue, PostgreSQL audit, horizontal red/blue agent scaling |
| 100k+ tests/day | Distributed orchestration (multiple workers), sharded audit store, Kubernetes-based sandbox fleet, CDN for audit queries |

### Scaling Priorities

1. **First bottleneck: Orchestrator throughput** - When test queue backs up, add worker processes, migrate from polling to event-driven
2. **Second bottleneck: LLM sandbox startup time** - Pre-warm containers, use container pooling, consider gVisor for faster startup
3. **Third bottleneck: Audit storage** - Move to time-series DB, implement tiered storage (hot/cold), add sampling for low-risk tests

## Anti-Patterns

### Anti-Pattern 1: Direct Database Access from Agents

**What people do:** Red-agent and blue-agent directly write to shared database, bypassing orchestrator state management.

**Why it's wrong:** Race conditions in test state, orphaned records on failures, impossible to reconstruct test lineage.

**Do this instead:** Use orchestrator as state store, agents communicate state changes through orchestrator API, audit observes events rather than polling DB.

### Anti-Pattern 2: Network-Enabled Sandboxes by Default

**What people do:** Enabling network access in LLM sandbox "for debugging" or "because the model needs context."

**Why it's wrong:** Prompt injection can exfiltrate data, tool calls can reach attacker-controlled servers, defeats entire sandbox purpose. Research shows this is the most common misconfiguration leading to sandbox escape.

**Do this instead:** Default to network=none, explicitly whitelist only required domains, log all network attempts even if blocked.

### Anti-Pattern 3: Logging Only Failures

**What people do:** Only logging when tests fail or safety scores drop, treating success as "nothing to log."

**Why it's wrong:** Compliance requires full decision logging (EU AI Act Article 12), cannot reconstruct why decisions passed, auditors cannot verify testing occurred.

**Do this instead:** Log every interaction - inputs, prompts, responses, evaluations, decisions. Full audit trail is the default, not opt-in.

### Anti-Pattern 4: No Correlation IDs Across Components

**What people do:** Each component generates its own IDs, making it impossible to trace a single test through the system.

**Why it's wrong:** Forensic reconstruction impossible - "why did this test pass?" cannot be answered. Compliance audits fail.

**Do this instead:** Orchestrator generates correlation_id at campaign start, propagates through all components, audit uses correlation_id as primary key.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| LLM Providers (OpenAI, Anthropic, etc.) | API client with provider adapter pattern | Handle rate limits, implement retries, normalize response formats |
| Vulnerability Scanners (OpenVAS, Nuclei) | Docker container with API server | Spawn on-demand, clean up after, share results via volume |
| SIEM Systems (Splunk, Elastic) | Audit log export via webhook or scheduled batch | Ensure structured JSON format, include all required fields |
| Compliance Platforms | Audit API with read-only access | Implement RBAC, log all access to audit logs themselves |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Orchestrator → Red-Agent | gRPC or REST API | Async preferred - orchestrator fires and forgets |
| Red-Agent → LLM Sandbox | Direct container invocation or IPC | Sandbox may be local Docker or remote service |
| LLM Sandbox → Blue-Agent | Message queue or callback | Enables parallel evaluation |
| All → Audit | Event bus (Kafka, Redis pub/sub, or HTTP webhooks) | Fire-and-forget from source, audit is non-blocking |

## Build Order Recommendations

Based on dependency analysis:

1. **Phase 1: LLM Sandbox (Foundation)**
   - No dependencies on other components
   - All subsequent components require isolated execution
   - Start with Docker container template, add security layers incrementally

2. **Phase 2: Audit System (Cross-Cutting)**
   - Must observe all components once they exist
   - Can be stubbed initially, implement full hash-chaining later
   - Implement basic logging first, add compliance features in Phase 3+

3. **Phase 3: Orchestrator (Coordination)**
   - Depends on sandbox and audit (via observer pattern)
   - Manages workflow state, scheduling, resource allocation
   - Implement campaign CRUD first, then test execution logic

4. **Phase 4: Red-Agent (Attack Engine)**
   - Requires orchestrator (to receive test definitions)
   - Requires sandbox (to execute attacks safely)
   - Implement prompt mutation strategies, attack profiles

5. **Phase 5: Blue-Agent (Evaluation)**
   - Can run in parallel with red-agent
   - Depends on sandbox (to observe model outputs)
   - Implement scoring models, benchmark integrations

**Rationale:** Build isolation layer first (nothing works without it), then add observability (you can't debug without it), then add coordination (tests need orchestration), then add the agents (red before blue because evaluation depends on having something to evaluate).

## Sources

- OWASP AI Testing Guide (v1, November 2025) - https://owasp.org/www-project-ai-testing-guide/
- AISafetyLab Framework (arXiv, February 2025) - https://github.com/thu-coai/AISafetyLab
- RedAmon Container Architecture (GitHub, February 2026) - https://github.com/l0cs/redamon
- LLM Sandbox Security Patterns (redteams.ai, March 2026) - https://redteams.ai/topics/walkthroughs/defense/sandboxed-tool-execution
- RLM Python Library (PyPI, v2.1.0, January 2026) - https://pypi.org/project/rlm-python/
- LLM Rustyolo (GitHub, November 2025) - https://github.com/brooksomics/llm-rustyolo
- SandboxEscapeBench (arXiv, March 2026) - https://huggingface.co/papers/2603.02277
- Audit Trail Compliance Research (Rends, May 2026) - https://rends.ai/blog/building-audit-trails-for-ai-agents-compliance-requirements-and-implementation-best-practices
- EU AI Act Article 12 Documentation Requirements - https://artificialintelligenceact.eu/article/12/
- NIST AI Agent Identity and Authorization Concept Paper (February 2026)

---

*Architecture research for: AI Safety Testing Platforms*
*Researched: 2026-05-14*
