"""Provenance tracker for data lineage."""

from datetime import datetime
from typing import Any


class ProvenanceNode:
    """A node in the provenance graph representing an artifact."""

    def __init__(
        self,
        artifact_id: str,
        artifact_type: str,
        metadata: dict[str, Any],
        parents: list[str],
    ) -> None:
        self.artifact_id = artifact_id
        self.artifact_type = artifact_type
        self.metadata = metadata
        self.parents = parents
        self.created_at = datetime.now()


class ProvenanceTracker:
    """Tracker for maintaining data lineage and provenance graphs."""

    def __init__(self) -> None:
        """Initialize the provenance tracker."""
        self._graph: dict[str, ProvenanceNode] = {}

    def add_artifact(
        self,
        artifact_id: str,
        artifact_type: str,
        metadata: dict[str, Any] | None = None,
        parents: list[str] | None = None,
    ) -> ProvenanceNode:
        """Add an artifact to the provenance graph."""
        metadata_dict = metadata or {}
        parents_list = parents or []
        node = ProvenanceNode(artifact_id, artifact_type, metadata_dict, parents_list)
        self._graph[artifact_id] = node
        return node

    def trace_backward(self, artifact_id: str) -> list[ProvenanceNode]:
        """Follow parent links to origin and return the full backward trace."""
        if artifact_id not in self._graph:
            return []

        result: list[ProvenanceNode] = []
        visited: set[str] = set()

        def dfs(curr_id: str) -> None:
            if curr_id in visited or curr_id not in self._graph:
                return
            visited.add(curr_id)
            node = self._graph[curr_id]
            result.append(node)
            for parent_id in node.parents:
                dfs(parent_id)

        dfs(artifact_id)
        return result

    def trace_forward(self, artifact_id: str) -> list[ProvenanceNode]:
        """Find all artifacts derived from the given artifact."""
        if artifact_id not in self._graph:
            return []

        result: list[ProvenanceNode] = []
        visited: set[str] = set()

        # Build child index
        children: dict[str, list[str]] = {node_id: [] for node_id in self._graph}
        for node_id, node in self._graph.items():
            for parent_id in node.parents:
                if parent_id in children:
                    children[parent_id].append(node_id)

        def dfs(curr_id: str) -> None:
            if curr_id in visited:
                return
            visited.add(curr_id)
            if curr_id in self._graph:
                result.append(self._graph[curr_id])
            for child_id in children.get(curr_id, []):
                dfs(child_id)

        dfs(artifact_id)
        return result

    def get_isolation_boundary_crossings(
        self, artifact_id: str, boundary: str
    ) -> list[dict[str, Any]]:
        """Detect when an artifact crosses a specified tenant/namespace boundary."""
        crossings: list[dict[str, Any]] = []
        node = self._graph.get(artifact_id)
        if not node:
            return crossings

        target_boundary = node.metadata.get(boundary)

        for parent_id in node.parents:
            parent = self._graph.get(parent_id)
            if parent and parent.metadata.get(boundary) != target_boundary:
                crossings.append(
                    {
                        "from_node": parent.artifact_id,
                        "to_node": artifact_id,
                        "from_boundary": parent.metadata.get(boundary),
                        "to_boundary": target_boundary,
                        "boundary_key": boundary,
                    }
                )

        return crossings
