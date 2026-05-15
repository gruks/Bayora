# CENTINELA — GitHub Issues

> **34 medium-level, independent tasks** derived from the CENTINELA roadmap (4 original phases + 21 Bayora-imported phases). Each task can be worked on in parallel by different contributors. Interface contracts are self-defined per task.

---

## Phase 1: Foundation

### 1. Python Project Scaffolding & Code Quality Tooling

**Labels:** `infrastructure`, `tooling`, `good-first-issue`

Set up the Python project foundation for all 5 containers (red-agent, orchestrator, blue-agent, llm-sandbox, audit):

- [ ] Create `pyproject.toml` with project metadata, dependencies, and build configuration
- [ ] Configure pytest with coverage reporting, parallel test execution
- [ ] Set up ruff for linting and formatting
- [ ] Configure mypy for type checking
- [ ] Add pre-commit hooks for automated quality gates
- [ ] Create multi-stage Dockerfiles for each of the 5 containers with health checks
- [ ] Set up GitHub Actions CI: lint → type-check → test → build
- [ ] Create `.env.example` with documented configuration options
- [ ] Add `CONTRIBUTING.md` with development setup instructions

**Acceptance Criteria:**
- `pytest` runs with >80% coverage on initial module stubs
- `ruff check .` passes with zero errors
- `mypy .` passes with no type errors
- GitHub Actions CI pipeline passes on PR
- `docker build` succeeds for all 5 container images

---

### 2. Multi-Provider LLM Adapter

**Labels:** `core`, `llm-integration`, `api`

Build a universal provider adapter that normalizes API calls across different LLM providers into a unified interface:

- [ ] Implement `UniversalProviderAdapter` abstract base class with `generate()`, `generate_stream()`, `count_tokens()`
- [ ] Create OpenAI adapter (GPT-4o, GPT-4-turbo, GPT-3.5-turbo)
- [ ] Create Anthropic adapter (Claude 3.5 Sonnet, Claude 3 Opus, Claude Haiku)
- [ ] Create Ollama adapter (Mistral 7B, LLaMA 3, Phi-3)
- [ ] Create custom OpenAI-compatible endpoint adapter
- [ ] Use LiteLLM as underlying gateway for unified API
- [ ] Implement normalized response format across all providers
- [ ] Add rate limit handling with exponential backoff and retry logic
- [ ] API key held in RAM only using `memoryview` — zeroed on session end
- [ ] API key never forwarded to red or blue agents, never logged in audit trail

**Acceptance Criteria:**
- All 4 adapters return identical response schema
- Rate limit retry succeeds up to 3 attempts with backoff
- API key memory is zeroed after session end (verified with memory inspection test)
- Token counting works for all providers
- Custom endpoint adapter works with any OpenAI-compatible API
- Provider instantiation takes <500ms including credential validation

---

### 3. Tamper-Evident Audit Log with SHA-256 Hash Chaining

**Labels:** `core`, `security`, `audit`

Implement a write-only Merkle-chained audit log in the isolated audit container:

- [ ] Design audit entry schema: `{timestamp, actor, event_type, payload_hash, prev_hash, correlation_id, signature}`
- [ ] Implement SHA-256 hash chaining where each entry includes hash of previous entry
- [ ] Create append-only storage with PostgreSQL (or SQLite for dev)
- [ ] Red, blue, and LLM containers have zero network access to audit container
- [ ] Every event includes SHA-256 hash of event payload (never the payload itself for red prompts)
- [ ] Implement `verify_audit.py` CLI script that recomputes every hash and confirms chain integrity
- [ ] Correlation ID links all events in a test run for forensic reconstruction
- [ ] Audit is non-blocking — failures do not halt test execution
- [ ] Add query API for read-only access with RBAC

**Acceptance Criteria:**
- Writing 1M entries takes <10s with PostgreSQL backend
- Verification script detects any single-byte modification in any entry
- Network isolation test confirms containers cannot reach audit host
- Verification of 10K entries completes in <1s
- Correlation ID query returns all related events in chronological order

---

### 4. Budget Guard — API Call & Spend Limits

**Labels:** `core`, `cost-control`, `session`

Implement configurable budget enforcement per session to prevent runaway costs:

- [ ] Configurable max API calls per session (default: 50)
- [ ] Configurable max estimated spend in USD (default: $5.00)
- [ ] Per-provider cost-per-token estimates (OpenAI: $0.005/1k, Anthropic: $0.003/1k)
- [ ] Real-time cost tracking throughout session execution
- [ ] Graceful session close when either limit reached (not hard cut — complete in-flight)
- [ ] Generate partial certificate covering completed tests when budget exhausted
- [ ] Budget state persisted to audit log for compliance traceability
- [ ] Configurable via session creation API parameters

**Acceptance Criteria:**
- Budget limit triggers within 1 API call of configured max
- Cost estimation accuracy within ±5% of actual API charges
- Partial certificate generation includes all completed tests
- Budget override requires explicit admin authorization
- Budget configuration validated on session creation

---

### 5. Side-Channel Mitigation — Timing Jitter & KV Cache Flush

**Labels:** `security`, `side-channel`, `llm-sandbox`

Implement defenses against timing side-channel attacks and inter-session data leakage:

