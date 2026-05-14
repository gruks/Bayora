# Phase 1: Foundation — Research

**Researched:** 2026-05-14
**Domain:** Python project setup, CI/CD, containerization
**Confidence:** HIGH

## Summary

Phase 1 establishes the entire CENTINELA project foundation: Python toolchain, monorepo structure, quality gates, Docker builds, and CI pipeline. Use **uv** as the package manager (replaces pip/pip-tools/poetry), **hatchling** as the PEP 621 build backend, **ruff** for linting+formatting (replaces flake8+black+isort), **mypy 2.0** with strict mode for type checking, **pytest 9.x** with xdist+cov for testing, and **pre-commit** for automated quality gates. The monorepo follows the `services/` + `libs/` pattern with a root `pyproject.toml` workspace. Docker uses multi-stage builds with `uv` in builder stage and distroless/slim runtime images. GitHub Actions runs lint → type-check → test → build with `astral-sh/setup-uv` for fast Python setup.

**Primary recommendation:** Use `uv` as the single tool for dependency management, virtual environments, and task running. Configure everything in `pyproject.toml` under `[tool.*]` sections. Use a monorepo workspace with `services/*` containers and `packages/*` shared libraries.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| uv | 0.11+ | Package & project manager | Single binary replaces pip/pip-tools/poetry/pipx/pyenv. Astral ecosystem (same team as ruff). Workspaces, lockfile, 10-100x faster than pip. |
| hatchling | latest | Build backend | PEP 621 compliant, fast, extensible. Default build backend for uv projects. Recommended for new pure-Python projects. |
| pytest | 9.0.x | Test framework | De facto standard Python test framework. 9.0.3 released Apr 2026. |
| pytest-cov | 7.1.x | Coverage reporting | Plugin for coverage.py integration. 7.1.0 released Mar 2026. |
| pytest-xdist | 3.8.x | Parallel test execution | Distributes test execution across CPUs/workers. |
| ruff | 0.15.x | Linter + formatter | All-in-one Rust-based linter and formatter. Replaces flake8, black, isort, pyupgrade, bugbear, etc. 10-100x faster. |
| mypy | 2.0.x | Static type checker | Industry standard Python type checker. 2.0.0 released May 2026 with new defaults (local-partial-types, strict-bytes). Drops Python 3.9 support. |
| pre-commit | 4.x+ | Git hook framework | Standardized Git hook management. Framework manages hook environments and versions. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | 0.28+ | Async HTTP client | For provider API calls (OpenAI, Anthropic). Modern replacement for requests. |
| pydantic | 2.x | Data validation | Settings management, request/response models. Use for configuration and data models. |
| python-dotenv | 1.x | .env file loading | Load environment variables from .env file for local development. |
| cryptography | 43+ | Cryptographic operations | Ed25519 signing, SHA-256 hashing for audit chain and certificates. |
| pre-commit-hooks | v6.0.0 | Basic git hooks | trailing-whitespace, end-of-file-fixer, check-yaml, check-added-large-files. |
| ruff-pre-commit | v0.15.x | Ruff pre-commit hooks | Mirrors ruff version. Provides ruff-check and ruff-format hooks. |
| mirrors-mypy | v2.0.0 | Mypy pre-commit hooks | Matches mypy version for pre-commit integration. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| uv + hatchling | Poetry | Poetry 2.0+ supports PEP 621 but is slower, ecosystem locked to Poetry. uv is faster, Astral ecosystem unifies tooling. |
| ruff | flake8 + black + isort | Legacy stack. 5+ tools vs 1. Ruff is 10-100x faster, single config, single dependency. |
| mypy | pyright | pyright (Microsoft) is faster but less mature ecosystem. mypy is the community standard, more plugins/stubs available. |
| pytest | unittest | Built-in but verbose, less plugin ecosystem, worse fixture model. pytest is universal in modern Python. |
| pre-commit | nox | nox is for test environments, not git hooks. pre-commit is specifically designed for pre-commit checks. |

