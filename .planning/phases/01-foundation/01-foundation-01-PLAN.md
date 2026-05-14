---
phase: 01-foundation
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - pyproject.toml
  - .gitignore
  - packages/centinela-core/pyproject.toml
  - packages/centinela-core/src/centinela/__init__.py
  - packages/centinela-core/src/centinela/models.py
  - services/red-agent/pyproject.toml
  - services/red-agent/src/red_agent/__init__.py
  - services/red-agent/src/red_agent/main.py
  - services/red-agent/tests/__init__.py
  - services/red-agent/tests/test_stub.py
  - services/orchestrator/pyproject.toml
  - services/orchestrator/src/orchestrator/__init__.py
  - services/orchestrator/src/orchestrator/main.py
  - services/orchestrator/tests/__init__.py
  - services/orchestrator/tests/test_stub.py
  - services/blue-agent/pyproject.toml
  - services/blue-agent/src/blue_agent/__init__.py
  - services/blue-agent/src/blue_agent/main.py
  - services/blue-agent/tests/__init__.py
  - services/blue-agent/tests/test_stub.py
  - services/llm-sandbox/pyproject.toml
  - services/llm-sandbox/src/llm_sandbox/__init__.py
  - services/llm-sandbox/src/llm_sandbox/main.py
  - services/llm-sandbox/tests/__init__.py
  - services/llm-sandbox/tests/test_stub.py
  - services/audit/pyproject.toml
  - services/audit/src/audit/__init__.py
  - services/audit/src/audit/main.py
  - services/audit/tests/__init__.py
  - services/audit/tests/test_stub.py
autonomous: true
user_setup: []

must_haves:
  truths:
    - "Developer can install all dependencies with `uv sync` — no errors"
    - "Developer can run `ruff check .` with zero lint errors"
    - "Developer can run `ruff format --check .` with zero formatting issues"
    - "Developer can run `uv run mypy services/ packages/` with zero type errors"
    - "Developer can run `uv run pytest` with all stubs discovered and >80% code coverage"
  artifacts:
    - path: "pyproject.toml"
      provides: "Root workspace + tool config"
      contains: "[tool.uv.workspace]", "[tool.ruff]", "[tool.mypy]", "[tool.pytest.ini_options]"
    - path: "packages/centinela-core/pyproject.toml"
      provides: "Shared library package definition"
      contains: "name = \"centinela-core\""
    - path: "services/*/pyproject.toml"
      provides: "Per-service package definitions"
      provides: "5 pyproject.toml files, one per service"
    - path: ".gitignore"
      provides: "Standard Python gitignore rules"
    - path: "services/*/src/*/__init__.py"
      provides: "Package init stubs for all 5 services"
    - path: "services/*/tests/__init__.py + test_stub.py"
      provides: "Test discovery infrastructure for all 5 services"
  key_links:
    - from: "pyproject.toml"
      to: "packages/*, services/*"
      via: "[tool.uv.workspace] members"
      pattern: "members = \\[\"packages/\\*\", \"services/\\*\"\\]"
    - from: "pyproject.toml [tool.uv.sources]"
      to: "packages/centinela-core"
      via: "workspace reference"
      pattern: "centinela-core = \\{ workspace = true \\}"
    - from: "services/*/pyproject.toml"
      to: "packages/centinela-core"
      via: "[project.dependencies]"
      pattern: "\"centinela-core\""
    - from: "services/*/tests/test_stub.py"
      to: "services/*/src/*/"
      via: "import in test"
      pattern: "from .* import"

---

<objective>
Create the complete Python project skeleton: root workspace configuration, shared package (centinela-core), and all 5 service containers with stub modules and test infrastructure.

Purpose: Establishes the monorepo structure that all subsequent phases build upon. Every Python file, config, and test stub must exist so that `uv sync`, `ruff`, `mypy`, and `pytest` all pass with zero errors.

Output: 30 files — root pyproject.toml, .gitignore, centinela-core package (3 files), and 5 services (5 files each = 25 files).
</objective>

<execution_context>
@C:/Users/HP/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/HP/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/project.md
@.planning/phases/01-foundation/01-RESEARCH.md

Key patterns from research:
- **src/ layout**: Each service uses `src/{service_name}/` not flat layout (avoids import ambiguity)
- **PEP 621**: Use `[project]` table, NOT `[tool.poetry]` (handles hatchling/uv compatibility)
- **Single config**: ALL tool configs in root `pyproject.toml` `[tool.*]` sections — no separate `.flake8`, `mypy.ini`, `.coveragerc`
- **ISC001 ignored**: Prevents linter/formatter conflict on implicit string concatenation
- **E501 ignored**: Line length enforced by `ruff format`, not lint
- **`--cov=` equals trick**: Prevents pytest `--cov` from eating next flag as source path
- **S101 allowed in tests**: `assert` is valid in test files
- **F401 allowed in __init__.py**: Re-exports are the pattern, not unused imports
</context>

