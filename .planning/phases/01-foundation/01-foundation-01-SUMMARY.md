---
plan: 01-foundation-01
phase: 01-foundation
wave: 1
status: completed
duration: ~45 min
task_count: 3
---

# Plan 01-SUMMARY: Project Skeleton

## What Was Built

Complete Python monorepo skeleton for the CENTINELA platform:
- **Root pyproject.toml** — uv workspace, hatchling build, ruff/mypy/pytest tool configs
- **centinela-core** — shared package with `SessionConfig` and `AuditEntry` pydantic models
- **5 service containers** — red-agent, orchestrator, blue-agent, llm-sandbox, audit (each with pyproject.toml, src/ layout, tests/)

## Key Files Created

| Path | Purpose |
|------|---------|
| `pyproject.toml` | Root workspace + tooling config |
| `.gitignore` | Standard Python/IDE/OS gitignore |
| `packages/centinela-core/` | Shared models (SessionConfig, AuditEntry) |
| `services/{5 containers}/` | Each: pyproject.toml, src/, tests/ |

## Verification Results

| Check | Result |
|-------|--------|
| `ruff check .` | ✅ All checks passed |
| `ruff format --check .` | ✅ 17 files already formatted |
| `mypy packages/ services/` | ✅ Success: no issues in 12 files |
| `pytest -n auto --cov` | ✅ 5/5 passed, 86% coverage |

## Decisions Made

- **Python package naming**: Directories use hyphens (e.g., `red-agent`), Python packages use underscores (`red_agent`). Hatchling handles the conversion.
- **Test naming**: Each service gets a unique test filename (`test_red_agent.py`, etc.) instead of generic `test_stub.py` to avoid pytest import conflicts.
- **Test `__init__.py` removed**: pytest 9 doesn't need them for discovery, and they caused mypy "duplicate module" errors.
- **Mypy exclude**: Added `exclude = "tests/"` to prevent test directory duplicate module issues.
- **`uv sync --all-extras`**: Required to install dev dependencies (pytest, ruff, mypy, pre-commit) since they're defined as `[project.optional-dependencies]`.

## Deviations from Plan

1. **Test file names**: Changed from `test_stub.py` to `test_{service_name}.py` to fix pytest import file mismatch.
2. **Removed test `__init__.py`**: Files removed to fix mypy duplicate module errors and pytest import conflicts.
3. **Mypy config**: Added `exclude = "tests/"` to prevent duplicate module errors.

## Next

Plan 02 depends on this. Proceeding to Wave 2.