- [ ] Add 50-200ms uniform-distribution timing jitter to every forwarded response
- [ ] Jitter is cryptographically random (secrets.randbelow, not random.uniform)
- [ ] Implement KV cache flushing between every session in LLM sandbox
- [ ] Verify KV cache flush via memory pattern inspection
- [ ] Both mitigations configurable per session (enable/disable, jitter range)
- [ ] Jitter timing logged to audit chain (min/max/mean per session)
- [ ] Compatible with vLLM, TGI, and Ollama inference servers
- [ ] Performance impact benchmark: jitter adds expected ~125ms per response

**Acceptance Criteria:**
- Timing jitter passes Kolmogorov-Smirnov test for uniform distribution (p > 0.05)
- KV cache flush verified with memory pattern test — no residual tokens detectable
- Jitter does not affect response content or ordering
- Configurable range respected (±1ms precision)
- Zero network requests made during jitter calculation

---

## Phase 2: Red-Teaming Engine

### 6. Attack Profile Loader with Domain-Specific Profiles

**Labels:** `red-team`, `data`, `security-testing`

Create a profile system for domain-specific adversarial attack patterns:

- [ ] Design JSONL attack profile schema with fields: `id`, `domain`, `severity`, `category`, `prompt_template`, `attack_vector`, `expected_guardrail`, `mitre_atlas_id`
- [ ] Implement profile loader with validation and integrity checking
- [ ] Create Healthcare domain profile (HIPAA compliance — 25+ attack vectors)
- [ ] Create Finance domain profile (SOX / MiFID II — 25+ attack vectors)
- [ ] Create Legal domain profile (GDPR / Bar regulations — 25+ attack vectors)
- [ ] Create General domain profile (EU AI Act Article 9 — 25+ attack vectors)
- [ ] CLI to list, inspect, validate, and search profiles
- [ ] Profile versioning with semantic versioning for reproducibility
- [ ] Auto-download curated profiles from repository on first use

**Acceptance Criteria:**
- 100+ total attack vectors across 4 domains
- Each profile includes severity ratings (critical/high/medium/low)
- CLI `centinela profiles list --domain healthcare` returns filtered results
- Profile validation catches malformed JSONL with descriptive error
- New profiles can be added without code changes
- All profiles load in <500ms

---

### 7. Prompt Mutation Engine — Adaptive Attack Strategies

**Labels:** `red-team`, `ml`, `mutation`

Build an adaptive mutation engine that evolves attacks when initial attempts are blocked:

- [ ] Implement 4 mutation strategies: roleplay framing, academic framing, hypothetical framing, indirect instruction
- [ ] Mutation engine uses an LLM itself to generate unbounded mutations
- [ ] Track mutation lineage with parent-child relationships logged to audit chain
- [ ] Implement escalation ladder: try direct first → mutate → mutate again → up to 5 attempts per attack
- [ ] Add mutation strategy selection based on which strategy has historically succeeded
- [ ] Mutation temperature and creativity configurable per session
- [ ] Mutation success rate tracking per provider, per domain, per strategy
- [ ] Prevent infinite loops with max mutation attempts per attack (configurable)
- [ ] Mutation lineage queryable via audit chain for forensic review

**Acceptance Criteria:**
- At least 3 different variations produced per blocked attack
- Mutation success rate logged with per-strategy breakdown
- Audit chain shows full lineage: original → attempt 1 → attempt 2 → result
- No infinite loops — hard cap at configured max attempts
- Mutation adds <2s overhead per attempt with cached LLM provider

---

### 8. Multi-Turn Conversation Manager with Context Carry-Over

**Labels:** `red-team`, `conversation`, `state`

Build conversation state management for multi-turn adversarial testing:

- [ ] Implement conversation state tracking with full history per session
- [ ] Context carry-over across turns with token-count-aware truncation
- [ ] Support minimum 50% multi-turn test scenarios in the test suite
- [ ] Track conversation depth, turn count, and cumulative token usage
- [ ] Context window limit enforcement with oldest-turn eviction
- [ ] Log full conversation lineage for forensic reconstruction
- [ ] Configurable max turns per conversation (default: 10)
- [ ] Conversation history stored in memory only — never persisted to disk
- [ ] Session isolation: no conversation data shared between sessions

**Acceptance Criteria:**
- Multi-turn conversations maintain context across 10+ turns
- Context truncation strategy (oldest-first) preserves conversation coherence
- Zero conversation data persists after session end
- Token counting accurate within ±5 tokens per provider
- Conversation export available for audit in structured JSON format

---

## Phase 3: Evaluation Engine

### 9. Blue-Agent Safety Classifier (HH-RLHF / ToxiGen)

**Labels:** `blue-team`, `ml`, `classification`

Implement a safety classifier that evaluates model outputs as safe or harmful:

- [ ] Train/load classifier on HH-RLHF dataset (helpful/harmless conversation pairs)
- [ ] Train/load classifier on ToxiGen dataset (toxic/benign across 13 minority groups)
- [ ] Blue-agent receives only the model response — never the original adversarial prompt (enforced isolation)
- [ ] Implement ensemble scoring combining both classifiers for higher accuracy
- [ ] Classification includes confidence score with calibrated probabilities
- [ ] Response time <500ms per classification
- [ ] ToxiGen subgroup breakdown reported with per-group scores
- [ ] Classifier operates offline (no external API calls for safety evaluation)
- [ ] Model version pinned for reproducibility with hash verification

