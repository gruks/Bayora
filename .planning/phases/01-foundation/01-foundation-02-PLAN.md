---
phase: 01-foundation
plan: 02
type: execute
wave: 2
depends_on: ["01"]
files_modified:
  - .pre-commit-config.yaml
  - .env.example
  - CONTRIBUTING.md
  - Dockerfile.red-agent
  - Dockerfile.orchestrator
  - Dockerfile.blue-agent
  - Dockerfile.llm-sandbox
  - Dockerfile.audit
  - docker-compose.yml
  - .github/workflows/ci.yml
autonomous: true
user_setup: []

must_haves:
  truths:
    - "Developer can install pre-commit hooks and hooks run automatically on git commit"
    - "Developer can build Docker images for all 5 containers from repo root"
    - "CI pipeline defines lint → type-check → test → build workflow"
    - "Developer can copy .env.example to .env and see all configuration keys documented"
    - "Developer can follow CONTRIBUTING.md setup instructions from scratch"
  artifacts:
    - path: ".pre-commit-config.yaml"
      provides: "Ruff lint, Ruff format, and mypy pre-commit hooks"
      contains: "ruff-pre-commit", "mirrors-mypy"
    - path: "Dockerfile.* (5 files at repo root)"
      provides: "Multi-stage Dockerfiles with uv builder, slim runtime, health checks"
      contains: "astral-sh/uv", "HEALTHCHECK"
    - path: "docker-compose.yml"
      provides: "Single-command orchestration for all 5 containers"
    - path: ".github/workflows/ci.yml"
      provides: "CI pipeline definition"
      contains: "astral-sh/setup-uv", "needs: [lint, type-check]", "needs: [test]"
    - path: ".env.example"
      provides: "Documented configuration template"
    - path: "CONTRIBUTING.md"
      provides: "Development setup instructions"
  key_links:
    - from: ".pre-commit-config.yaml"
      to: "pyproject.toml"
      via: "Ruff and mypy configs in [tool.*] sections"
    - from: "Dockerfile.red-agent"
      to: "services/red-agent/"
      via: "COPY command in runtime stage"
      pattern: "COPY.*services/red-agent"
    - from: "Dockerfile.*"
      to: "packages/centinela-core/"
      via: "COPY . . (includes packages/ in build context)"
      pattern: "COPY \\. \\."
    - from: ".github/workflows/ci.yml"
      to: "astral-sh/setup-uv"
      via: "uses: astral-sh/setup-uv@v8"
    - from: ".github/workflows/ci.yml test job"
      to: "lint + type-check jobs"
      via: "needs: [lint, type-check]"

---

<objective>
Configure quality gates, containerization, and CI pipeline: pre-commit hooks, multi-stage Dockerfiles, docker-compose orchestration, CI workflow, environment template, and contributing guide.

Purpose: Lock in code quality with automated pre-commit hooks, enable containerized deployment with multi-stage secure Docker builds, and define the CI pipeline that gates all PRs.

Output: 10 files — pre-commit config, 5 Dockerfiles, docker-compose.yml, CI workflow, .env.example, CONTRIBUTING.md.
</objective>

<execution_context>
@C:/Users/HP/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/HP/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/project.md
@.planning/phases/01-foundation/01-RESEARCH.md

