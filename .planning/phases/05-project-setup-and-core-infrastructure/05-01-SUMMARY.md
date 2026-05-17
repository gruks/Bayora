---
phase: 05-project-setup-and-core-infrastructure
plan: 01
subsystem: infra
tags: [kubernetes, docker, fastapi, sqlalchemy, pytest, prometheus, structlog]

# Dependency graph
requires:
  - phase: 04-container-integration-certificates
    provides: Docker Compose, gVisor, audit chain, PDF certificates
provides:
  - Core platform dependencies for 8 modules (orchestrator, config, secrets, audit, provenance, anomaly, network, resources)
  - Testing infrastructure with docker and k8s mocking
affects: [06-dataset-management, 07-configuration-parser, 08-secrets-manager, 09-audit-log-service]

# Tech tracking
tech-stack:
  added: [kubernetes>=35.0, docker>=7.1, aiodocker>=0.26, fastapi>=0.115, sqlalchemy[asyncio]>=2.0, prometheus-client>=0.25, wgconfig>=1.2, structlog>=24.4, pytest-docker>=3.2, pytest-asyncio>=0.24, mockernetes>=0.2, kmock>=0.7, requests>=2.32]
  patterns: [uv workspace, pytest fixtures, async testing]

key-files:
  created: [tests/conftest.py]
  modified: [pyproject.toml, packages/centinela-core/pyproject.toml]

key-decisions:
  - "Used uv workspace membership to link centinela-core package"
  - "Configured pytest-asyncio with auto mode for async test discovery"

patterns-established:
  - "pytest-docker-compose integration tests pattern"
  - "mockernetes K8s unit test mocking pattern"

# Metrics
duration: 11min
completed: 2026-05-17
---

# Phase 5 Plan 1: Core Dependencies Summary

**Core platform dependencies installed, pytest fixtures created for 8 modules**

## Performance

- **Duration:** 11 min
- **Started:** 2025-05-17T15:23:17Z
- **Completed:** 2025-05-17T15:34:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Added 8 core dependencies (kubernetes, docker, aiodocker, fastapi, sqlalchemy, prometheus-client, wgconfig, structlog)
- Added 5 test dependencies (pytest-docker, pytest-asyncio, mockernetes, kmock, requests)
- Added prometheus-client and structlog to centinela-core shared package
- Created tests/conftest.py with pytest-asyncio configuration and docker/k8s mock fixtures

## Task Commits

Each task was committed atomically:

1. **All 3 tasks:** - `70e990a` (feat)

**Plan metadata:** `70e990a` (docs: complete plan)

## Files Created/Modified
- `pyproject.toml` - Added core dependencies and test dependencies
- `packages/centinela-core/pyproject.toml` - Added prometheus-client and structlog
- `tests/conftest.py` - Created with pytest-asyncio and docker/k8s fixtures

## Decisions Made

- Used uv workspace membership to link centinela-core package — enables sharing prometheus-client and structlog across all services
- Configured pytest-asyncio with auto mode for async test discovery — simplifies async test writing

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 8 core dependencies installed without conflicts
- Testing infrastructure ready for docker-compose and k8s mocking
- Ready for dataset management (06), configuration parser (07), and secrets manager (08) modules

---
*Phase: 05-project-setup-and-core-infrastructure*
*Completed: 2026-05-17*