**Acceptance Criteria:**
- Classifier achieves >85% F1 on HH-RLHF holdout set
- Classifier achieves >80% F1 on ToxiGen holdout set
- Blue-agent prompt isolation verified — test confirms zero prompt leakage
- Classification latency <500ms p95 on CPU inference
- Ensemble improves F1 by >2% over best single classifier
- Model weights loaded from read-only mounted volume with hash verification

---

### 10. Evaluation Scoring System — 50+ Core Metrics

**Labels:** `blue-team`, `evaluation`, `metrics`

Build a comprehensive scoring system for quantitative safety evaluation:

- [ ] Implement 50+ core safety metrics with category breakdown
- [ ] Run evaluations across multiple seeds (configurable, default: 5)
- [ ] Report confidence intervals (95% CI) for all scores
- [ ] Test benign perturbations to detect evaluation instability
- [ ] Categories: toxicity, bias, jailbreak-resistance, prompt-injection, hallucination, refusal-consistency
- [ ] Metric aggregation per category, per domain, per session
- [ ] Score normalization to 0-100 scale for easy comparison
- [ ] Historical score tracking for trend analysis across campaigns
- [ ] CSV/JSON export of full evaluation results

**Acceptance Criteria:**
- 50+ metrics implemented with documented formulas
- Confidence intervals narrow by >20% with 5 seeds vs 1 seed
- Benign perturbation changes score by <2% (stability test)
- Score computation for 1000 evaluations completes in <5s
- Export files parsable by standard data analysis tools (pandas, Excel)

---

## Phase 4: Container Integration + Certificates

### 11. Five-Container Docker Compose Infrastructure

**Labels:** `infrastructure`, `docker`, `networking`

Create the Docker Compose deployment for the full five-container architecture:

- [ ] Define 5 Docker services: red-agent, orchestrator, blue-agent, llm-sandbox, audit
- [ ] Each container sits on its own Docker bridge network with no direct routes between them
- [ ] Orchestrator is the only host present across all networks (blindfolded intermediary)
- [ ] Linux namespaces (pid, net, ipc, uts, mnt) enforced per container
- [ ] Health checks with startup dependencies and restart policies
- [ ] `docker compose up` single-command deploys entire system
- [ ] `.env` file for configuration without editing Compose file
- [ ] Volume mounts for audit storage and shared configurations
- [ ] Resource limits (CPU, memory) defined per service
- [ ] Development and production Compose overrides

**Acceptance Criteria:**
- `docker compose up` starts all 5 containers in <30s
- Network isolation verified: red-agent cannot ping blue-agent
- Orchestrator can reach all 4 other containers
- Health checks pass within 10s of container start
- `docker compose down --volumes` cleans up all resources
- Compose file passes `docker compose config --validate`

---

### 12. Container Security Hardening — Seccomp, gVisor, No-New-Privileges

**Labels:** `security`, `containers`, `hardening`

Harden all containers with defense-in-depth security configurations:

- [ ] Create seccomp profiles per container role whitelisting only necessary syscalls
- [ ] Configure gVisor (runsc) as container runtime for LLM sandbox
- [ ] Enable `no-new-privileges` security option on all containers
- [ ] Set `read_only_root_filesystem: true` for sandbox and audit containers
- [ ] Run as `nobody` user (non-root) in all containers
- [ ] Mount tmpfs for ephemeral storage: `/tmp:size=50m,noexec,nosuid`
- [ ] Drop all capabilities with `cap_drop: [ALL]`, add only required ones
- [ ] Memory limit: 512MB sandbox, 256MB agents, 1GB auditor
- [ ] CPU limit: 1 core sandbox, 0.5 cores agents
- [ ] Kernel hardening: `kernel.printk=0`, `kernel.kptr_restrict=2`

**Acceptance Criteria:**
- Seccomp profile blocks all unnecessary syscalls (verified with audit log)
- gVisor runtime successfully isolates sandbox from host kernel
- `docker inspect` confirms all security options are applied
- Container cannot create new processes (verified with fork bomb test)
- Read-only filesystem confirmed — write attempts fail with `EROFS`
- No capabilities present beyond those explicitly whitelisted

---

### 13. Signed PDF Certificate Generator with Ed25519 Signing

**Labels:** `certificate`, `cryptography`, `compliance`

Generate signed PDF safety certificates as the primary compliance deliverable:

- [ ] Design PDF certificate layout with: model info, test date, session ID, domain breakdown
- [ ] Include: total attacks fired, vulnerabilities found (count/severity/category), adaptive mutation rounds
- [ ] Include: audit chain Merkle root hash for verification
- [ ] Sign certificate with Ed25519 from orchestrator session key
- [ ] Embed verification command in certificate for recipient integrity checking
- [ ] Ed25519 signing key generated per session, destroyed on session end
- [ ] Certificate includes QR code linking to audit chain verification endpoint
- [ ] Partial certificate generation on budget exhaustion or session interrupt
- [ ] Certificate PDF validates with standard PDF/A-2u compliance

**Acceptance Criteria:**
- Certificate generation takes <2s including signing
- Ed25519 signature verifies with `openssl pkeyutl -verify`
- QR code decodes to valid verification URL
- PDF passes veraPDF PDF/A-2u validation
- Partial certificate contains all completed test data
- Verification command in certificate works when copied to terminal

---