Key patterns from research:
- **Multi-stage Docker**: uv builder stage (astral-sh/uv image) → slim runtime stage (python:3.12-slim). uv NOT included in runtime image (reduces size + attack surface).
- **Root-level Dockerfiles**: All Dockerfiles at repo root so `docker build -f Dockerfile.X .` has build context including `packages/` directory. Avoids Pitfall 1 (workspace packages missing in build context).
- **nonroot user**: Runtime stage uses `--chown=nonroot:nonroot`, USER nonroot for security.
- **ci.yml**: 4 sequential jobs: lint → type-check → test (matrix: 3.12, 3.13) → build. Uses `astral-sh/setup-uv@v8` not `setup-python`.
- **UV_COMPILE_BYTECODE=1**: Compile .pyc during build for faster startup.
- **UV_LINK_MODE=copy**: Copy instead of symlink in Docker (symlinks break across stages).
- **Cache mounts**: `--mount=type=cache,target=/root/.cache/uv` for faster rebuilds.
- **`uv sync --locked`**: Use lockfile in Docker builds (deterministic). Must create uv.lock first via `uv sync` in dev.
- **Health checks**: Use `python -c "import {service_package}"` as simple health check for stubs.
- **pre-commit**: 3 hooks from 3 repos: pre-commit-hooks (trailing-whitespace, end-of-file-fixer, check-yaml, check-added-large-files), ruff-pre-commit (ruff-check, ruff-format), mirrors-mypy (mypy on services/ and packages/).
</context>

<tasks>

<task type="auto">
  <name>Task 1: Pre-commit hooks, env template, and contributing guide</name>
  <files>
    .pre-commit-config.yaml
    .env.example
    CONTRIBUTING.md
  </files>
  <action>
    Create `.pre-commit-config.yaml` following 01-RESEARCH.md §Code Examples with hooks from:
    - `pre-commit/pre-commit-hooks` rev v6.0.0: trailing-whitespace, end-of-file-fixer, check-yaml, check-added-large-files (args: --maxkb=5000)
    - `astral-sh/ruff-pre-commit` rev v0.15.10: ruff-check (args: --fix), ruff-format
    - `pre-commit/mirrors-mypy` rev v2.0.0: mypy (files: ^(services/|packages/)), additional_dependencies: [pydantic>=2.0]

    Create `.env.example`:
    ```bash
    # CENTINELA Configuration
    # Copy to .env — NEVER commit .env to version control.

    # Provider API Keys
    OPENAI_API_KEY=
    ANTHROPIC_API_KEY=

    # Session Configuration
    CENTINELA_MAX_API_CALLS=50
    CENTINELA_MAX_BUDGET_USD=5.00

    # Provider Cost Estimates (USD per 1K tokens)
    OPENAI_COST_PER_1K=0.005
    ANTHROPIC_COST_PER_1K=0.003

    # Timing Jitter (milliseconds) — defeats side-channel inference
    TIMING_JITTER_MIN=50
    TIMING_JITTER_MAX=200

    # Logging
    LOG_LEVEL=INFO
    ```

    Create `CONTRIBUTING.md` following 01-RESEARCH.md §Code Examples structure:
    - ## Prerequisites: Python 3.12+, Docker 24+, uv 0.11+
    - ## Setup: clone, uv install, `uv sync --frozen`, `uv run pre-commit install`, `cp .env.example .env`
    - ## Development Workflow: ruff check, ruff format, mypy, pytest, docker build commands
    - ## Project Structure: services/, packages/, pyproject.toml, uv.lock
    - ## Quality Gates: 5 checks before committing, pre-commit runs automatically on `git commit`
    - Include `git commit --no-verify` as emergency override note

    IMPORTANT: All 3 files should reference exact commands that work with the project structure created in Plan 01.
  </action>
  <verify>
    uv run pre-commit run --all-files (all hooks pass on existing files)
    grep "OPENAI_API_KEY" .env.example (keys exist)
    grep "uv run pre-commit install" CONTRIBUTING.md (setup docs reference correct commands)
  </verify>
  <done>
    Pre-commit hooks installed and passing. Environment template documents all config options. Contributing guide has complete setup instructions.
  </done>
</task>

