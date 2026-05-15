# Feature Research

**Domain:** AI Safety Testing & Validation Platform
**Researched:** 2026-05-14
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Automated Red-Teaming** | Core to any AI safety platform; users expect vulnerability discovery | HIGH | Baseline expectation across all competitors (EvalGuard 249 attacks, Giskard 50+ probes, VirtueRed 600+ vectors). No platform is taken seriously without it. |
| **Prompt Injection Detection** | OWASP LLM Top 10 #1 risk; regulatory requirement for AI security | HIGH | Universal feature. Every competitor advertises this. Missing = immediate disqualification. |
| **Compliance Framework Mapping** | Auditors, regulators, enterprise buyers require OWASP/NIST/EU AI Act alignment | MEDIUM | EvalGuard maps to 33 frameworks, Validaitor covers EU AI Act + ISO, Prufer maps to SOC 2/ISO 42001. Expected baseline for enterprise sales. |
| **Multi-Provider Support** | Enterprise AI deployments span OpenAI, Anthropic, Azure, custom endpoints | MEDIUM | EvalGuard supports 87 providers. VirtueRed, HiddenLayer, Confident AI all offer multi-provider. Required for enterprise relevance. |
| **Evaluation/Scoring Metrics** | Quantitative assessment of AI safety outputs | MEDIUM | EvalGuard has 166 scorers, Giskard measures hallucinations/omissions/prompt injection. Users expect measurable results. |
| **Audit Trail/Logging** | Compliance evidence, regulatory requirements, incident investigation | HIGH | TraceGov, FireTail, Integritas emphasize audit trails. EU AI Act requires documentation. Expected for regulated industries. |
| **CI/CD Integration** | Security testing must fit into deployment pipelines | LOW | DeepTeam, Splx AI, HiddenLayer all offer CI/CD integration. Dev teams expect this. |
| **Vulnerability Reporting** | Actionable findings with remediation guidance | MEDIUM | All platforms produce reports. Competitors like Adversa AI emphasize "remediation playbooks." Users expect clear outputs. |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Forensically Auditable Certificates** | Third-party validation with cryptographic proof; tangible deliverable for compliance | MEDIUM | Signed PDF certificates with cryptographic attestation. Unique among competitors - most only produce digital reports. Creates trust for audit stakeholders. |
| **Merkle-Chained Audit Log with Ed25519 Signing** | Tamper-evident, cryptographically verifiable history; stronger than standard logging | HIGH | Unique differentiator. Competitors use standard logging (TraceGov SHA-256, FireTail centralized logs). CENTINELA's cryptographic verification exceeds typical audit requirements. |
| **Five Isolated Docker Containers** | Network isolation prevents attack leakage; sandboxed execution | HIGH | Rare in competitors - most run in same environment. Critical for high-security environments (defense, healthcare). Creates trust for sensitive deployments. |
| **Adaptive Red-Teaming with Prompt Mutation** | Evolving attacks find novel vulnerabilities; not static test libraries | HIGH | Noma Security advertises "intelligent agent" that adapts. EvalGuard uses UCB1 bandit optimization. Competitors are moving toward adaptive. CENTINELA's prompt mutation is strong differentiation. |
| **Domain-Specific Attack Profiles** | Targeted testing for Healthcare, Finance, Legal | MEDIUM | EvalGuard has 9 industry-specific packs. Most platforms offer generic attacks. Domain expertise is valued by regulated industries. |
| **Side-Channel Mitigations** | Timing jitter, KV cache flush, cgroup limits prevent inference attacks | HIGH | Uncommon in competitors. Addresses emerging threat vectors (timing attacks, cache-based exfiltration). Positions as "security-first" platform. |
| **Budget Guard** | Cost control for enterprise red-teaming runs | LOW | Rarely offered by competitors. Valuable for enterprises managing AI spend. |
| **Universal Provider Adapter** | OpenAI, Anthropic, Ollama, custom endpoints in one platform | MEDIUM | EvalGuard has 87 providers, but custom endpoint adapters are less common. Ollama support valuable for on-prem deployments. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Real-Time Continuous Monitoring** | "We need 24/7 protection" | Creates alert fatigue, high infrastructure cost, false positives. Red-teaming is typically periodic, not continuous. | Scheduled campaign-based testing with clear thresholds |
| **Human-Led Red Teaming as Default** | "Automated isn't enough" | Scalability issues, cost ($15K-50K per engagement), slow. HackerOne offers this but at premium. | Use automated for scale, human for edge cases |
| **Model Training/Fine-Tuning Security** | "Secure the entire ML lifecycle" | Beyond scope for validation platform. Protect AI, HiddenLayer address this. CENTINELA should stay focused on testing. | Partner with lifecycle security tools |
| **Runtime Guardrails as Primary Feature** | "Block attacks in production" | Distracts from core value (testing/validation). Lakera, Calypso specialize here. | Focus on testing, not defense |
| **Full LLM Access for Testing** | "We need to test the model directly" | Security risk, privacy concerns. HiddenLayer advertises "non-invasive" approach as differentiator. | Test via API/endpoint, not direct model access |
| **Multi-Modal Testing (Image/Video/Audio)** | "Test all modalities" | High complexity, niche demand. VirtueRed mentions this but most platforms focus on text. | Defer to v2, focus on text first |
| **Custom Attack Development Platform** | "Build your own attacks" | Most users want turnkey solutions. DeepTeam offers programmatic access but most prefer UI-driven. | Provide pre-built profiles, offer customization later |

## Feature Dependencies

