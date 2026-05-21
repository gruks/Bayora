# Requirements Document

## Introduction

The Provenance Tracker is a forensic data lineage component for the CENTINELA AI safety validation platform. It maintains a directed acyclic graph (DAG) of artifacts produced during validation sessions, enabling auditors to trace any artifact back to its origin, enumerate all derivatives of a given artifact, detect when data crosses isolation boundaries (tenant, namespace, container), and export the full lineage graph for offline forensic analysis. The tracker extends the existing in-memory stub with cycle detection, full-graph boundary crossing detection, JSON serialization, and type-based querying.

## Glossary

- **Artifact**: Any discrete data object tracked by the platform (prompt, response, dataset, evaluation result, session record, etc.).
- **Artifact_ID**: A unique string identifier for an artifact within the provenance graph.
- **Artifact_Type**: A string label categorising an artifact (e.g. `"prompt"`, `"response"`, `"evaluation"`).
- **ProvenanceNode**: A graph node representing one artifact, holding its ID, type, metadata, parent list, and creation timestamp.
- **ProvenanceTracker**: The component responsible for managing the provenance graph and all lineage queries.
- **Parent**: An artifact from which another artifact was directly derived.
- **Ancestor**: Any artifact reachable by following parent links transitively from a given artifact.
- **Descendant**: Any artifact reachable by following child links transitively from a given artifact.
- **Isolation_Boundary**: A metadata key whose value identifies a security or tenancy domain (e.g. `"tenant_id"`, `"namespace"`, `"container_id"`).
- **Boundary_Crossing**: An edge in the provenance graph where the parent and child nodes carry different values for the same Isolation_Boundary key.
- **Lineage_Graph**: The complete set of ProvenanceNodes and their parent-child edges managed by a ProvenanceTracker instance.
- **Serialized_Graph**: A JSON representation of the Lineage_Graph suitable for persistence and import.

---

## Requirements

### Requirement 1: Artifact Registration

**User Story:** As a CENTINELA platform component, I want to register artifacts with their parent relationships, so that a complete lineage graph is built incrementally during a validation session.

#### Acceptance Criteria

1. WHEN `add_artifact` is called with a unique `artifact_id`, `artifact_type`, optional `metadata`, and optional `parents` list, THE `ProvenanceTracker` SHALL create a `ProvenanceNode` and store it in the graph.
2. WHEN `add_artifact` is called with a `parents` list containing one or more IDs, THE `ProvenanceTracker` SHALL record those IDs as the node's parents.
3. WHEN `add_artifact` is called with an `artifact_id` that already exists in the graph, THE `ProvenanceTracker` SHALL raise a `DuplicateArtifactError`.
4. WHEN `add_artifact` is called with a `parents` list containing an ID not present in the graph, THE `ProvenanceTracker` SHALL raise an `UnknownParentError`.
5. WHEN `add_artifact` is called with a `parents` list that would introduce a cycle into the graph, THE `ProvenanceTracker` SHALL raise a `CycleDetectedError` and leave the graph unchanged.
6. THE `ProvenanceTracker` SHALL record a UTC timestamp on each `ProvenanceNode` at the moment `add_artifact` is called.

---

### Requirement 2: Backward Tracing

**User Story:** As a forensic auditor, I want to trace any artifact back to its full origin chain, so that I can determine the complete provenance of any platform output.

#### Acceptance Criteria

1. WHEN `trace_backward` is called with a valid `artifact_id`, THE `ProvenanceTracker` SHALL return the set of all ancestor `ProvenanceNode`s reachable by following parent links transitively, including the node itself.
2. WHEN `trace_backward` is called with an `artifact_id` not present in the graph, THE `ProvenanceTracker` SHALL return an empty list.
3. WHEN `trace_backward` is called on a root artifact (one with no parents), THE `ProvenanceTracker` SHALL return a list containing only that node.
4. WHILE the graph contains a diamond-shaped dependency (two paths converge on a common ancestor), THE `ProvenanceTracker` SHALL include that common ancestor exactly once in the backward trace result.

---

### Requirement 3: Forward Tracing

**User Story:** As a forensic auditor, I want to enumerate all artifacts derived from a given artifact, so that I can assess the blast radius of a compromised or tainted input.

#### Acceptance Criteria

1. WHEN `trace_forward` is called with a valid `artifact_id`, THE `ProvenanceTracker` SHALL return the set of all descendant `ProvenanceNode`s reachable by following child links transitively, including the node itself.
2. WHEN `trace_forward` is called with an `artifact_id` not present in the graph, THE `ProvenanceTracker` SHALL return an empty list.
3. WHEN `trace_forward` is called on a leaf artifact (one with no children), THE `ProvenanceTracker` SHALL return a list containing only that node.
4. WHILE the graph contains a diamond-shaped dependency (one ancestor has two paths to a common descendant), THE `ProvenanceTracker` SHALL include that common descendant exactly once in the forward trace result.