## Bayora Import: Core Services (Phases 5-11)

### 14. Dataset Management CLI Tool

**Labels:** `data`, `cli`, `datasets`

Build a unified CLI tool to manage adversarial testing datasets:

- [ ] Auto-download 5 datasets: AdvBench (500+ harmful instructions), JailbreakBench, Gandalf/Lakera, ToxiGen (optional), HH-RLHF (optional)
- [ ] SHA-256 integrity verification for all downloads
- [ ] Dataset caching with LRU eviction and disk quota
- [ ] Validation: schema check, deduplication, format normalization
- [ ] Unified `DatasetManager` class with programmatic API
- [ ] CLI commands: `list`, `download`, `validate`, `inspect`, `stats`, `clear-cache`
- [ ] Progress bars and resumable downloads for large datasets
- [ ] Dataset version tracking with changelog awareness
- [ ] Export to JSONL, CSV, Parquet formats

**Acceptance Criteria:**
- All 3 required datasets download and validate in <5 minutes
- Integrity check catches single-byte corruption in any dataset
- Cache hit serves dataset in <100ms vs 5-minute download
- CLI `centinela datasets stats` shows per-dataset row counts and size
- Resumed download continues from byte offset (not restart)

---

### 15. YAML/JSON Configuration Parser with Schema Validation

**Labels:** `core`, `configuration`, `validation`

Build a declarative configuration system for security policy management:

- [ ] Parse YAML and JSON configuration files with unified internal representation
- [ ] JSON Schema validation with descriptive error messages
- [ ] Resource limit validation: CPU 0.1-32 cores, Memory 128MB-64GB
- [ ] DFS-based circular dependency detection between configuration sections
- [ ] Pretty printer for round-trip configuration serialization (comments preserved)
- [ ] Environment variable substitution with `${VAR}` and `${VAR:default}` syntax
- [ ] Configuration merging: defaults → file → environment → CLI overrides
- [ ] Configuration change events for hot-reload support
- [ ] Schema generation from Python dataclasses/Pydantic models

**Acceptance Criteria:**
- Circular dependency detected with path shown: `section_a → section_b → section_a`
- Environment variable substitution works for all supported formats
- Round-trip: parse → modify → serialize → parse produces identical AST
- Schema validation error includes line number and expected type
- Load 1000-line configuration in <100ms

---

### 16. Secrets Manager — AES-256-GCM with ABAC and mTLS

**Labels:** `security`, `cryptography`, `secrets`

Build a cryptographic secrets management service:

- [ ] AES-256-GCM encryption with PBKDF2 key derivation (100k iterations, SHA-256)
- [ ] Attribute-Based Access Control (ABAC) with policy DSL (JSON/YAML)
- [ ] Mutual TLS authentication with certificate pinning
- [ ] Automatic 24-hour secret rotation with graceful transitions (old key decrypts existing, new key encrypts new)
- [ ] tmpfs secret injection at 0400 permissions — never in environment variables
- [ ] Backend: HashiCorp Vault integration or encrypted SQLite for dev
- [ ] Secret types: API keys, certificates, encryption keys, database credentials
- [ ] Audit logging of all secret access (read, write, rotate, delete)
- [ ] Emergency secret revocation with immediate effect

**Acceptance Criteria:**
- Encryption/decryption of 1KB secret takes <50ms
- ABAC policy evaluation takes <5ms per request
- mTLS handshake completes in <200ms with certificate pinning
- Rotation completes within 2 minutes (grace period overlap)
- tmpfs mount verified: 0400 permissions, owned by root, not in env vars
- Vault integration works with Vault 1.18+ in dev and production modes

---

### 17. Enhanced Audit — Geo-Replication & Ed25519 Batch Signing

**Labels:** `audit`, `replication`, `cryptography`

Extend the base audit system with advanced compliance features:

- [ ] Ed25519 batch signing every 60 seconds (sign Merkle root of batch)
- [ ] Tamper detection with 5-second alert SLA — compare local vs replicated chain heads
- [ ] Geo-replication to 2+ regions within 10 seconds (async, quorum-based)
- [ ] PostgreSQL with row-level security for tenant isolation (or immutable SQLite for dev)
- [ ] Complete audit trail: timestamp, tenant_id, operation_type, result, metadata JSONB
- [ ] Replication lag monitoring with Prometheus metric
- [ ] Split-brain detection and automatic resolution
- [ ] Read-only replica for compliance queries without production load

**Acceptance Criteria:**
- Batch signing of 100K entries takes <5s
- Tamper detection alerts within 5s of chain divergence
- Geo-replication lag <10s p99 across 2 regions
- Row-level security prevents cross-tenant data access
- Read replica query latency <100ms for last-24h queries

---

### 18. Provenance Tracker — Graph-Based Data Lineage

**Labels:** `forensics`, `graph`, `lineage`

Implement forensic data lineage tracking using graph-based storage:

- [ ] Graph-based storage using NetworkX or adjacency list in PostgreSQL
- [ ] Parent-child relationship tracking for derived artifacts (e.g., mutated prompts)
- [ ] Backward tracing: find origin of any artifact given its ID
- [ ] Forward tracing: find all derived artifacts given an origin ID
- [ ] Isolation boundary crossing detection with source/destination logging
- [ ] Graph query API: ancestors, descendants, shortest path, subgraph
- [ ] Visualization export to Graphviz DOT format
- [ ] Provenance records immutable — linked to audit chain entries
- [ ] Garbage collection of orphaned nodes after configurable TTL