<tasks>

<task type="auto">
  <name>Task 1: Root pyproject.toml workspace + .gitignore</name>
  <files>
    pyproject.toml
    .gitignore
  </files>
  <action>
    Create root `pyproject.toml` following the complete example in 01-RESEARCH.md §Code Examples with these specifics:

    [build-system]: hatchling build backend (requires=["hatchling"], build-backend="hatchling.build")
    [project]: name="centinela", version="0.1.0", description="AI safety validation platform", requires-python=">=3.12"
    [project.dependencies]: httpx>=0.28, pydantic>=2.0, python-dotenv>=1.0, cryptography>=43.0
    [project.optional-dependencies]: dev = [pytest>=9.0, pytest-cov>=7.0, pytest-xdist>=3.8, ruff>=0.15, mypy>=2.0, pre-commit>=4.0]
    [tool.uv.workspace]: members = ["packages/*", "services/*"]
    [tool.uv.sources]: centinela-core = { workspace = true }
    [tool.ruff]: target-version="py312", line-length=100
    [tool.ruff.lint]: select E,W,F,I,N,UP,B,C4,SIM,TCH,RUF; ignore E501,ISC001
    [tool.ruff.lint.per-file-ignores]: tests/** = [S101], __init__.py = [F401]
    [tool.ruff.format]: quote-style="double"
    [tool.mypy]: python_version="3.12", strict=true
    [[tool.mypy.overrides]]: module=["openai.*","anthropic.*"], ignore_missing_imports=true
    [tool.pytest.ini_options]: minversion="9.0", addopts="--strict-markers --strict-config --cov= --cov-report=term-missing -n auto", testpaths=["tests"], xfail_strict=true

    Create `.gitignore` with:
    # Python
    __pycache__/
    *.py[cod]
    *.egg-info/
    .venv/
    dist/
    build/
    # Environment
    .env
    # IDE
    .vscode/
    .idea/
    # OS
    .DS_Store
    Thumbs.db
    # Coverage
    htmlcov/
    .coverage
    .coverage.*

    Do NOT include uv.lock in .gitignore (it must be committed for deterministic builds).
    Do NOT create any separate config files (.flake8, mypy.ini, .coveragerc, setup.cfg).
  </action>
  <verify>
    uv sync (generates uv.lock without errors)
    ruff check . (zero errors)
    ruff format --check . (zero formatting changes needed)
  </verify>
  <done>
    Root pyproject.toml exists with workspace pointing to packages/* and services/*.
    uv.lock is generated. Ruff and basic tool configs are functional.
  </done>
</task>

<task type="auto">
  <name>Task 2: Shared package — centinela-core</name>
  <files>
    packages/centinela-core/pyproject.toml
    packages/centinela-core/src/centinela/__init__.py
    packages/centinela-core/src/centinela/models.py
  </files>
  <action>
    Create `packages/centinela-core/pyproject.toml`:
    [build-system]: hatchling
    [project]: name="centinela-core", version="0.1.0", description="Shared core types, models, and interfaces for CENTINELA services", requires-python=">=3.12"
    [project.dependencies]: pydantic>=2.0

    Create `packages/centinela-core/src/centinela/__init__.py`:
    Empty file with docstring: """CENTINELA shared core — types, models, and interfaces."""

    Create `packages/centinela-core/src/centinela/models.py`:
    Stub file with a base class `SessionConfig` and `AuditEntry` using pydantic BaseModel:
    ```python
    from pydantic import BaseModel
    from datetime import datetime
    from uuid import UUID, uuid4

    class SessionConfig(BaseModel):
        max_api_calls: int = 50
        max_budget_usd: float = 5.0

    class AuditEntry(BaseModel):
        timestamp: datetime = datetime.now()
        event_type: str
        payload_hash: str
        prev_hash: str | None = None
    ```

    Use `str | None` (Python 3.10+ union syntax) not `Optional[str]` — project targets 3.12+.
  </action>
  <verify>
    uv sync discovers centinela-core in workspace (no "package not found" errors)
    python -c "from centinela.models import SessionConfig, AuditEntry" (imports work)
  </verify>
  <done>
    centinela-core package is installable as editable workspace member. Models module imports without errors.
  </done>
</task>

<task type="auto">
  <name>Task 3: Five service containers — stubs and test infrastructure</name>
  <files>
    services/red-agent/pyproject.toml
    services/red-agent/src/red_agent/__init__.py
    services/red-agent/src/red_agent/main.py
    services/red-agent/tests/__init__.py
    services/red-agent/tests/test_stub.py
    services/orchestrator/pyproject.toml
    services/orchestrator/src/orchestrator/__init__.py
    services/orchestrator/src/orchestrator/main.py
    services/orchestrator/tests/__init__.py
    services/orchestrator/tests/test_stub.py
    services/blue-agent/pyproject.toml
    services/blue-agent/src/blue_agent/__init__.py
    services/blue-agent/src/blue_agent/main.py
    services/blue-agent/tests/__init__.py
    services/blue-agent/tests/test_stub.py
    services/llm-sandbox/pyproject.toml
    services/llm-sandbox/src/llm_sandbox/__init__.py
    services/llm-sandbox/src/llm_sandbox/main.py
    services/llm-sandbox/tests/__init__.py
    services/llm-sandbox/tests/test_stub.py
    services/audit/pyproject.toml
    services/audit/src/audit/__init__.py
    services/audit/src/audit/main.py
    services/audit/tests/__init__.py
    services/audit/tests/test_stub.py
  </files>
  <action>
    Create 5 service directories with identical structure pattern. Each service has:

    **pyproject.toml** (service-specific name and description):
    ```toml
    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"

    [project]
    name = "{service_name}"        # e.g., "red-agent", "orchestrator", "blue-agent", "llm-sandbox", "audit"
    version = "0.1.0"
    description = "{Service description}"  # See descriptions below
    requires-python = ">=3.12"
    dependencies = [
        "centinela-core",
    ]
    ```
    Service descriptions:
    - red-agent: "Red agent service — adversarial prompt generation and attack execution"
    - orchestrator: "Orchestrator service — session lifecycle, provider routing, and container coordination"
    - blue-agent: "Blue agent service — safety evaluation and response classification"
    - llm-sandbox: "LLM sandbox service — isolated model interaction and output sanitization"
    - audit: "Audit service — tamper-evident cryptographic logging and certificate generation"

    **src/{python_package}/__init__.py** (empty with docstring):
    ```python
    """{Service name} service for CENTINELA."""
    ```

    **src/{python_package}/main.py** (stub with entry point):
    ```python
    def main() -> None:
        print("Hello from centinela-{service_name}!")

    if __name__ == "__main__":
        main()
    ```

    **tests/__init__.py** (empty file — enables pytest discovery):
    ```python
    """Tests for centinela-{service_name}."""
    ```

    **tests/test_stub.py** (minimal test that imports the package):
    ```python
    from {python_package} import main

    def test_main() -> None:
        """Verify the module can be imported and main runs without error."""
        main.main()
    ```

    Service name mapping (CLI arg → directory name → Python package name):
    | Directory        | Python package   | pyproject.toml name |
    |------------------|------------------|---------------------|
    | red-agent        | red_agent        | red-agent           |
    | orchestrator     | orchestrator     | orchestrator        |
    | blue-agent       | blue_agent       | blue-agent          |
    | llm-sandbox      | llm_sandbox      | llm-sandbox         |
    | audit            | audit            | audit               |

    IMPORTANT: Directories use hyphens, Python packages use underscores. This is normal for Python packaging — setuptools/hatchling handle the conversion when defining [project] name with hyphens and having src/ with underscores.
  </action>
  <verify>
    uv sync succeeds (discovers all 5 services as workspace members)
    uv run pytest -n auto --cov=services --cov=packages --cov-report=term-missing (all 5 test stubs discovered, >80% coverage)
    uv run mypy services/ packages/ (zero type errors)
  </verify>
  <done>
    All 5 services importable. Test discovery finds 5+ tests. Coverage >80%. Mypy strict mode passes.
  </done>
</task>

</tasks>

<verification>
Run the following in sequence:

```bash
# 1. Install dependencies and generate lockfile
uv sync

# 2. Lint check — must be zero errors
ruff check .

# 3. Format check — must require zero changes
ruff format --check .

# 4. Type check — strict mode must pass with zero errors
uv run mypy services/ packages/

# 5. Test + coverage — all stubs discovered, >80% coverage
uv run pytest -n auto --cov=services --cov=packages --cov-report=term-missing
```

All 5 steps must succeed. If any step fails, fix the underlying issue (likely a misconfigured pyproject.toml or missing __init__.py) and retry.
</verification>

<success_criteria>
- `ruff check .` returns exit code 0 with zero lint errors
- `ruff format --check .` returns exit code 0
- `uv run mypy services/ packages/` returns exit code 0
- `uv run pytest` discovers and passes all 5 test_stub.py files (5+ tests)
- `uv run pytest --cov=services --cov=packages` reports >80% coverage
- `uv sync` generates uv.lock without warnings
- All 30 files listed in files_modified exist on disk with correct content
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation/01-foundation-01-SUMMARY.md`
</output>