---

### Requirement 4: Isolation Boundary Crossing Detection

**User Story:** As a security auditor, I want to detect when data crosses tenant, namespace, or container boundaries anywhere in the lineage graph, so that I can identify potential data exfiltration or policy violations.

#### Acceptance Criteria

1. WHEN `get_isolation_boundary_crossings` is called with a valid `artifact_id` and a `boundary` key, THE `ProvenanceTracker` SHALL return all edges in the full ancestor subgraph where the parent and child nodes carry different values for that `boundary` key.
2. WHEN `get_isolation_boundary_crossings` is called and no boundary crossings exist in the ancestor subgraph, THE `ProvenanceTracker` SHALL return an empty list.
3. WHEN `get_isolation_boundary_crossings` is called with an `artifact_id` not present in the graph, THE `ProvenanceTracker` SHALL return an empty list.
4. WHEN a node or its parent does not carry the specified `boundary` key in its metadata, THE `ProvenanceTracker` SHALL treat the missing value as a distinct boundary value (i.e. `None` is not equal to any string value).
5. WHEN `get_isolation_boundary_crossings` is called on a graph with a diamond-shaped dependency containing a crossing, THE `ProvenanceTracker` SHALL report that crossing exactly once.

---

### Requirement 5: Cycle Detection

**User Story:** As a platform engineer, I want the provenance graph to remain acyclic at all times, so that tracing operations always terminate and the lineage is logically consistent.

#### Acceptance Criteria

1. WHEN `add_artifact` is called with a `parents` list that would create a direct self-reference (`artifact_id` in `parents`), THE `ProvenanceTracker` SHALL raise a `CycleDetectedError`.
2. WHEN `add_artifact` is called with a `parents` list that would create an indirect cycle (the new node is already an ancestor of one of its proposed parents), THE `ProvenanceTracker` SHALL raise a `CycleDetectedError`.
3. WHEN a `CycleDetectedError` is raised, THE `ProvenanceTracker` SHALL leave the graph in its prior state with no partial modifications.

---

### Requirement 6: JSON Serialization and Deserialization

**User Story:** As a forensic analyst, I want to export and import the full provenance graph as JSON, so that lineage data can be persisted to disk, transmitted, and reconstructed for offline analysis.

#### Acceptance Criteria

1. WHEN `to_json` is called on a `ProvenanceTracker` instance, THE `ProvenanceTracker` SHALL return a JSON string encoding all nodes, their metadata, parent lists, and timestamps.
2. WHEN `from_json` is called with a valid JSON string produced by `to_json`, THE `ProvenanceTracker` SHALL reconstruct a `ProvenanceTracker` instance whose graph is equivalent to the original.
3. WHEN `from_json` is called with a JSON string containing a cycle, THE `ProvenanceTracker` SHALL raise a `CycleDetectedError`.
4. WHEN `from_json` is called with malformed JSON, THE `ProvenanceTracker` SHALL raise a `DeserializationError`.
5. THE `ProvenanceTracker` SHALL preserve `created_at` timestamps exactly (to millisecond precision) through a serialization round-trip.
6. THE `ProvenanceTracker` SHALL preserve all metadata key-value pairs exactly through a serialization round-trip.

---

### Requirement 7: Query by Artifact Type

**User Story:** As a platform analyst, I want to retrieve all artifacts of a given type from the provenance graph, so that I can audit all prompts, responses, or evaluations produced during a session.

#### Acceptance Criteria

1. WHEN `get_by_type` is called with a valid `artifact_type` string, THE `ProvenanceTracker` SHALL return a list of all `ProvenanceNode`s whose `artifact_type` matches that string exactly.
2. WHEN `get_by_type` is called with an `artifact_type` that matches no nodes, THE `ProvenanceTracker` SHALL return an empty list.
3. THE `ProvenanceTracker` SHALL treat `artifact_type` matching as case-sensitive.

---

### Requirement 8: Graph Integrity Invariants

**User Story:** As a platform engineer, I want the provenance graph to maintain structural integrity at all times, so that all queries return consistent and correct results.

#### Acceptance Criteria

1. THE `ProvenanceTracker` SHALL ensure that every parent ID referenced by any node in the graph corresponds to an existing node in the graph.
2. THE `ProvenanceTracker` SHALL ensure that the graph remains acyclic after every `add_artifact` call.
3. WHEN `get_node` is called with a valid `artifact_id`, THE `ProvenanceTracker` SHALL return the corresponding `ProvenanceNode`.
4. WHEN `get_node` is called with an `artifact_id` not present in the graph, THE `ProvenanceTracker` SHALL return `None`.