**Installation:**
```bash
# Install uv (standalone installer, recommended)
powershell -c "irm https://astral.sh/uv/0.11.14/install.ps1 | iex"

# Or via pip
pip install uv
```

## Architecture Patterns

### Recommended Project Structure

```
bayora/
├── services/                    # Deployable containers (each has its own Dockerfile)
│   ├── red-agent/
│   │   ├── src/red_agent/
│   │   │   ├── __init__.py
│   │   │   └── main.py
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml       # Service-specific dependencies
│   ├── orchestrator/
│   │   ├── src/orchestrator/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   ├── blue-agent/
│   │   ├── src/blue_agent/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   ├── llm-sandbox/
│   │   ├── src/llm_sandbox/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   └── audit/
│       ├── src/audit/
│       ├── tests/
│       ├── Dockerfile
│       └── pyproject.toml
├── packages/                    # Shared internal libraries (imported by services)
│   ├── centinela-core/          # Core data models, enums, types
│   │   ├── src/centinela/
│   │   └── pyproject.toml
│   └── ...                      # Additional shared libs as needed
├── pyproject.toml               # Root workspace config + shared tool settings
├── uv.lock                      # Single lockfile for all dependencies
├── .pre-commit-config.yaml
├── Dockerfile.red-agent         # Dockerfiles at root for shared build context
├── Dockerfile.orchestrator
├── Dockerfile.blue-agent
├── Dockerfile.llm-sandbox
├── Dockerfile.audit
├── docker-compose.yml
├── .env.example
├── CONTRIBUTING.md
└── .github/
    └── workflows/
        └── ci.yml
```

**Rationale:** Dockerfiles at repo root so build context includes shared `packages/` directory. Each service has its own `pyproject.toml` for service-specific dependencies. Root `pyproject.toml` defines the workspace and shared tooling configuration (ruff, mypy, pytest). A single `uv.lock` ensures deterministic builds across all services.

### Pattern 1: uv Workspace Monorepo

**What:** Root `pyproject.toml` defines a workspace with members listed under `[tool.uv.workspace]`. Each member has its own `pyproject.toml`. A shared `uv.lock` tracks all dependencies.

**When to use:** Multi-service Python monorepo with shared internal libraries. Scales to 30-50 engineers and ~100 packages.

**Example:**
```toml
# Root pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "centinela"
requires-python = ">=3.12"

[tool.uv.workspace]
members = ["packages/*", "services/*"]

[tool.uv.sources]
centinela = { workspace = true }

# Shared tooling config lives here once, inherited by all members
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "C4", "SIM", "TCH", "RUF"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.12"
strict = true
```

### Pattern 2: Multi-stage Docker with uv

**What:** Two-stage Dockerfile. Build stage installs deps with `uv sync --no-dev --no-editable`. Runtime stage copies only `.venv` and app code. Cache mounts for speed.

**When to use:** Every service container.

**Example:**
```dockerfile
# Dockerfile.orchestrator
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-editable --no-install-project

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

FROM python:3.12-slim
ENV PATH="/app/.venv/bin:$PATH"
COPY --from=builder --chown=nonroot:nonroot /app/.venv /app/.venv
COPY --from=builder /app/services/orchestrator /app/services/orchestrator
WORKDIR /app/services/orchestrator
USER nonroot
CMD ["python", "-m", "orchestrator"]
```

### Pattern 3: GitHub Actions CI Pipeline

**What:** Four-job workflow: lint → type-check → test → build. Jobs run sequentially with dependency chaining.

**When to use:** Every push and pull request to main branch.

