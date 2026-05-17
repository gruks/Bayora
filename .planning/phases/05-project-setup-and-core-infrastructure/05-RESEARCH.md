# Phase 5: Project Setup and Core Infrastructure - Research

**Researched:** 2026-05-17
**Domain:** Python package structure, Kubernetes/Docker integration, testing infrastructure
**Confidence:** HIGH

## Summary

This phase establishes the foundational Python package structure for the CENTINELA platform with 8 core modules: orchestrator, config, secrets, audit, provenance, anomaly, network, and resources. The dependencies include official Kubernetes Python client (v35.0), Docker SDK (v7.1), FastAPI (0.115+), cryptography, SQLAlchemy (async), Prometheus client, and WireGuard integration. Testing infrastructure requires pytest with coverage, pytest-docker for container integration tests, and Kubernetes mock libraries (mockernetes or kmock) for unit testing K8s interactions.

**Primary recommendation:** Use the official `kubernetes` Python client (v35.0), `docker` SDK (v7.1), `pytest-docker` for integration testing, `mockernetes` for K8s unit testing, `prometheus-client` for metrics, and WireGuard config parsing via `wgconfig` or `wireguard-tools`.

## Standard Stack

### Core Dependencies

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **kubernetes** | 35.0 | K8s API client | Official Python client (7.5k stars), supports K8s 1.35, active development |
| **docker** | 7.1 | Docker Engine API | Official Docker SDK (7.2k stars), supports API v1.44 |
| **aiodocker** | 0.26 | Async Docker client | aio-libs project, asyncio-native Docker operations |
| **fastapi** | 0.115+ | Web framework | Native async, Pydantic integration, auto OpenAPI |
| **cryptography** | 43.0+ | Cryptographic primitives | Rust-based, active maintenance, secure defaults |
| **sqlalchemy[asyncio]** | 2.0+ | ORM + async | AsyncSession, selectinload for relationships |
| **prometheus-client** | 0.25 | Metrics export | Official Prometheus Python client |
| **pytest** | 9.0+ | Testing framework | Industry standard, extensive plugin ecosystem |

### WireGuard Integration

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **wgconfig** | 1.2+ | Config file parsing | INI-style config parsing, comment preservation |
| **wireguard-tools** | 0.6+ | Pure Python wg CLI | Key generation, config management |
| **wireguard-py** | 2023.6 | Cython kernel access | Direct Netlink API access (requires root) |

### Testing Infrastructure

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **pytest** | 9.0+ | Core test framework | All tests |
| **pytest-cov** | 7.0+ | Coverage reporting | Code coverage tracking |
| **pytest-xdist** | 3.8+ | Parallel execution | Fast test runs |
| **pytest-docker** | 3.2+ | Docker Compose integration | Integration tests with containers |
| **pytest-asyncio** | 0.24+ | Async test support | Testing async code |
| **mockernetes** | 0.2+ | K8s API mocking | Unit tests for K8s client code |
| **kmock** | 0.7+ | K8s mock server | More complex K8s scenarios |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **httpx** | 0.28+ | Async HTTP client | LLM provider calls |
| **structlog** | 24.4+ | Structured logging | JSON audit logs |
| **python-dotenv** | 1.0+ | Environment variables | Local dev secrets |
| **uv** | 0.5+ | Package manager | Fast dependency resolution |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| kubernetes | lightkube, kr8s | Alternative K8s clients, lighter but less maintained |
| docker | aiodocker | Sync vs async, use aiodocker for async-first code |
| mockernetes | kmock, fake_k8s_client | mockernetes is moto-like (easier API), kmock is more feature-rich |
| wgconfig | wireguard-tools | wgconfig is simpler for config parsing |
| prometheus-client | opentelemetry | OTEL is more complex but vendor-neutral |

## Architecture Patterns

### Recommended Package Structure

```
centinela/
├── pyproject.toml           # Workspace root
├── packages/
│   └── centinela-core/     # Shared types (EXISTING)
│       └── src/centinela/
│           ├── __init__.py
│           ├── models/     # Pydantic models (EXISTING)
│           ├── core/       # Core utilities (EXISTING)
│           └── # NEW in Phase 5:
│           ├── config/    # Config parsing & validation
│           ├── secrets/   # Cryptographic secrets management
│           ├── audit/     # Audit log infrastructure
│           ├── provenance/# Data lineage tracking
│           ├── anomaly/   # Anomaly detection
│           ├── network/   # WireGuard/segmentation
│           └── resources/ # cgroup/resource governance
└── services/               # Service packages
    ├── orchestrator/      # Main orchestration service
    ├── audit/             # Audit log service
    ├── red-agent/         # Red teaming
    ├── blue-agent/        # Evaluation
    └── llm-sandbox/       # LLM isolation
```