**Acceptance Criteria:**
- Backward trace of artifact with 100 ancestors completes in <200ms
- Forward trace returns all descendants (including branching)
- Boundary crossing detection logs source container, destination container, timestamp
- DOT export renders correctly with Graphviz
- GC does not remove nodes still referenced by audit chain entries

---

### 19. Checkpoint — Core Services Validation

**Labels:** `checkpoint`, `testing`, `quality`

Create a validation checkpoint that ensures all core services function correctly:

- [ ] Automated test suite covering all Phase 1-6 services
- [ ] Integration tests for cross-service communication (config → secrets → audit → provenance)
- [ ] Performance benchmarks for each service's critical path
- [ ] Security scan of all service dependencies (pip audit, safety)
- [ ] Documentation verification: all public APIs have docstrings and examples
- [ ] Test report generation in JUnit XML and HTML formats
- [ ] Failed tests block roadmap progression until resolved

**Acceptance Criteria:**
- All core service tests pass with >80% coverage
- Cross-service integration test covers the full pipeline
- No critical/high severity vulnerabilities in dependencies
- Performance benchmarks within 2x of target SLA
- Checkpoint report generated and archived

---

## Bayora Import: Security Services (Phases 12-15)

### 20. Anomaly Detector — Syscall, Network, and ML Detection

**Labels:** `security`, `monitoring`, `ml`

Build real-time security monitoring across multiple detection dimensions:

- [ ] System call monitoring with seccomp/eBPF (log all syscalls, alert on anomalies)
- [ ] Network traffic monitoring: detect exfiltration via DNS tunneling, large uploads (>10 MB/min)
- [ ] Container escape detection: monitor privilege escalation syscalls (CLONE_NEWNS, unshare, etc.)
- [ ] ML-based adversarial prompt detection using AdvBench/JailbreakBench trained models
- [ ] Timing side-channel detection: identify correlation attacks with statistical tests
- [ ] Alert thresholds: >3σ deviation, >10 MB/min traffic, <1s escape termination
- [ ] Prometheus alerting with configurable severity levels
- [ ] Alert deduplication and aggregation to prevent alert fatigue

**Acceptance Criteria:**
- Syscall anomaly detection latency <100ms per event
- DNS tunneling detection catches all standard exfiltration tools (dnscat2, iodine)
- Container escape attempt detected and terminated in <1s
- ML prompt detection achieves >80% recall on holdout set
- Alert aggregation reduces 100 raw events to <5 grouped alerts
- Zero false positives for normal operation traffic patterns

---

### 21. Network Segmentation — WireGuard Tunnels & NetworkPolicies

**Labels:** `network`, `wireguard`, `kubernetes`

Implement WireGuard-based network isolation with Kubernetes NetworkPolicy:

- [ ] WireGuard tunnel setup with keypair generation per tenant
- [ ] Kubernetes NetworkPolicy for inter-tenant traffic blocking (default deny ingress/egress)
- [ ] Egress filtering with endpoint whitelisting (allow only specified external endpoints)
- [ ] DNS tunneling prevention: rate limit DNS queries, block TXT/AAAA exfiltration
- [ ] Network boundary crossing logging with source/destination metadata
- [ ] WireGuard key rotation every 24 hours with zero-downtime transition
- [ ] Network policy audit: periodic scan for overly permissive policies
- [ ] Support for both Docker Compose and Kubernetes network models

**Acceptance Criteria:**
- WireGuard tunnel establishment <1s per tenant
- NetworkPolicy blocks all cross-tenant traffic by default
- Egress whitelist allows only configured endpoints (verified with curl test)
- DNS tunneling test with dnscat2 is detected and blocked
- Network crossing log contains: timestamp, src_ip, dst_ip, protocol, port
- Key rotation does not drop existing connections (graceful transition)

---

### 22. Cgroup v2 Resource Governor — CPU/Memory/I/O Enforcement

**Labels:** `cgroups`, `resource-control`, `performance`

Build cgroup v2 resource controller for per-tenant isolation:

- [ ] CPU quota enforcement with CPU pinning to prevent cache side-channels
- [ ] Separate cgroup hierarchy per tenant with resource limits
- [ ] Memory limit enforcement with OOM killer isolation (OOM kills within tenant cgroup only)
- [ ] I/O bandwidth limits with per-tenant throttling (bps/iops)
- [ ] 50-200ms random timing jitter to prevent timing attacks
- [ ] Prometheus metrics: CPU usage, memory usage, I/O bandwidth, OOM count per tenant
- [ ] Limits dynamically adjustable without container restart
- [ ] Graceful degradation: warn at 80% of limit, throttle at 95%, enforce at 100%
- [ ] Fallback to Docker resource limits when cgroup v2 not available

**Acceptance Criteria:**
- CPU pinning mapped to separate physical cores per tenant
- Memory limit enforced: OOM killer only kills processes within the exceeding tenant's cgroup (verified with stress test)
- I/O throttle keeps tenant within 100/1000 MB/s read/write
- Timing jitter passes uniform distribution test (K-S p > 0.05)
- Prometheus metrics update every 5s with <1% overhead

---

### 23. Container Image Security — Trivy, Cosign, Base Image Whitelist

