# Contributing to CENTINELA

## Prerequisites

- Python 3.12+
- Docker 24+
- uv 0.11+

## Setup

```bash
# Clone and enter the repository
git clone <repo-url>
cd bayora

# Install uv (if not already installed)
# Windows:
powershell -c "irm https://astral.sh/uv/0.11.14/install.ps1 | iex"
# macOS/Linux:
# curl -LsSf https://astral.sh/uv/0.11.14/install.sh | sh

# Install all dependencies (including dev)
uv sync --all-packages --all-extras

# Install pre-commit hooks
uv run pre-commit install

# Create environment file
cp .env.example .env
# Edit .env with your API keys
```

## Development Workflow

```bash
# Lint and format
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy packages/ services/

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest -n auto --cov=services --cov=packages --cov-report=html

# Build Docker image
docker build -f Dockerfile.orchestrator -t centinela/orchestrator .
docker build -f Dockerfile.red-agent -t centinela/red-agent .
docker build -f Dockerfile.blue-agent -t centinela/blue-agent .
docker build -f Dockerfile.llm-sandbox -t centinela/llm-sandbox .
docker build -f Dockerfile.audit -t centinela/audit .
```

## Project Structure

```
bayora/
├── services/              # Deployable containers (each has its own Dockerfile)
│   ├── red-agent/         # Adversarial prompt generation and attack execution
│   ├── orchestrator/      # Session lifecycle, provider routing, coordination
│   ├── blue-agent/        # Safety evaluation and response classification
│   ├── llm-sandbox/       # Isolated model interaction and output sanitization
│   └── audit/             # Tamper-evident cryptographic logging and certificates
├── packages/              # Shared internal libraries
│   └── centinela-core/    # Core types, models, and interfaces
├── pyproject.toml         # Root workspace configuration
├── uv.lock                # Deterministic dependency lockfile
├── Dockerfile.*           # Multi-stage Dockerfiles at repo root
└── docker-compose.yml     # Single-command orchestration
```

## Quality Gates

Before committing, ensure:

1. **Ruff lint** passes: `ruff check .`
2. **Ruff format** passes: `ruff format --check .`
3. **Mypy type check** passes: `mypy packages/ services/`
4. **All tests pass**: `pytest -n auto --cov=services --cov=packages`
5. **Pre-commit hooks pass**: Run automatically on `git commit`

To skip pre-commit hooks (emergency only):
```bash
git commit --no-verify
```