### Core Module Design Patterns

#### 1. Config Module
**Pattern:** Pydantic-based declarative config with env var substitution
```python
# Source: FastAPI + Pydantic best practices
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import os

class ResourceLimits(BaseModel):
    cpu_cores: float = Field(ge=0.1, le=32)
    memory_mb: int = Field(ge=128, le=65536)
    timeout_seconds: int = Field(gt=0, le=3600)

class SecurityConfig(BaseModel):
    enable_network_isolation: bool = True
    wireguard_enabled: bool = False
    gvisor_enabled: bool = True

class PlatformConfig(BaseModel):
    resources: ResourceLimits
    security: SecurityConfig
    
    @field_validator('*', mode='before')
    @classmethod
    def env_var_substitution(cls, v):
        # Expand ${VAR} and ${VAR:-default} patterns
        if isinstance(v, str):
            return os.path.expandvars(v)
        return v
```

#### 2. Secrets Module
**Pattern:** AES-256-GCM encryption with PBKDF2 key derivation
```python
# Source: cryptography library documentation
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import os

class SecretManager:
    def __init__(self, master_key: bytes):
        self._aesgcm = AESGCM(master_key)
    
    def encrypt(self, plaintext: bytes) -> tuple[bytes, bytes]:
        """Returns (ciphertext, nonce)."""
        nonce = os.urandom(12)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext, None)
        return ciphertext, nonce
    
    def decrypt(self, ciphertext: bytes, nonce: bytes) -> bytes:
        return self._aesgcm.decrypt(nonce, ciphertext, None)

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600000)
    return kdf.derive(password.encode())
```

#### 3. Audit Module (Merkle Chain)
**Pattern:** SHA-256 hash chaining with append-only storage
```python
import hashlib
from datetime import datetime
from pydantic import BaseModel

class AuditEntry(BaseModel):
    entry_id: str
    timestamp: datetime
    event_type: str
    payload: dict
    prev_hash: str | None
    
    @property
    def payload_hash(self) -> str:
        return hashlib.sha256(self.payload.__repr__().encode()).hexdigest()
    
    @property
    def entry_hash(self) -> str:
        content = f"{self.entry_id}{self.timestamp.isoformat()}{self.event_type}{self.payload_hash}{self.prev_hash or ''}"
        return hashlib.sha256(content.encode()).hexdigest()

class AuditLog:
    def __init__(self):
        self._entries: list[AuditEntry] = []
    
    def append(self, event_type: str, payload: dict) -> AuditEntry:
        prev_hash = self._entries[-1].entry_hash if self._entries else None
        entry = AuditEntry(
            entry_id=uuid4().hex[:16],
            timestamp=datetime.now(),
            event_type=event_type,
            payload=payload,
            prev_hash=prev_hash
        )
        self._entries.append(entry)
        return entry
```

#### 4. Kubernetes Integration
**Pattern:** Use official kubernetes client with async wrapper
```python
# Source: kubernetes-python official examples
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import asyncio

class K8sClient:
    def __init__(self, config_file: str | None = None):
        if config_file:
            config.load_kube_config(config_file=config_file)
        else:
            config.load_incluster_config()
        self._core = client.CoreV1Api()
        self._apps = client.AppsV1Api()
    
    async def create_pod(self, namespace: str, pod_spec: dict) -> dict:
        # Run sync operations in executor for async compatibility
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self._core.create_namespaced_pod(namespace, pod_spec)
        )
    
    async def list_pods(self, namespace: str) -> list[dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._core.list_namespaced_pod(namespace)
        )
```

#### 5. Docker Integration
**Pattern:** Use docker SDK with health checks
```python
import docker
from typing import Generator

class DockerManager:
    def __init__(self):
        self._client = docker.from_env()
    
    def run_container(self, image: str, command: str, detach: bool = False) -> Container:
        return self._client.containers.run(image, command, detach=detach)
    
    def get_container(self, container_id: str) -> Container:
        return self._client.containers.get(container_id)
    
    def list_containers(self, all: bool = False) -> list[Container]:
        return self._client.containers.list(all=all)
    
    async def wait_for_healthy(self, container_id: str, timeout: int = 30) -> bool:
        """Wait for container to become healthy."""
        # Implementation with health check polling
        pass
```