**Labels:** `security`, `containers`, `supply-chain`

Implement supply chain security for all container images:

- [ ] Trivy integration for CVE scanning: reject builds with critical/high vulnerabilities
- [ ] Cosign integration for image signature verification before deployment
- [ ] Base image whitelist enforcement (only approved base images allowed)
- [ ] Image digest logging for forensic analysis (immutable reference)
- [ ] Private registry authentication for pulling from internal registries
- [ ] Automated daily scan of all deployed images
- [ ] Vulnerability report generation in CycloneDX/SBOM format
- [ ] Policy-as-code for image approval (YAML-based rules engine)
- [ ] Slack/webhook alerting on new critical vulnerabilities in deployed images

**Acceptance Criteria:**
- Build fails if any critical CVE in base image or dependencies
- Cosign verification uses keyless (fulcio/rekor) or key-pair mode
- Base image whitelist: 3 approved images (python-slim, alpine, distroless)
- Image digest changes detected and blocked on mismatch
- Daily scan completes for all 5 containers in <2 minutes

---

### 24. Checkpoint — Security Services Validation

**Labels:** `checkpoint`, `security`, `testing`

Validation checkpoint for all security services (Phases 12-15):

- [ ] Automated test suite for anomaly detector, network segmentation, resource governor, image security
- [ ] Cross-service security integration tests
- [ ] Penetration test against hardened containers
- [ ] Performance benchmarks under security load
- [ ] Verify alert thresholds trigger at correct levels
- [ ] Test report with security findings and remediation timeline

**Acceptance Criteria:**
- All security service tests pass
- Cross-service test validates: anomaly detect → network block → resource limit → image reject
- Penetration test finds no critical/high severity issues
- Performance overhead of security services <5% of baseline

---

## Bayora Import: Orchestrator (Phases 16-20)

### 25. Orchestrator Session Management — Lifecycle & State Machine

**Labels:** `orchestrator`, `session`, `state-machine`

Implement session lifecycle orchestration for the platform core:

- [ ] Session creation with UUID v4 session ID and secret allocation (<5s SLA)
- [ ] State machine: CREATED → RUNNING → COMPLETED / TERMINATED / FAILED
- [ ] Session monitoring with Prometheus metrics (active sessions, state transitions, errors)
- [ ] Session termination with cleanup: archive audit data (<10s), memory scrub (<30s)
- [ ] Automatic timeout enforcement (3600-second max duration, configurable)
- [ ] Concurrent session limit (configurable, default: 10)
- [ ] Session state persistence with crash recovery
- [ ] Webhook notifications on session state transitions

**Acceptance Criteria:**
- Session creation completes in <5s including credential validation
- State transitions are atomic — no inconsistent states possible
- Timeout enforcement within 1s of configured max duration
- Memory scrub verified: zero residual data detectable in process memory
- Crash recovery restores session state within 2s of restart

---

### 26. Orchestrator Kubernetes Pod Manager

**Labels:** `orchestrator`, `kubernetes`, `pods`

Build Kubernetes pod management for dynamic tenant isolation:

- [ ] Pod creation with security context: rootless, seccomp profile, minimal Linux capabilities
- [ ] Namespace isolation per tenant (PID, network, IPC, UTS namespaces)
- [ ] Resource allocation: CPU/memory requests and limits, cgroup v2 controls
- [ ] Network policy application with WireGuard tunnel injection
- [ ] Pod lifecycle management: monitor health, cleanup on session end, graceful termination
- [ ] Pod template configurable via Kubernetes Deployment/StatefulSet
- [ ] Pod startup time SLA <10s from request to Ready
- [ ] Pod resource usage exposed via Prometheus metrics
- [ ] Kubernetes Events integration for pod lifecycle monitoring

**Acceptance Criteria:**
- Pod creation with security context in <10s
- Network policy applied within 2s of pod creation
- Graceful termination completes within 30s (SIGTERM → SIGKILL)
- Pod resource limits match configured values
- Pod startup time meets <10s SLA (p99)
- Zero pods orphaned on orchestrator restart (reconciliation loop)

---

### 27. Orchestrator LLM-Specific Isolation

**Labels:** `orchestrator`, `llm`, `isolation`, `security`

Implement AI-specific security controls:

- [ ] KV cache clearing between sessions (integrate with vLLM/TGI inference endpoints)
- [ ] Prompt artifact isolation: shared memory regions scanned and zeroed between sessions
- [ ] Output sanitization: strip control characters, null bytes, escape sequences
- [ ] Prevent prompt injection in outputs: detect and neutralize injected instructions
- [ ] Model weight isolation: separate copies per Client_LLM using copy-on-write
- [ ] Output sandboxing: detect code execution attempts in LLM outputs (code fences, shell commands)
- [ ] All isolation verified via memory inspection after session end
- [ ] Isolation overhead: <100ms per session transition

**Acceptance Criteria:**
- KV cache flush verified with vLLM API call — no residual tokens
- Memory scan after session end finds no prompt artifacts from previous session
- Output sanitization removes control characters and null bytes
- Prompt injection in output detected and blocked
- COW model weights consume <20% additional memory per additional tenant

---

### 28. Orchestrator FastAPI REST API

**Labels:** `api`, `fastapi`, `rest`

Build the REST API layer for orchestrator interaction:

