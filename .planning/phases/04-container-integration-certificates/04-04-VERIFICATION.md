---
phase: 04-container-integration-certificates
verified: 2026-05-17T12:30:00Z
status: gaps_found
score: 5/7 must-haves verified
gaps:
  - truth: "LLM sandbox uses gVisor runtime with seccomp profiles and cgroup v2 hard limits"
    status: failed
    reason: "runtime: runsc is not configured in docker-compose.yml - only a comment exists noting it requires gVisor installation"
    artifacts:
      - path: "docker-compose.yml"
        issue: "llm-sandbox service missing 'runtime: runsc' configuration"
    missing:
      - "Add 'runtime: runsc' to llm-sandbox service in docker-compose.yml"
      - "Ensure gVisor installation documented for users"
  - truth: "Recipient can verify certificate integrity using the included verification command"
    status: failed
    reason: "verify_cert.py is a stub that only prints 'SIGNATURE_VERIFIED' without actually performing Ed25519 signature verification"
    artifacts:
      - path: "services/orchestrator/src/orchestrator/verify_cert.py"
        issue: "verify_certificate() always returns True without validating signature against certificate data"
    missing:
      - "Implement actual Ed25519 signature verification using public key and signature from certificate"
      - "Extract certificate data (model_info, session_id, vuln_count, merkle_root) from PDF or sidecar JSON"
      - "Reconstruct payload and verify Ed25519 signature"
      - "Return verification result based on actual cryptographic check"
---

# Phase 4: Container Integration & Certificates Verification Report

**Phase Goal:** Users can deploy the complete five-container architecture with forensically auditable signed certificates
**Verified:** 2026-05-17T12:30:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth   | Status     | Evidence       |
| --- | ------- | ---------- | -------------- |
| 1   | User can deploy entire system with single docker compose up command | ✓ VERIFIED | docker-compose.yml defines all 5 services with valid build contexts |
| 2   | System runs as five isolated containers on separate Docker bridge networks | ✓ VERIFIED | 5 networks (red-net, orchestrator-red, orchestrator-blue, sandbox-net, audit-net) and 5 services properly assigned |
| 3   | LLM sandbox uses gVisor runtime with seccomp profiles and cgroup v2 hard limits | ✗ FAILED | runtime: runsc NOT in docker-compose.yml - only comment exists |
| 4   | Audit chain verification confirms cryptographic integrity across all logged events | ✓ VERIFIED | chain.py implements SHA-256 hash chain + Merkle tree with verify_chain() |
| 5   | User receives signed PDF safety certificate after session completes | ✓ VERIFIED | certificate.py implements full PDF generation with Ed25519 signing |
| 6   | Certificate includes model info, test date, session ID, vuln count, mutation rounds, Merkle root | ✓ VERIFIED | All fields present in certificate.py generate_pdf() |
| 7   | Recipient can verify certificate integrity using the included verification command | ✗ FAILED | verify_cert.py is stub - prints "SIGNATURE_VERIFIED" without actual verification |

**Score:** 5/7 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `docker-compose.yml` | 5-container deployment with networks | ✓ VERIFIED | 5 services, 5 networks defined |
| `configs/seccomp/*.json` | Seccomp profiles | ✓ VERIFIED | 5 profiles exist (red-agent, blue-agent, llm-sandbox, audit, orchestrator) |
| `configs/gVisor/runsc.conf` | gVisor configuration | ✓ VERIFIED | Configuration file exists |
| `services/audit/src/audit/chain.py` | Hash chain + Merkle tree | ✓ VERIFIED | Full implementation with verify_chain(), get_merkle_root() |
| `services/orchestrator/src/orchestrator/audit_client.py` | Audit client | ✓ VERIFIED | Has get_merkle_root() method |
| `services/orchestrator/src/orchestrator/certificate.py` | PDF generation + signing | ✓ VERIFIED | Full implementation with Ed25519 |
| `services/orchestrator/src/orchestrator/verify_cert.py` | Certificate verification CLI | ✗ STUB | Stub - doesn't actually verify signatures |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| certificate.py | audit_client.py | get_merkle_root() call | ✓ WIRED | Line 175: merkle_root = audit_client.get_merkle_root(session_id) |
| docker-compose.yml | seccomp profiles | security_opt | ✓ WIRED | All services reference /configs/seccomp/*.json |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
|------------|--------|----------------|
| Single docker compose up command | SATISFIED | - |
| Five isolated containers | SATISFIED | - |
| gVisor runtime for LLM sandbox | BLOCKED | runtime: runsc not configured |
| Audit chain verification | SATISFIED | - |
| Signed PDF certificate | SATISFIED | - |
| Verification command works | BLOCKED | verify_cert.py is stub |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| verify_cert.py | 37-45 | Mock verification - always returns True | Blocker | Certificate integrity cannot be verified |

### Human Verification Required

None - all gaps are code-level issues that can be verified programmatically.

### Gaps Summary

Two critical gaps prevent full goal achievement:

1. **gVisor runtime not configured**: The llm-sandbox service in docker-compose.yml does not have `runtime: runsc` set. It only has a comment noting that gVisor needs to be installed on the host. This means the LLM sandbox runs with standard Docker runtime (runc) instead of the gVisor sandbox required by the security architecture.

2. **Certificate verification is non-functional**: The verify_cert.py CLI accepts --cert and --pubkey arguments but performs no actual signature verification. It simply prints "Certificate verification: SIGNATURE_VERIFIED" and returns True, regardless of whether the certificate is valid or tampered with. This fails the requirement that "Recipient can verify certificate integrity using the included verification command."

---

_Verified: 2026-05-17T12:30:00Z_
_Verifier: Claude (gsd-verifier)_