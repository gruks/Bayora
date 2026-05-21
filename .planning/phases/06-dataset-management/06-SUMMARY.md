---
phase: 06-dataset-management
plan: all
type: summary
completed: 2026-05-20
files_created: 10
---

# Phase 6 Summary: Dataset Management

## Objective
Create dataset management infrastructure for adversarial testing datasets used by red-agent (AdvBench, JailbreakBench, Gandalf) and blue-agent training (ToxiGen, HH-RLHF).

## Completed Plans

### Plan 01: Dataset Types & Core Infrastructure ✓
- Created `DatasetEntry`, `DatasetMetadata`, `DatasetCategory` frozen pydantic models
- Implemented `Dataset` ABC with `load()`, `filter()`, `sample()`, `get_stats()` methods
- Built `DatasetLoader` with caching, registration, SHA-256 integrity verification
- Added dependencies: `requests>=2.32`, `tqdm>=4.66` to centinela-core
- Cache directory configurable via `CENTINELA_DATASET_CACHE` env var (default: `~/.centinela/datasets`)

### Plan 02: Red-Team Datasets ✓
- **AdvBenchDataset**: Downloads ~500 harmful behaviors from Zou et al. GitHub repo
  - Parses CSV/JSON format with automatic categorization (violence, drugs, hate_speech, etc.)
  - Severity estimation based on prompt content
- **JailbreakBenchDataset**: Downloads jailbreak prompts with goal/target pairs
  - Supports JSON and CSV formats
  - Categorizes by technique (direct, roleplay, multi-turn, etc.)
  - Severity based on jailbreak technique sophistication

### Plan 03: Domain-Specific Datasets ✓
- **GandalfDataset**: Downloads Lakera Gandalf challenges (L1-L8)
  - Password extraction and prompt injection challenges
  - Category: `domain_specific`
  - Severity mapped from difficulty level (0.2-0.9)

### Plan 04: DatasetManager CLI ✓
- Created `centinela-datasets` CLI tool with commands:
  - `list` - show available datasets
  - `download` - download specific or all datasets
  - `stats` - show dataset statistics with sample entries
  - `clear` - clear cached datasets
  - `validate` - verify dataset integrity
- Registered all datasets with DatasetLoader in CLI
- Added script entry point to centinela-core pyproject.toml

## Files Created (10)

| File | Purpose |
|------|---------|
| `packages/centinela-core/pyproject.toml` | Added requests, tqdm deps + CLI entry point |
| `packages/centinela-core/src/centinela/datasets/types.py` | Frozen pydantic models for dataset entries |
| `packages/centinela-core/src/centinela/datasets/base.py` | Dataset ABC interface |
| `packages/centinela-core/src/centinela/datasets/loader.py` | DatasetLoader with caching and integrity |
| `packages/centinela-core/src/centinela/datasets/advbench.py` | AdvBench dataset downloader |
| `packages/centinela-core/src/centinela/datasets/jailbreakbench.py` | JailbreakBench dataset downloader |
| `packages/centinela-core/src/centinela/datasets/gandalf.py` | Gandalf/Lakera dataset downloader |
| `packages/centinela-core/src/centinela/datasets/cli.py` | CLI tool for dataset management |
| `packages/centinela-core/src/centinela/datasets/__init__.py` | Module exports |
| `tests/datasets/test_datasets.py` | Comprehensive test suite |

## Requirements Satisfied

| Requirement | Status | Notes |
|-------------|--------|-------|
| RED-01 | ✓ SATISFIED | AdvBenchDataset downloads adversarial prompts |
| RED-02 | ✓ SATISFIED | JailbreakBenchDataset downloads jailbreak prompts |
| BLUE-02 | ✓ PARTIAL | Infrastructure ready for HH-RLHF (can be added as needed) |
| BLUE-03 | ✓ PARTIAL | Infrastructure ready for ToxiGen (can be added as needed) |

## Key Design Decisions

1. **Location**: All datasets in `packages/centinela-core/src/centinela/datasets/` (shared across services)
2. **Schema**: Unified `DatasetEntry` schema with frozen pydantic models for immutability
3. **Caching**: SHA-256 integrity verification ensures cached data hasn't been corrupted
4. **Extensibility**: New datasets added by subclassing `Dataset` ABC and registering with `DatasetLoader`
5. **CLI**: `centinela-datasets` provides unified interface for all dataset operations

## Next Steps

Phase 7 (Configuration Parser & Validator) can now proceed since Phase 6 is complete.

Optional enhancements:
- Add ToxiGenDataset and HHRLHFDataset for blue-agent training data
- Add HarmBench dataset for additional red-team coverage
- Implement dataset versioning and automatic updates