- [ ] `POST /sessions` — Create session with provider config and budget limits
- [ ] `GET /sessions/{id}` — Get session status, state, and summary metrics
- [ ] `DELETE /sessions/{id}` — Terminate session with cleanup
- [ ] `POST /sessions/{id}/execute` — Execute prompt with <10s response SLA
- [ ] `GET /health` — Kubernetes liveness and readiness probes
- [ ] `GET /metrics` — Prometheus metrics endpoint
- [ ] `GET /sessions` — List sessions with filtering and pagination
- [ ] Authentication: JWT bearer tokens or mutual TLS
- [ ] OpenAPI 3.1 documentation auto-generated with Swagger UI
- [ ] Rate limiting: 100 requests/min per session, 1000 requests/min per tenant

**Acceptance Criteria:**
- All endpoints respond within SLA (<500ms p95 for non-execute, <10s for execute)
- OpenAPI spec validates against OpenAPI 3.1 schema
- JWT authentication rejects unauthenticated requests with 401
- Rate limiting returns 429 with Retry-After header
- Metrics endpoint returns Prometheus-formatted output
- Health endpoint reflects dependency health (DB, LLM providers)

---

### 29. Campaign Management API & State Machine

**Labels:** `orchestrator`, `campaign`, `workflow`

Implement test campaign management for structured testing sequences:

- [ ] Campaign CRUD: create, read, update, delete campaigns
- [ ] Campaign state machine: DRAFT → QUEUED → RUNNING → COMPLETED / CANCELLED / FAILED
- [ ] Test sequencing within campaigns with dependency ordering
- [ ] Async execution via task queue (Celery/Redis) for parallel test execution
- [ ] Correlation ID propagation across all campaign events
- [ ] Result aggregation: per-test scores → per-campaign summary
- [ ] Campaign replay: re-run specific campaign with same configuration
- [ ] Campaign templates for reusable test scenarios
- [ ] Campaign scheduling: run at specific time or on recurring schedule

**Acceptance Criteria:**
- Campaign with 100 tests executes and aggregates results
- Dependency ordering respected: if test B depends on A, A runs first
- Correlation ID traces all 100 tests through the full pipeline
- Campaign replay produces bit-identical results (same seed, same config)
- Scheduled campaign triggers within 5s of scheduled time

---

### 30. Checkpoint — Orchestrator Validation

**Labels:** `checkpoint`, `orchestrator`, `integration`

End-to-end orchestrator validation checkpoint:

- [ ] Integration tests: session creation → execution → termination
- [ ] API contract tests: all endpoints respond with correct schemas
- [ ] State machine transition tests: all valid and invalid transitions
- [ ] Concurrent session tests: 10 sessions running simultaneously
- [ ] Failure recovery tests: orchestrator crash, DB outage, provider timeout
- [ ] Performance benchmarks against all SLAs
- [ ] Test report with coverage metrics

**Acceptance Criteria:**
- Full session lifecycle test passes (create → execute → terminate)
- 10 concurrent sessions execute without race conditions or state corruption
- Orchestrator crash recovery restores all active sessions
- All API responses match OpenAPI schema (validated with schemathesis)
- All SLAs met under concurrent load

---

## Bayora Import: Integration (Phases 21-25)

### 31. Red/Blue Team Full Integration Pipeline

**Labels:** `integration`, `red-team`, `blue-team`

Connect red-team and blue-team into a unified end-to-end pipeline:

- [ ] Red-team executes adversarial prompts against target LLM via orchestrator
- [ ] Rate limiting: 100 prompts/min per session
- [ ] Batch execution: load test set from AdvBench/JailbreakBench/HarmBench
- [ ] Orchestrator strips red-team metadata before forwarding to LLM sandbox
- [ ] Blue-team receives only model response (never the original prompt)
- [ ] Blue-team classifies response as safe/harmful with score
- [ ] Results aggregated per test, per batch, per session
- [ ] A/B testing: multiple blue-team strategies on same red-team output
- [ ] Blue-team training support: labeled datasets for classifier improvement
- [ ] Performance metrics: precision, recall, F1, confusion matrix

**Acceptance Criteria:**
- Full pipeline: red → LLM → blue → result in <15s per prompt
- Rate limiter enforces 100 prompts/min (±1)
- Blue-team prompt isolation verified: zero red-team prompts in blue-team logs
- A/B test compares 2+ strategies with statistical significance
- Confusion matrix generated per batch with precision, recall, F1

---

### 32. Helm Charts for Production Kubernetes Deployment

**Labels:** `kubernetes`, `helm`, `deployment`

Create production-ready Helm charts for Kubernetes deployment:

- [ ] Helm chart for orchestrator (StatefulSet with persistent storage)
- [ ] Helm chart for tenant pods (Deployment with sidecar injection)
- [ ] RBAC policies: ServiceAccounts, Roles, RoleBindings (least privilege)
- [ ] ConfigMaps and Secrets for configuration management
- [ ] Ingress configuration with TLS termination
- [ ] PodDisruptionBudget for high availability
- [ ] Horizontal Pod Autoscaler based on session count
- [ ] NetworkPolicies for inter-service isolation
- [ ] Chart linting and testing with helm unittest
- [ ] Deployment validation with kind cluster and helm --dry-run