<task type="auto">
  <name>Task 2: Multi-stage Dockerfiles + docker-compose.yml</name>
  <files>
    Dockerfile.red-agent
    Dockerfile.orchestrator
    Dockerfile.blue-agent
    Dockerfile.llm-sandbox
    Dockerfile.audit
    docker-compose.yml
  </files>
  <action>
    Create 5 Dockerfiles at repo root following 01-RESEARCH.md §Pattern 2 (multi-stage with uv):

    **Builder stage** (identical across all 5):
    ```dockerfile
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
    ```

    **Runtime stage** (varies by service):
    ```dockerfile
    FROM python:3.12-slim
    ENV PATH="/app/.venv/bin:$PATH"
    COPY --from=builder --chown=nonroot:nonroot /app/.venv /app/.venv
    COPY --from=builder --chown=nonroot:nonroot /app/services/{service_name} /app/services/{service_name}
    WORKDIR /app/services/{service_name}
    HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
        CMD python -c "from {python_package} import main; exit(0)"
    USER nonroot
    CMD ["python", "-m", "{python_package}"]
    ```

    Service-specific runtime values:
    | Dockerfile           | service_name   | python_package |
    |----------------------|----------------|----------------|
    | Dockerfile.red-agent | red-agent      | red_agent      |
    | Dockerfile.orchestrator | orchestrator | orchestrator   |
    | Dockerfile.blue-agent  | blue-agent   | blue_agent     |
    | Dockerfile.llm-sandbox | llm-sandbox  | llm_sandbox    |
    | Dockerfile.audit       | audit        | audit          |

    Create `docker-compose.yml` with 5 services, each building from its Dockerfile:
    ```yaml
    services:
      red-agent:
        build:
          context: .
          dockerfile: Dockerfile.red-agent
        ports: []
        networks: []
      orchestrator:
        build:
          context: .
          dockerfile: Dockerfile.orchestrator
        ports: ["8080:8080"]
      blue-agent:
        build:
          context: .
          dockerfile: Dockerfile.blue-agent
        ports: []
      llm-sandbox:
        build:
          context: .
          dockerfile: Dockerfile.llm-sandbox
        ports: []
      audit:
        build:
          context: .
          dockerfile: Dockerfile.audit
        ports: []
    ```
    All services use `context: .` (repo root) so Docker build context includes `packages/` and root `pyproject.toml` + `uv.lock`. Use `docker/compose:latest` or pinned version.

    IMPORTANT SAFETY NOTES:
    - Do NOT install uv in runtime stage (build-time tool only — reduces image size and attack surface)
    - Use `--locked` flag (not `--frozen`) in Dockerfiles — lockfile is copied into context
    - All COPY commands use `--chown=nonroot:nonroot` (prevents root-owned files in runtime)
    - Set `USER nonroot` before CMD (container runs without root privileges)
    - Health check uses `python -c "import {pkg}"` which works for stub modules
    - Dockerfiles at repo root with context `.` avoids Pitfall 1 (missing packages in build context)
  </action>
  <verify>
    docker build -f Dockerfile.orchestrator -t centinela/orchestrator . (builds without errors)
    docker build -f Dockerfile.red-agent -t centinela/red-agent . (builds without errors)
    docker build -f Dockerfile.blue-agent -t centinela/blue-agent . (builds without errors)
    docker build -f Dockerfile.llm-sandbox -t centinela/llm-sandbox . (builds without errors)
    docker build -f Dockerfile.audit -t centinela/audit . (builds without errors)
    # Docker build verification is optional per acceptance criteria — if Docker is not available in CI, skip.
  </verify>
  <done>
    5 Dockerfiles exist at repo root, each produces a working Docker image. docker-compose.yml defines all 5 services.
  </done>
</task>