### Anti-Patterns to Avoid

- **Async with sync Kubernetes client without executor:** Blocking calls will block event loop
- **Using docker-compose V1 (docker-compose):** Deprecated July 2023, use `docker compose` (V2)
- **Global Celery visibility timeout < ETA:** Causes task redelivery loops for long-running tasks
- **SQLAlchemy sync with async engine:** MissingGreenlet errors when lazy loading in async context
- **Pickle serialization in Celery:** Security risk, use JSON serialization
- **Using `psycopg` (sync) with `create_async_engine`:** Use `asyncpg` driver instead

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Kubernetes API client | Custom HTTP wrapper | `kubernetes` (official) | Handles auth, retries, API versioning |
| Docker container management | subprocess docker CLI | `docker` SDK | Type-safe, streaming, proper cleanup |
| WireGuard key management | Custom crypto | `wireguard-tools` for keys, `wgconfig` for configs | Properly implements WireGuard spec |
| K8s mocking for tests | Manual mock classes | `mockernetes` or `kmock` | Stateful in-memory K8s cluster |
| Prometheus metrics | Custom HTTP metrics endpoint | `prometheus-client` | Standard format, auto-exposition |
| Audit hash chain | Custom Merkle implementation | SQLAlchemy with SHA-256 | Queryable, transaction-safe |
| Secret encryption | Custom XOR/proprietary | `cryptography` (AES-256-GCM) | Audited, secure defaults |

## Common Pitfalls

### Pitfall 1: K8s Client Version Mismatch
**What goes wrong:** Creating pods fails with "Failed to create pod: field label not supported"
**Why it happens:** K8s client version doesn't match cluster version
**How to avoid:** Pin client version to match cluster, use `kubectl version` to check
**Warning signs:** `ApiException: (422)`, field validation errors

### Pitfall 2: Docker SDK Connection Issues
**What goes wrong:** `docker.from_env()` fails with "Docker socket not found"
**Why it happens:** Running outside Docker context (CI/CD without Docker socket)
**How to avoid:** Use environment variables `DOCKER_HOST`, or mock for unit tests
**Warning signs:** `DockerException: Could not connect to the Docker daemon`

### Pitfall 3: Async/Sync Confusion
**What goes wrong:** Event loop blocks, timeouts, or "RuntimeError: Event loop is closed"
**Why it happens:** Mixing sync blocking calls in async functions
**How to avoid:** Use `asyncio.get_event_loop().run_in_executor()` for blocking calls
**Warning signs:** High latency, connection timeouts in async context

### Pitfall 4: WireGuard Root Requirement
**What goes wrong:** "Permission denied" when creating WireGuard interface
**Why it happens:** Creating network interfaces requires root/CAP_NET_ADMIN
**How to avoid:** Use config-file-based approach (wgconfig) for non-root, or run with elevated privileges
**Warning signs:** `OSError: [Errno 1] Operation not permitted`

### Pitfall 5: Prometheus Metrics Port Conflicts
**What goes wrong:** `AddrInUseError: [Errno 98] Address already in use`
**Why it happens:** Multiple services trying to use same metrics port
**How to avoid:** Configure different ports per service, use `pushgateway` for batch jobs
**Warning signs:** Service startup failures, metrics not exposed

## Code Examples

### Kubernetes Pod Creation with Security Context
```python
# Source: kubernetes-python official documentation
from kubernetes.client import V1Pod, V1Container, V1SecurityContext, V1PodSpec

def create_secure_pod(name: str, image: str) -> V1Pod:
    container = V1Container(
        name=name,
        image=image,
        security_context=V1SecurityContext(
            privileged=False,
            run_as_non_root=True,
            capabilities={"drop": ["ALL"]},
            seccomp_profile={"type": "RuntimeDefault"}
        )
    )
    return V1Pod(
        metadata={"name": name, "namespace": "default"},
        spec=V1PodSpec(containers=[container])
    )
```