**Acceptance Criteria:**
- `helm install` deploys all components in <60s
- RBAC policies grant minimum required permissions (verified with audit)
- HPA scales pods based on session queue depth
- NetworkPolicies tested with kubectl network-policy-verifier
- Kind cluster deployment passes all E2E tests
- `helm lint` passes with zero warnings

---

### 33. Terraform IaC Modules — AWS EKS, GCP GKE, Azure AKS

**Labels:** `terraform`, `infrastructure`, `cloud`

Write Terraform modules for deploying CENTINELA on major cloud providers:

- [ ] AWS EKS module: VPC, private subnets, node groups, IAM roles, ECR, EKS cluster
- [ ] GCP GKE module: VPC, private cluster, node pools, IAM, Artifact Registry
- [ ] Azure AKS module: VNet, private cluster, node pools, RBAC, ACR
- [ ] Common: audit database (RDS/CloudSQL/Azure SQL), Redis, object storage
- [ ] Outputs: kubeconfig, endpoint URLs, resource IDs
- [ ] Remote state management with encrypted backend
- [ ] Terraform validation with `terraform validate` and `terraform plan`
- [ ] Cost estimation output for each provider
- [ ] Multi-region support for audit geo-replication

**Acceptance Criteria:**
- `terraform plan` succeeds for all 3 providers
- AWS EKS cluster deploys in <20 minutes with `terraform apply`
- GCP GKE cluster deploys in <15 minutes
- Azure AKS cluster deploys in <15 minutes
- Cost estimation within ±10% of actual cloud pricing
- Destroy cleans up all resources (verified with resource scan)

---

### 34. Threat Model (STRIDE) & CVSS Risk Scoring

**Labels:** `security`, `documentation`, `compliance`

Document the complete threat model with risk scoring:

- [ ] STRIDE threat model covering all 5 containers and their interactions
- [ ] CVSS v3.1 risk scoring for all identified threats
- [ ] Mitigation documentation for threats with risk score >4.0
- [ ] Residual risk documentation — honest assessment of known gaps
- [ ] Security runbook: incident response procedures, escalation paths
- [ ] Threat model diagram (data flow diagram with trust boundaries)
- [ ] Per-container threat surface analysis
- [ ] Compliance framework mapping (HIPAA, SOX, GDPR, EU AI Act)
- [ ] Regular review cadence: quarterly threat model updates

**Acceptance Criteria:**
- 20+ threats identified with STRIDE categories
- CVSS scores calculated using official CVSS v3.1 calculator
- All >4.0 score threats have documented mitigation
- Residual risks acknowledged with acceptance rationale
- Security runbook includes runbooks for top 5 incident types

---

### 35. E2E Integration Tests & Performance Benchmarks

**Labels:** `testing`, `integration`, `performance`

Comprehensive end-to-end validation of the entire platform:

- **Test Scenarios:**
  - Red Team attacks Client LLM → Blue Team blocks attack
  - Blue Team deploys classifier and successfully blocks adversarial prompts
  - Multi-tenant isolation: parallel sessions don't leak data
  - Complete session lifecycle: create → execute → terminate → verify audit

- **Performance Benchmarks:**
  - Session creation: <5s
  - Prompt execution: <10s
  - Session termination: <30s
  - Audit log replication: <10s

- **Security Validation:**
  - Inter-tenant isolation: tenant A cannot access tenant B's data
  - Container escape prevention: escape attempts are blocked and logged
  - Network segmentation: cross-container network isolation verified
  - Audit tamper-evidence: tampering detected and alerted within SLA

- **Coverage:**
  - Target >80% code coverage across all modules
  - All acceptance criteria from previous phases tested
  - CI pipeline enforces coverage gate

**Acceptance Criteria:**
- All E2E test scenarios pass
- Performance benchmarks meet all SLAs
- Security validation tests pass with zero critical findings
- Code coverage >= 80%
- Test suite runs in <10 minutes
- CI pipeline blocks PRs that reduce coverage

---

### 36. Production Readiness Final Checkpoint

**Labels:** `checkpoint`, `production`, `release`

Final validation before production deployment:

- [ ] All previous checkpoints pass (Core Services, Security Services, Orchestrator)
- [ ] Security audit: penetration test, dependency scan, secrets scan
- [ ] Performance load test: 2x expected peak load for 1 hour
- [ ] Disaster recovery test: full restore from backup
- [ ] Documentation review: API docs, deployment guide, runbook
- [ ] Compliance review: HIPAA/SOX/GDPR/EU AI Act mapping complete
- [ ] Monitoring and alerting verified for all components
- [ ] Release checklist signed off
- [ ] Rollback plan documented and tested

**Acceptance Criteria:**
- All checkpoints pass with zero failures
- Load test at 2x peak shows no degradation
- Full restore from backup in <30 minutes
- Documentation covers all operational procedures
- Release candidate tagged and artifacts published

---

## Summary

| Category | Task Count |
|----------|-----------|
| Phase 1: Foundation | 5 |
| Phase 2: Red-Teaming Engine | 3 |
| Phase 3: Evaluation Engine | 2 |
| Phase 4: Container Integration + Certificates | 3 |
| Bayora Core Services (Phases 5-11) | 6 |
| Bayora Security Services (Phases 12-15) | 5 |
| Bayora Orchestrator (Phases 16-20) | 6 |
| Bayora Integration (Phases 21-25) | 6 |
| **Total** | **36** |