**Example:**
```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v8
        with:
          enable-cache: true
      - run: uvx ruff check .
      - run: uvx ruff format --check .

  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v8
        with:
          enable-cache: true
      - run: uv sync --frozen
      - run: uv run mypy services/ packages/

  test:
    runs-on: ubuntu-latest
    needs: [lint, type-check]
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v8
        with:
          enable-cache: true
      - run: uv sync --frozen
      - run: uv run pytest --cov=services --cov=packages --cov-report=xml -n auto
      - uses: codecov/codecov-action@v4
        if: matrix.python-version == '3.12'

  build:
    runs-on: ubuntu-latest
    needs: [test]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v8
        with:
          enable-cache: true
      - run: uv build --all-packages
```

### Anti-Patterns to Avoid

- **Flat layout instead of src/ layout:** Flat layout (`services/orchestrator/orchestrator/`) lets tests import from source tree directly, masking packaging bugs. Use `src/` layout (`services/orchestrator/src/orchestrator/`) so tests import the installed package.
- **Multiple config files:** Don't use `.flake8`, `.coveragerc`, `setup.cfg`, `mypy.ini`. Centralize everything in `pyproject.toml` under `[tool.*]` sections.
- **Pin exact versions in library dependencies:** Use range constraints (`>=`) for runtime dependencies so consuming projects don't have version conflicts. Pin exact versions only in `uv.lock` (handled automatically).
- **Install uv in runtime image:** uv is a build-time tool. Builder stage installs deps; runtime stage should not include uv. Reduces image size and attack surface.
- **Global pre-commit install:** Install pre-commit hooks per-repo with `uv run pre-commit install`, not globally. Ensures consistent versions.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dependency management | requirements.txt + pip | uv + pyproject.toml | uv is 10-100x faster, deterministic lockfile, workspace support |
| Linting + formatting | flake8 + black + isort + pyupgrade | ruff | One Rust binary replaces 5+ tools, 10-100x faster |
| CI Python setup | Manual Python install + caching | astral-sh/setup-uv | Official action, handles uv install + cache + Python version |
| Configuration loading | Custom env parser | python-dotenv | Standard library for .env loading, handles edge cases |
| Git hooks | Custom shell scripts | pre-commit | Framework manages hook environments, versions, and execution |

**Key insight:** The Python ecosystem has consolidated around a single modern stack (uv, ruff, mypy, pytest). Hand-rolling any of these wastes time and introduces subtle bugs that the community has already solved.

## Common Pitfalls

### Pitfall 1: Workspace `uv sync` fails because shared packages aren't copied to Docker build context

**What goes wrong:** Docker build fails with "package not found" when building a service that depends on a shared `packages/` library.
**Why it happens:** Docker builds in the context directory. If the Dockerfile is in `services/orchestrator/`, the build context only includes that directory, not `packages/`.
**How to avoid:** Place all Dockerfiles at repository root and set build context to `.`. Use `docker build -f Dockerfile.orchestrator .` to reference root-level Dockerfiles.
**Warning signs:** `uv sync` errors about missing workspace members during Docker build.

### Pitfall 2: Mypy strict mode overwhelming new codebase

**What goes wrong:** `strict = true` produces 100+ errors on first run, developer disables it entirely.
**Why it happens:** Strict mode enables 15+ optional flags. Third-party libraries lack type stubs.
**How to avoid:** Enable strict mode from day 0 (greenfield project). Add `[[tool.mypy.overrides]]` for untyped third-party libraries:
```toml
[[tool.mypy.overrides]]
module = ["openai.*", "anthropic.*"]
ignore_missing_imports = true
```
**Warning signs:** Any `# type: ignore` comments — minimize them from the start.

### Pitfall 3: Ruff linter and formatter disagree

**What goes wrong:** `ruff check --fix` changes code, then `ruff format` changes it back, or vice versa.
**Why it happens:** Some lint rules (e.g., `ISC001` implicit string concatenation) conflict with formatter output.
**How to avoid:** Disable conflicting rules explicitly:
```toml
[tool.ruff.lint]
ignore = ["ISC001"]  # Let formatter handle string concatenation
```
**Warning signs:** Pre-commit hooks alternating between lint-fix and format changes on the same file.

