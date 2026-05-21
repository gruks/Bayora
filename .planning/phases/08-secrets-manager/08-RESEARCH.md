# Phase 8 Research: Secrets Manager

## Current State Analysis

During Phase 5, the foundation for the secrets module was laid out in `packages/centinela-core/src/centinela/secrets/manager.py`. The following components are already implemented:
- `generate_salt()`, `derive_key()` using PBKDF2-HMAC-SHA256
- `SecretManager` class handling AES-256-GCM encryption/decryption
- `SecretRef` model (with `name`, `path`, `encryption_key_id`)
- `SecretStore` Abstract Base Class with `get_secret`, `set_secret`, `delete_secret`, and `list_secrets`.

## Gap Analysis against Phase 8 Goal

The Phase 8 goal in `ROADMAP.md` is:
> **Goal:** Cryptographic key and credential management — AES-256-GCM encryption, PBKDF2 key derivation, ABAC policy DSL, mutual TLS, automatic 24-hour rotation, tmpfs secret injection, HashiCorp Vault or encrypted SQLite backend

### What is missing:
1. **Encrypted SQLite / HashiCorp Vault Backend**: We need concrete implementations of `SecretStore`.
2. **tmpfs Secret Injection**: A mechanism to securely mount and inject secrets into containers using tmpfs (so secrets never touch disk).
3. **ABAC Policy DSL**: Attribute-Based Access Control to dictate which container/tenant can access which secret.
4. **Automatic 24-hour rotation**: A service or background task to automatically rotate the master key and re-encrypt secrets.
5. **mutual TLS (mTLS)**: Infrastructure to secure communication between the orchestrator and agents using mTLS.

## Technical Approach

### 1. Storage Backends
We will implement two backends:
- `SQLiteSecretStore`: Uses SQLite with `sqlcipher` or encrypts payloads at the app level before inserting into standard SQLite. Since we already have `SecretManager`, app-level encryption before DB insertion is preferred and reduces native dependencies.
- `VaultSecretStore`: Uses `hvac` Python library to interact with HashiCorp Vault.

### 2. tmpfs Injection
Implement a `SecretInjector` that takes a `SecretRef`, retrieves the decrypted payload from the store, and writes it to a tmpfs mount path (e.g., `/dev/shm/secrets/<secret_id>`), setting strict permissions (`0400`).

### 3. ABAC Policy DSL
Extend the declarative YAML configuration from Phase 7 to include secrets access policies. We will define an `ABACEngine` that evaluates rules based on attributes: `tenant_id`, `container_role`, `environment`.

### 4. Key Rotation & mTLS
- **Rotation**: A background scheduler using `asyncio` or an orchestrator cron job that calls `rotate_key()` and rewrites all stored secrets.
- **mTLS**: Generate X.509 certificates for the Orchestrator, Red-Agent, and Blue-Agent. Configure FastAPI to require client certificates.

## Execution Breakdown

We will split this phase into 4 plans:
- `08-01-PLAN.md` - Storage Backends (SQLite & Vault)
- `08-02-PLAN.md` - tmpfs Secret Injection Service
- `08-03-PLAN.md` - ABAC Policy DSL
- `08-04-PLAN.md` - Key Rotation & mTLS Setup
