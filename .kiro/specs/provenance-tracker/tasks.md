# Implementation Plan: Provenance Tracker

## Overview

Extend the existing stub in `packages/centinela-core/src/centinela/provenance/tracker.py` with a typed Pydantic v2 model, structured exceptions, a maintained children index, full-subgraph boundary crossing detection, cycle detection with atomicity, JSON serialization/deserialization, and type-based querying. Tests live in `packages/centinela-core/tests/provenance/`.

## Tasks

- [ ] 1. Define exceptions and typed models
  - [ ] 1.1 Create `packages/centinela-core/src/centinela/provenance/exceptions.py` with the `ProvenanceError` base class and `DuplicateArtifactError`, `UnknownParentError`, `CycleDetectedError`, `DeserializationError` subclasses
    - _Requirements: 1.3, 1.4, 1.5, 5.1, 5.2, 6.3, 6.4_
  - [ ] 1.2 Replace the plain `ProvenanceNode` class in `tracker.py` with a Pydantic v2 `BaseModel` (frozen, UTC `created_at`, typed `metadata`, typed `parents`)
    - _Requirements: 1.1, 1.6_
  - [ ] 1.3 Add `BoundaryCrossing` Pydantic v2 model to `tracker.py` (fields: `from_node`, `to_node`, `from_boundary`, `to_boundary`, `boundary_key`)
    - _Requirements: 4.1_
  - [ ] 1.4 Export all new public names from `packages/centinela-core/src/centinela/provenance/__init__.py`
    - _Requirements: 1.1_

- [ ] 2. Rewrite `ProvenanceTracker` core with children index and cycle detection
  - [ ] 2.1 Replace the single `_graph` dict with `_nodes: dict[str, ProvenanceNode]` and `_children: dict[str, set[str]]`; update `add_artifact` to maintain both structures
    - _Requirements: 1.1, 1.2_
  - [ ] 2.2 Implement `_would_create_cycle(new_id, parents)` private method using iterative DFS over `_nodes` parent links; raise `CycleDetectedError` before any mutation if a cycle is detected
    - _Requirements: 1.5, 5.1, 5.2, 5.3_
  - [ ] 2.3 Add duplicate-ID and unknown-parent validation to `add_artifact`, raising `DuplicateArtifactError` and `UnknownParentError` respectively
    - _Requirements: 1.3, 1.4_
  - [ ]* 2.4 Write property test for add-then-retrieve round trip (Property 1)
    - **Property 1: Add-then-retrieve round trip**
    - **Validates: Requirements 1.1, 1.2, 8.3**
  - [ ]* 2.5 Write property test for cycle detection atomicity (Property 5)
    - **Property 5: Cycle detection with atomicity**
    - **Validates: Requirements 1.5, 5.1, 5.2, 5.3**
  - [ ]* 2.6 Write unit tests for `add_artifact` error conditions (duplicate ID, unknown parent, self-loop, indirect cycle)
    - _Requirements: 1.3, 1.4, 1.5, 5.1, 5.2_

- [ ] 3. Implement iterative `trace_backward` and `trace_forward`
  - [ ] 3.1 Rewrite `trace_backward` using an explicit stack (iterative DFS over parent links); return empty list for unknown IDs
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [ ] 3.2 Rewrite `trace_forward` using an explicit stack (iterative DFS over `_children` index); return empty list for unknown IDs
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  - [ ]* 3.3 Write property test for backward trace completeness and no duplicates (Property 2)
    - **Property 2: Backward trace completeness and no duplicates**
    - **Validates: Requirements 2.1, 2.4**
  - [ ]* 3.4 Write property test for forward trace completeness and no duplicates (Property 3)
    - **Property 3: Forward trace completeness and no duplicates**
    - **Validates: Requirements 3.1, 3.4**
  - [ ]* 3.5 Write property test for backward/forward trace symmetry (Property 4)
    - **Property 4: Backward/forward trace symmetry**
    - **Validates: Requirements 2.1, 3.1**
  - [ ]* 3.6 Write unit tests for edge cases: empty graph, single root node, single leaf node, diamond graph

- [ ] 4. Checkpoint — ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement full-subgraph boundary crossing detection
  - [ ] 5.1 Rewrite `get_isolation_boundary_crossings` to walk the full ancestor subgraph via `trace_backward`, check every edge for boundary value differences (treating absent keys as `None`), and deduplicate crossings using a `seen_edges` set; return `list[BoundaryCrossing]`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - [ ]* 5.2 Write property test for boundary crossing completeness and deduplication (Property 6)
    - **Property 6: Boundary crossing completeness and deduplication**
    - **Validates: Requirements 4.1, 4.4, 4.5**
  - [ ]* 5.3 Write unit tests for boundary crossing edge cases: no crossings, missing boundary key on one side, diamond graph with shared crossing edge, unknown artifact ID

- [ ] 6. Implement `get_node` and `get_by_type`
  - [ ] 6.1 Implement `get_node(artifact_id) -> ProvenanceNode | None` returning the node or `None`
    - _Requirements: 8.3, 8.4_
  - [ ] 6.2 Implement `get_by_type(artifact_type: str) -> list[ProvenanceNode]` with exact case-sensitive matching
    - _Requirements: 7.1, 7.2, 7.3_
  - [ ]* 6.3 Write property test for type query exactness (Property 8)
    - **Property 8: Type query exactness**
    - **Validates: Requirements 7.1, 7.3**
  - [ ]* 6.4 Write unit tests for `get_by_type` case-sensitivity and empty-result cases

- [ ] 7. Implement JSON serialization and deserialization
  - [ ] 7.1 Implement `to_json(self) -> str` — emit nodes in topological order (parents before children) as a JSON object `{"nodes": [...]}` with ISO 8601 UTC timestamps
    - _Requirements: 6.1, 6.5, 6.6_
  - [ ] 7.2 Implement `from_json(cls, data: str) -> ProvenanceTracker` — parse the JSON, reconstruct nodes in list order via `add_artifact`, raise `DeserializationError` on malformed JSON and `CycleDetectedError` on cyclic data
    - _Requirements: 6.2, 6.3, 6.4_
  - [ ]* 7.3 Write property test for serialization round trip (Property 7)
    - **Property 7: Serialization round trip**
    - **Validates: Requirements 6.1, 6.2, 6.5, 6.6**
  - [ ]* 7.4 Write unit tests for `from_json` error conditions: malformed JSON, cyclic JSON, missing required fields

- [ ] 8. Write graph structural integrity property test and Hypothesis strategies
  - [ ] 8.1 Create `packages/centinela-core/tests/provenance/__init__.py` and `test_tracker_properties.py`; implement the `dag_strategy` and `node_spec_strategy` Hypothesis composite strategies
    - _Requirements: 8.1, 8.2_
  - [ ]* 8.2 Write property test for graph structural integrity invariant (Property 9)
    - **Property 9: Graph structural integrity invariant**
    - **Validates: Requirements 8.1, 8.2**

- [ ] 9. Final checkpoint — ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Property tests use `hypothesis` with `@settings(max_examples=200)` for critical properties
- All property tests must carry a comment: `# Feature: provenance-tracker, Property N: <title>`
- The existing stub's `trace_backward` and `trace_forward` use recursion — replace with iterative DFS to avoid stack overflow on deep lineage chains