### Docker Compose Health Check Integration
```python
# Source: pytest-docker documentation
import pytest
import requests

@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return "tests/fixtures/docker-compose.yml"

@pytest.fixture(scope="session")
def web_service(docker_services):
    port = docker_services.port_for("web", 8000)
    url = f"http://localhost:{port}"
    docker_services.wait_until_responsive(
        timeout=30.0,
        pause=0.1,
        check=lambda: requests.get(f"{url}/health").status_code == 200
    )
    return url
```

### Prometheus Metrics Export
```python
# Source: prometheus-client documentation
from prometheus_client import Counter, Histogram, start_http_server
import time

REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency')

class App:
    def handle_request(self, method: str, endpoint: str):
        start = time.time()
        # ... handle request ...
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.observe(time.time() - start)
```

### Mockernetes K8s Testing
```python
# Source: mockernetes documentation
import pytest
from kubernetes import client as k8s_client
from mockernetes import mock_kubernetes

@pytest.fixture
def k8s_cluster():
    with MockKubernetes() as mock_k8s:
        yield mock_k8s

def test_create_pod(k8s_cluster):
    core_api = k8s_client.CoreV1Api()
    pod = k8s_client.V1Pod(
        metadata=k8s_client.V1ObjectMeta(name="test-pod"),
        spec=k8s_client.V1PodSpec(
            containers=[k8s_client.V1Container(name="app", image="nginx")]
        )
    )
    created = core_api.create_namespaced_pod(namespace="default", body=pod)
    assert created.status.phase == "Running"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| docker-py (old name) | docker (v6+) | 2020 | Renamed package, API cleanup |
| Flask for async | FastAPI | 2023-2024 | Native async, 2-5x throughput |
| Custom K8s client | kubernetes (official) | 2016+ | 7.5k stars, official support |
| pickle in Celery | JSON serialization | 2023+ | Security hardening |
| prometheus-flask-exporter | prometheus-client | 2022+ | More control, less dependencies |

**Deprecated/outdated:**
- **docker-compose V1:** Deprecated July 2023, no longer maintained
- **Flask for new AI projects:** FastAPI has native async, 2-5x better throughput
- **Celery pickle serializer:** Security vulnerability, use JSON
- **python-gi for WireGuard:** Use wgconfig or wireguard-tools (pure Python)

## Open Questions

1. **K8s Mock Library Selection: mockernetes vs kmock**
   - What we know: mockernetes is moto-like (simpler API), kmock is more feature-rich (K8s stateful server)
   - What's unclear: Performance characteristics for large test suites
   - Recommendation: Start with mockernetes for simpler use cases, migrate to kmock if needed

2. **WireGuard Integration Strategy**
   - What we know: Multiple Python libraries exist (wgconfig, wireguard-tools, wireguard-py)
   - What's unclear: What's the best approach for containerized environment?
   - Recommendation: Use wgconfig for config parsing, wireguard-tools for key generation

3. **Async SQLAlchemy Patterns**
   - What we know: Must use `selectinload` for eager loading, avoid sync queries in async context
   - What's unclear: Transaction management patterns for long-running sessions
   - Recommendation: Follow SQLAlchemy 2.0 async patterns strictly

## Sources

### Primary (HIGH confidence)
- https://github.com/kubernetes-client/python - Official K8s Python client
- https://github.com/docker/docker-py - Official Docker SDK for Python
- https://docker-py.readthedocs.io/ - Docker SDK documentation
- https://github.com/prometheus/client_python - Official Prometheus Python client
- https://pypi.org/project/mockernetes/ - K8s mocking library
- https://pypi.org/project/wgconfig/ - WireGuard config parsing

### Secondary (MEDIUM confidence)
- https://kmock.readthedocs.io/ - Alternative K8s mock server
- https://github.com/avast/pytest-docker - Docker integration for pytest
- https://pypi.org/project/wireguard-tools/ - Pure Python WireGuard tools

### Tertiary (LOW confidence)
- https://github.com/facebookincubator/wireguard_py - Cython-based WireGuard (early stage)

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH - Verified via official documentation and GitHub
- Architecture Patterns: HIGH - Based on existing centinela-core patterns + official library documentation
- Pitfalls: MEDIUM - Based on community experience and common patterns
- Don't Hand-Roll: HIGH - Well-established best practices for Python container tooling

**Research date:** 2026-05-17
**Valid until:** 2026-06-17 (30 days for stable stack, libraries actively maintained)