### Pitfall 4: `pytest --cov` flag eats the next argument

**What goes wrong:** `addopts = "--cov --cov-report xml"` in pyproject.toml causes pytest to interpret `--cov-report` as the source argument for `--cov`.
**Why it happens:** `--cov` takes an optional source argument. When followed by another flag, it can consume that flag as the source path.
**How to avoid:** Use `--cov=` (with trailing equals but empty value) to explicitly pass no source:
```toml
[tool.pytest.ini_options]
addopts = "--cov= --cov-report=xml -n auto"
```
**Warning signs:** Coverage reports showing 0% because coverage is measuring the wrong module.

### Pitfall 5: Poetry-style pyproject.toml breaking PEP 621 tools

**What goes wrong:** Tools expect `[project]` table but find `[tool.poetry]` — dependencies not detected.
**Why it happens:** Poetry <2.0 used `[tool.poetry]` instead of PEP 621 `[project]`. Some projects still use this format.
**How to avoid:** Use PEP 621 `[project]` table for metadata. Hatchling + uv are fully PEP 621 compliant. Avoid `[tool.poetry]`.
**Warning signs:** `uv sync` warns about missing `[project]` table.

## Code Examples

### Complete Root pyproject.toml
```toml
# Source: https://packaging.python.org/guides/writing-pyproject-toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "centinela"
version = "0.1.0"
description = "AI safety validation platform"
readme = "README.md"
requires-python = ">=3.12"
authors = [
    { name = "Bayora Hackathon Team" },
]
license = { text = "MIT" }
dependencies = [
    "httpx>=0.28",
    "pydantic>=2.0",
    "python-dotenv>=1.0",
    "cryptography>=43.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=9.0",
    "pytest-cov>=7.0",
    "pytest-xdist>=3.8",
    "ruff>=0.15",
    "mypy>=2.0",
    "pre-commit>=4.0",
]

[tool.uv.workspace]
members = ["packages/*", "services/*"]

[tool.uv.sources]
centinela = { workspace = true }

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "C4", "SIM", "TCH", "RUF"]
ignore = ["E501", "ISC001"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]
"__init__.py" = ["F401"]

[tool.ruff.format]
quote-style = "double"

[tool.mypy]
python_version = "3.12"
strict = true

[[tool.mypy.overrides]]
module = ["openai.*", "anthropic.*"]
ignore_missing_imports = true

[tool.pytest.ini_options]
minversion = "9.0"
addopts = "--strict-markers --strict-config --cov= --cov-report=term-missing -n auto"
testpaths = ["tests"]
xfail_strict = true
```

### Complete .pre-commit-config.yaml
```yaml
# Source: https://pre-commit.com
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ["--maxkb=5000"]

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.10
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v2.0.0
    hooks:
      - id: mypy
        files: ^(services/|packages/)
        additional_dependencies:
          - pydantic>=2.0
```

### .env.example
```bash
# CENTINELA Configuration
# Copy this file to .env and fill in your values.
# NEVER commit .env to version control.

# Provider API Keys
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Session Configuration
CENTINELA_MAX_API_CALLS=50
CENTINELA_MAX_BUDGET_USD=5.00

# Provider Cost Estimates (USD per 1K tokens)
OPENAI_COST_PER_1K=0.005
ANTHROPIC_COST_PER_1K=0.003

# Timing Jitter (milliseconds)
TIMING_JITTER_MIN=50
TIMING_JITTER_MAX=200

# Logging
LOG_LEVEL=INFO
```