<task type="auto">
  <name>Task 3: GitHub Actions CI pipeline</name>
  <files>
    .github/workflows/ci.yml
  </files>
  <action>
    Create `.github/workflows/ci.yml` following 01-RESEARCH.md §Pattern 3 with 4 jobs:

    **lint job:**
    - runs-on: ubuntu-latest
    - actions/checkout@v4
    - astral-sh/setup-uv@v8 with enable-cache: true
    - `uvx ruff check .`
    - `uvx ruff format --check .`

    **type-check job:**
    - runs-on: ubuntu-latest
    - actions/checkout@v4
    - astral-sh/setup-uv@v8 with enable-cache: true
    - `uv sync --frozen`
    - `uv run mypy services/ packages/`

    **test job:**
    - needs: [lint, type-check]
    - strategy matrix: python-version ["3.12", "3.13"]
    - runs-on: ubuntu-latest
    - actions/checkout@v4
    - astral-sh/setup-uv@v8 with enable-cache: true, cache-dependency-glob: "uv.lock"
    - `uv sync --frozen`
    - `uv run pytest -n auto --cov=services --cov=packages --cov-report=xml`
    - codecov/codecov-action@v4 (if: matrix.python-version == '3.12')

    **build job:**
    - needs: [test]
    - runs-on: ubuntu-latest
    - actions/checkout@v4
    - astral-sh/setup-uv@v8 with enable-cache: true
    - `uv build --all-packages`

    CI triggers: `push` and `pull_request` on `main` branch.

    IMPORTANT NOTES:
    - Use `astral-sh/setup-uv@v8` (NOT `actions/setup-python`) — per research, this is the modern approach that handles uv install + cache + Python version
    - Use `uv sync --frozen` (NOT `uv sync`) — ensures CI uses committed lockfile
    - Use `uvx` for ruff (avoids installing ruff as project dependency for lint job — runs from cache)
    - Use `uv run` for mypy and pytest (runs within project venv)
    - Test job depends on both lint AND type-check (quality gates must pass before testing)
    - Build job depends on test (only build if tests pass)
    - codecov step only runs for Python 3.12 to avoid duplicate uploads
    - Do NOT add a Docker build step to CI — this is a code-quality pipeline; Docker build is optional per acceptance criteria and can be added in a later phase
  </action>
  <verify>
    Verify YAML syntax is valid:
    python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" (no YAML errors)
    Verify workflow structure:
    grep "name: CI" .github/workflows/ci.yml
    grep "needs: \[lint, type-check\]" .github/workflows/ci.yml (test depends on lint+type-check)
    grep "needs: \[test\]" .github/workflows/ci.yml (build depends on test)
    grep "astral-sh/setup-uv@v8" .github/workflows/ci.yml (uses correct action)
  </verify>
  <done>
    CI pipeline defines 4 jobs with correct dependency chain. YAML is valid. Uses astral-sh/setup-uv@v8.
  </done>
</task>

</tasks>

<verification>
```bash
# 1. Verify pre-commit hooks
uv run pre-commit run --all-files

# 2. Verify YAML syntax of CI workflow
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"

# 3. Verify key patterns in all generated files
grep -r "from pydantic" .pre-commit-config.yaml  # mypy hook provides pydantic stubs
grep "astral-sh/uv" Dockerfile.orchestrator       # Docker uses uv in builder stage
grep "HEALTHCHECK" Dockerfile.orchestrator        # Docker has health check
grep "nonroot" Dockerfile.orchestrator            # Runtime runs as nonroot user

# 4. Optional: Docker build (skip if Docker not available)
if command -v docker &> /dev/null; then
    docker build -f Dockerfile.orchestrator -t centinela/orchestrator . --quiet
fi
```

Run ordered verification. Steps 1-3 must pass before considering this plan complete. Step 4 is optional.
</verification>

<success_criteria>
- `uv run pre-commit run --all-files` passes with zero hook failures
- `.github/workflows/ci.yml` parses as valid YAML
- CI job dependency chain is correct: lint, type-check → test → build
- `astral-sh/setup-uv@v8` is used in all CI jobs (not `actions/setup-python`)
- All 5 Dockerfiles exist at repo root with multi-stage builds
- All Dockerfiles include HEALTHCHECK instruction
- All Dockerfiles use `USER nonroot` before CMD
- docker-compose.yml references all 5 Dockerfiles with context: .
- `.env.example` documents all 6 configuration sections (keys, session, cost, jitter, logging)
- CONTRIBUTING.md includes setup commands and quality gate checklist
- All 10 files listed in files_modified exist on disk
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation/01-foundation-02-SUMMARY.md`
</output>
