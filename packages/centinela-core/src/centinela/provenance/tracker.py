"""Provenance tracker for data lineage and artifact tracking."""

from datetime import datetime
from typing import Any


class ProvenanceNode:
    """Represents a single artifact in the provenance graph."""

    def __init__(
        self,
        artifact_id: str,
        artifact_type: str,
        metadata: dict[str, Any],
        parents: list[str],
        created_at: datetime | None = None,
    ):
        self.artifact_id = artifact_id
        self.artifact_type = artifact_type
        self.metadata = metadata
        self.parents = parents
        self.created_at = created_at or datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "metadata": self.metadata,
            "parents": self.parents,
            "created_at": self.created_at.isoformat(),
        }


class ProvenanceTracker:
    """Tracks artifact lineage using a directed acyclic graph (DAG)."""

    def __init__(self):
        # Adjacency list: artifact_id -> ProvenanceNode
        self._graph: dict[str, ProvenanceNode] = {}
        # Reverse adjacency for forward tracing: artifact_id -> list of children
        self._reverse: dict[str, list[str]] = {}

    def add_artifact(
        self,
        artifact_id: str,
        artifact_type: str,
        metadata: dict[str, Any] | None = None,
        parents: list[str] | None = None,
    ) -> ProvenanceNode:
        """Add a new artifact to the provenance graph."""
        if metadata is None:
            metadata = {}
        if parents is None:
            parents = []

        # Validate parent references exist
        for parent_id in parents:
            if parent_id not in self._graph:
                raise ValueError(f"Parent artifact '{parent_id}' does not exist")

        node = ProvenanceNode(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            metadata=metadata,
            parents=parents,
        )

        self._graph[artifact_id] = node
        self._reverse[artifact_id] = []

        # Update reverse adjacency
        for parent_id in parents:
            self._reverse[parent_id].append(artifact_id)

        return node

    def get_artifact(self, artifact_id: str) -> ProvenanceNode | None:
        """Get an artifact by ID."""
        return self._graph.get(artifact_id)

    def trace_backward(self, artifact_id: str) -> list[ProvenanceNode]:
        """Trace lineage backward to origin following parent links."""
        if artifact_id not in self._graph:
            return []

        result: list[ProvenanceNode] = []
        visited: set[str] = set()
        queue = [artifact_id]

        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)

            node = self._graph.get(current_id)
            if node:
                result.append(node)
                # Add parents to queue
                for parent_id in node.parents:
                    if parent_id not in visited:
                        queue.append(parent_id)

        return result

    def trace_forward(self, artifact_id: str) -> list[ProvenanceNode]:
        """Find all artifacts derived from the given artifact."""
        if artifact_id not in self._graph:
            return []

        result: list[ProvenanceNode] = []
        visited: set[str] = set()
        queue = [artifact_id]

        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)

            # Get children from reverse adjacency
            children = self._reverse.get(current_id, [])
            for child_id in children:
                if child_id not in visited:
                    node = self._graph.get(child_id)
                    if node:
                        result.append(node)
                        queue.append(child_id)

        return result

    def get_isolation_boundary_crossings(
        self, artifact_id: str, boundary: str = "tenant"
    ) -> list[dict[str, Any]]:
        """Detect when an artifact crosses isolation boundaries."""
        if artifact_id not in self._graph:
            return []

        node = self._graph[artifact_id]
        boundary_key = f"{boundary}_id"
        crossings: list[dict[str, Any]] = []

        # Check current artifact's boundary
        current_boundary = node.metadata.get(boundary_key)

        # Trace backward to check boundary changes
        lineage = self.trace_backward(artifact_id)
        for ancestor in lineage:
            ancestor_boundary = ancestor.metadata.get(boundary_key)
            if ancestor_boundary and ancestor_boundary != current_boundary:
                crossings.append(
                    {
                        "artifact_id": ancestor.artifact_id,
                        "from_boundary": ancestor_boundary,
                        "to_boundary": current_boundary,
                        "direction": "backward",
                    }
                )

        # Trace forward to check boundary changes
        derived = self.trace_forward(artifact_id)
        for descendant in derived:
            descendant_boundary = descendant.metadata.get(boundary_key)
            if descendant_boundary and descendant_boundary != current_boundary:
                crossings.append(
                    {
                        "artifact_id": descendant.artifact_id,
                        "from_boundary": current_boundary,
                        "to_boundary": descendant_boundary,
                        "direction": "forward",
                    }
                )

        return crossings

    def __len__(self) -> int:
        return len(self._graph)

    def __contains__(self, artifact_id: str) -> bool:
        return artifact_id in self._graph


__all__ = ["ProvenanceNode", "ProvenanceTracker"]