```
[Multi-Provider Support]
    └──requires──> [Universal Provider Adapter]

[Adaptive Red-Teaming]
    └──requires──> [Domain-Specific Attack Profiles]

[Merkle-Chained Audit Log]
    └──requires──> [Audit Trail/Logging]

[Forensically Auditable Certificates]
    └──requires──> [Merkle-Chained Audit Log]
    └──requires──> [Evaluation/Scoring Metrics]

[Side-Channel Mitigations]
    └──requires──> [Five Isolated Docker Containers]

[Budget Guard]
    └──requires──> [Multi-Provider Support]
```

### Dependency Notes

- **Multi-Provider Support requires Universal Provider Adapter:** Testing across providers requires standardized adapter layer.
- **Adaptive Red-Teaming requires Domain-Specific Profiles:** Mutation strategies should align with domain attack patterns.
- **Merkle-Chain requires Audit Trail:** Cryptographic verification builds on logging infrastructure.
- **Certificates require Merkle-Chain + Scoring:** Certificate generation needs verifiable metrics + tamper-proof history.
- **Side-Channel Mitigations require Isolation:** Container isolation enables timing/cache controls.
- **Budget Guard requires Multi-Provider:** Cost tracking across different LLM endpoints.

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [x] **Multi-Provider Support (OpenAI, Anthropic, Ollama)** — Core requirement for platform relevance
- [x] **Automated Red-Teaming with Basic Attack Library** — Table stakes, no platform survives without it
- [x] **Prompt Injection Detection** — OWASP #1, expected baseline
- [x] **Basic Audit Trail** — Compliance evidence minimum
- [x] **Evaluation/Scoring Metrics** — Quantitative results for stakeholders

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] **Adaptive Red-Teaming with Prompt Mutation** — Differentiator, add after core works
- [ ] **Domain-Specific Attack Profiles (Healthcare, Finance, Legal)** — Targeted for regulated industries
- [ ] **Signed PDF Safety Certificates** — Tangible deliverable for compliance teams
- [ ] **Merkle-Chained Audit Log with Ed25519** — Strengthen audit credibility
- [ ] **Budget Guard** — Cost control feature for enterprise

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] **Side-Channel Mitigations (timing jitter, KV cache flush)** — Advanced security, niche market
- [ ] **Five Isolated Docker Containers** — Infrastructure heavy, deploy after验证
- [ ] **Custom Endpoint Adapter Framework** — Developer feature, secondary to core value
- [ ] **Multi-Modal Testing** — Beyond current scope, high complexity

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Multi-Provider Support | HIGH | MEDIUM | P1 |
| Automated Red-Teaming | HIGH | HIGH | P1 |
| Prompt Injection Detection | HIGH | HIGH | P1 |
| Compliance Framework Mapping | HIGH | MEDIUM | P1 |
| Basic Audit Trail | HIGH | MEDIUM | P1 |
| Evaluation/Scoring | HIGH | MEDIUM | P1 |
| Domain-Specific Profiles | MEDIUM | MEDIUM | P2 |
| Adaptive Red-Teaming | HIGH | HIGH | P2 |
| PDF Certificates | MEDIUM | MEDIUM | P2 |
| Budget Guard | LOW | LOW | P2 |
| Merkle-Chained Audit | MEDIUM | HIGH | P2 |
| Side-Channel Mitigations | MEDIUM | HIGH | P3 |
| Container Isolation | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | EvalGuard | Giskard | HiddenLayer | VirtueRed | CENTINELA (Our Approach) |
|---------|-----------|---------|-------------|-----------|--------------------------|
| Attack Vectors | 249 | 50+ | 100+ | 600+ | Start with core 50-100 |
| Evaluation Scorers | 166 | Yes | Yes | 1000+ | Start with 50 core metrics |
| Provider Support | 87 | Limited | Limited | Limited | 3+ (OAI, Anthropic, Ollama) |
| Compliance Mapping | 33 frameworks | OWASP/NIST | OWASP/NIST/EU AI | OWASP/NIST/MITRE | OWASP/NIST (expand later) |
| Adaptive Red-Teaming | UCB1 bandit | Yes | Yes | Yes | Prompt mutation engine |
| Domain-Specific Packs | 9 industries | Limited | Limited | Yes | Healthcare/Finance/Legal/General |
| Audit Trail | Yes | Yes | Yes | Yes | Merkle-chain + Ed25519 |
| Certificates | No | No | No | Yes | Signed PDF + cryptographic |
| Container Isolation | No | No | No | No | Five isolated containers |
| Side-Channel Mitigations | No | No | No | No | Timing/cache/cgroup limits |
| Budget Guard | Yes (cost tracking) | No | No | No | Budget guard feature |

### Analysis Summary

CENTINELA's differentiation strategy:
1. **Cryptographic Verification** — Merkle-chain + Ed25519 exceeds standard audit trails
2. **Isolation Architecture** — Unique container-based isolation addresses high-security requirements
3. **Tangible Deliverables** — PDF certificates unlike competitors' digital-only reports
4. **Side-Channel Focus** — Addresses emerging threat class most competitors ignore
5. **Budget Control** — Cost feature competitors only partially offer

## Sources

- **Competitor Analysis:** EvalGuard, Giskard, HiddenLayer, VirtueRed, Noma Security, Adversa AI, Confident AI, Validaitor, Prufer, TraceGov
- **Framework Standards:** OWASP LLM Top 10 (2025), NIST AI RMF, MITRE ATLAS, EU AI Act, ISO 42001
- **Industry Research:** Giskard "Best 7 AI Red Teaming Tools 2025", AI Compare "AI Security Platforms 2026", HiddenLayer "AI Threat Landscape Report 2025", redteams.ai vendor evaluation framework
- **Compliance Requirements:** EU AI Act enforcement (August 2026), SOC 2 requirements, GDPR Article 22

---
*Feature research for: AI Safety Testing Platform*
*Researched: 2026-05-14*