### CONTRIBUTING.md Structure
```markdown
# Contributing to CENTINELA

## Prerequisites
- Python 3.12+
- Docker 24+
- uv 0.11+

## Setup

\`\`\`bash
# Clone and enter the repository
git clone <repo-url>
cd bayora

# Install uv (if not already installed)
powershell -c "irm https://astral.sh/uv/0.11.14/install.ps1 | iex"

# Install dependencies
uv sync --frozen

# Install pre-commit hooks
uv run pre-commit install

# Create environment file
cp .env.example .env
# Edit .env with your API keys
\`\`\`

## Development Workflow

\`\`\`bash
# Lint and format
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy services/ packages/

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=services --cov=packages --cov-report=html

# Build Docker image
docker build -f Dockerfile.orchestrator -t centinela/orchestrator .
\`\`\`

## Project Structure

- \`services/\` — Deployable containers (each has its own Dockerfile)
- \`packages/\` — Shared internal libraries
- \`pyproject.toml\` — Root workspace configuration
- \`uv.lock\` — Deterministic dependency lockfile

## Quality Gates

Before committing, ensure:
1. Ruff lint passes (\`ruff check .\`)
2. Ruff format passes (\`ruff format --check .\`)
3. Mypy type check passes (\`mypy services/ packages/\`)
4. All tests pass (\`pytest\`)
5. Pre-commit hooks pass (run automatically on \`git commit\`)

To skip pre-commit hooks (emergency only): \`git commit --no-verify\`
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pip + requirements.txt | uv + pyproject.toml + uv.lock | 2024-2025 | 10-100x faster, deterministic, workspace support |
| flake8 + black + isort | ruff | 2023-2025 | 5+ tools → 1, 10-100x faster, Rust-based |
| setup.py/setup.cfg | pyproject.toml (PEP 621) | 2020-2025 | Declarative, secure, no arbitrary code execution |
| mypy 1.x defaults | mypy 2.0 + strict mode | May 2026 | local-partial-types by default, strict-bytes by default, drops Python 3.9 |
| pytest 7.x | pytest 9.x | 2024-2026 | Native --json-report, improved fixtures, faster collection |
| actions/setup-python | astral-sh/setup-uv | 2024-2025 | Native uv + cache support, single action for Python + package manager |

**Deprecated/outdated:**
- **setup.py for metadata:** PEP 621 `[project]` table is the standard. Keep `setup.py` only for C extensions.
- **requirements.txt:** Use `pyproject.toml` `[project.dependencies]` + `uv.lock`. Generate requirements.txt from lockfile only if needed for legacy systems.
- **Flake8/Black/Isort:** All replaced by ruff. Migration is straightforward: ruff has drop-in parity.
- **pip-compile/pip-tools:** Replaced by `uv lock` and `uv sync`.
- **Python 3.9 support:** mypy 2.0 drops Python 3.9 runtime support. Project targets 3.12+.

## Open Questions

1. **Should containers use distroless or slim base images?**
   - What we know: distroless (`gcr.io/distroless/python3-debian12:nonroot`) has zero shell/package manager, minimal attack surface. Slim (`python:3.12-slim`) has `apt` and common tools for debugging.
   - What's unclear: Whether debugging access is needed in production containers for this project. Distroless makes debugging impossible without `kubectl exec` workarounds.
   - Recommendation: Use `python:3.12-slim` for Phase 4 (easier debugging, still small). Revisit distroless in Phase 14 (Container Image Security) when security hardening is the focus.

2. **Single root-level Dockerfiles vs service-level Dockerfiles?**
   - What we know: Root-level Dockerfiles allow shared build context including `packages/`. Service-level Dockerfiles can't access parent directories without complex Docker context tricks.
   - What's unclear: Whether `docker buildx bake` should be used for multi-container builds instead of individual Dockerfiles.
   - Recommendation: Use root-level Dockerfiles individually. `docker compose up` handles multi-container orchestration. Adopt `docker buildx bake` in Phase 14 if build parallelism matters.

3. **What shared library should go in `packages/` vs being copied into each service?**
   - What we know: Core data models, provider adapter interface, audit log format, and configuration types are shared across multiple services.
   - What's unclear: Exact boundaries until Phase 1 code is written.
   - Recommendation: Start with `packages/centinela-core/` for shared types/enums/interfaces. Extract additional shared libraries during Phase 1 development when >2 services need the same code.

## Sources

### Primary (HIGH confidence)
- [Python Packaging User Guide: Writing pyproject.toml](https://packaging.python.org/guides/writing-pyproject-toml) — Official standard for pyproject.toml format
- [Ruff Documentation: Configuration](https://docs.astral.sh/ruff/configuration/) — Ruff official docs for lint/format config
- [Mypy Documentation: Config File](https://mypy.readthedocs.io/en/stable/config_file.html) — Mypy official config docs, 2.0 release notes
- [uv Documentation: Workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/) — uv official workspace docs
- [uv Documentation: Docker Integration](https://docs.astral.sh/uv/guides/integration/docker/) — uv official Docker multi-stage pattern
- [astral-sh/setup-uv README](https://github.com/astral-sh/setup-uv) — Official GitHub Action for uv
- [Pytest Documentation: Configuration](https://docs.pytest.org/en/stable/reference/customize.html) — pytest config file formats
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/en/stable/config.html) — pytest-cov official config
- [pre-commit Documentation](https://pre-commit.com) — pre-commit framework docs
- [pre-commit/pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks) — Official hook repository
- [astral-sh/ruff-pre-commit](https://github.com/astral-sh/ruff-pre-commit) — Official ruff pre-commit hooks
- [pre-commit/mirrors-mypy](https://github.com/pre-commit/mirrors-mypy) — Official mypy pre-commit mirror
- [PEP 621](https://peps.python.org/pep-0621/) — Storing project metadata in pyproject.toml
- [PEP 518](https://peps.python.org/pep-0518/) — Specifying minimum build system requirements

### Secondary (MEDIUM confidence)
- [pydevtools.com: How to configure mypy strict mode](https://pydevtools.com/handbook/how-to/how-to-configure-mypy-strict-mode) — Verified against official mypy docs
- [pydevtools.com: How to set up pre-commit hooks for Python](https://pydevtools.com/handbook/how-to/how-to-set-up-pre-commit-hooks-for-a-python-project) — Verified against official pre-commit docs
- [pydevtools.com: Ruff complete guide](https://pydevtools.com/handbook/explanation/ruff-complete-guide) — Verified against ruff official docs
- [timothy-jeong/monorepo-example](https://github.com/timothy-jeong/monorepo-example) — Verified uv workspace monorepo pattern
- [GitHub Docs: Building and testing Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-nodejs-or-python?langId=py) — Official GitHub Actions Python guide
- [digon.io: Build multistage Python Docker images using UV](https://digon.io/en/blog/2025_07_28_python_docker_images_with_uv) — Verified against uv official Docker docs

### Tertiary (LOW confidence)
- [nerdleveltech.com: Distroless Python containers with uv tutorial](https://nerdleveltech.com/distroless-python-containers-with-uv-tutorial) — Single source, needs validation against official distroless docs. Used for pattern ideas only.
- [Medium articles on pyproject.toml patterns](https://medium.com/@usamanawaz789/how-to-configure-ruff-mypy-and-pre-commit-for-production-ai-python-projects-1b3fc56d3d4c) — Community patterns, verified against official docs where possible.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — All tools verified against official documentation and current PyPI releases
- Architecture: HIGH — uv workspace monorepo pattern validated by official uv docs and reference implementations
- Pitfalls: HIGH — All pitfalls documented from official docs or widely known community knowledge
- Docker: MEDIUM — Multi-stage pattern from uv official docs. Distroless question (Open Question 1) is unresolved.

**Research date:** 2026-05-14
**Valid until:** 2026-08-14 (stable stack — uv, ruff, mypy, pytest are mature. Re-validate tool versions in 90 days.)
