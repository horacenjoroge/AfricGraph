"""Restore functionality for time-travel queries."""
from datetime import datetime
from typing import Optional, Dict, Any, List

from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.logging import get_logger
from src.temporal.queries import TemporalQueryEngine
from src.temporal.snapshots import SnapshotManager

logger = get_logger(__name__)


class RestoreManager:
    """Manages restoration of graph to previous states."""

    def __init__(self):
        """Initialize restore manager."""
        self.query_engine = TemporalQueryEngine()
        self.snapshot_manager = SnapshotManager()

    def restore_to_timestamp(
        self,
        timestamp: datetime,
        node_ids: Optional[List[str]] = None,
        relationship_ids: Optional[List[str]] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Restore graph to a specific point in time.

        Args:
            timestamp: Point in time to restore to
            node_ids: Optional list of node IDs to restore (all if None)
            relationship_ids: Optional list of relationship IDs to restore (all if None)
            dry_run: If True, only simulate restore without making changes

        Returns:
            Dictionary with restore statistics
        """
        logger.info("Starting restore to timestamp", timestamp=timestamp, dry_run=dry_run)

        # Query graph state at timestamp
        result = self.query_engine.query_at_time(
            timestamp=timestamp,
            node_ids=node_ids,
            relationship_ids=relationship_ids,
        )

        if dry_run:
            return {
                "timestamp": timestamp,
                "nodes_to_restore": result.total_nodes,
                "relationships_to_restore": result.total_relationships,
                "dry_run": True,
            }

        # Restore nodes
        nodes_restored = self._restore_nodes(result.nodes)

        # Restore relationships
        relationships_restored = self._restore_relationships(result.relationships)

        logger.info("Restore completed", timestamp=timestamp, nodes=nodes_restored, relationships=relationships_restored)

        return {
            "timestamp": timestamp,
            "nodes_restored": nodes_restored,
            "relationships_restored": relationships_restored,
            "status": "completed",
        }

    def restore_from_snapshot(
        self,
        snapshot_id: str,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Restore graph from a snapshot.

        Args:
            snapshot_id: Snapshot ID to restore from
            dry_run: If True, only simulate restore

        Returns:
            Dictionary with restore statistics
        """
        snapshot = self.snapshot_manager.get_snapshot(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot not found: {snapshot_id}")

        return self.restore_to_timestamp(
            timestamp=snapshot.timestamp,
            dry_run=dry_run,
        )

    def _restore_nodes(self, nodes: List) -> int:
        """Restore nodes to Neo4j."""
        restored = 0
        for node in nodes:
            try:
                # Merge node with versioned properties
                props = {**node.properties, "_temporal_version": node.version, "_temporal_valid_from": node.valid_from.isoformat()}
                if node.valid_to:
                    props["_temporal_valid_to"] = node.valid_to.isoformat()

                # Use merge_node with proper signature: (label, id_val, props)
                label = node.labels[0] if node.labels else "Node"
                neo4j_client.merge_node(
                    label=label,
                    id_val=node.node_id,
                    props=props,
                )
                restored += 1
            except Exception as e:
                logger.exception("Failed to restore node", node_id=node.node_id, error=str(e))

        return restored

    def _restore_relationships(self, relationships: List) -> int:
        """Restore relationships to Neo4j."""
        restored = 0
        for rel in relationships:
            try:
                # Create relationship with versioned properties
                props = {**rel.properties, "_temporal_version": rel.version, "_temporal_valid_from": rel.valid_from.isoformat()}
                if rel.valid_to:
                    props["_temporal_valid_to"] = rel.valid_to.isoformat()

                # Use create_relationship with proper signature: (from_id, to_id, rel_type, properties)
                neo4j_client.create_relationship(
                    from_id=rel.from_node_id,
                    to_id=rel.to_node_id,
                    rel_type=rel.type,
                    properties=props,
                )
                restored += 1
            except Exception as e:
                logger.exception("Failed to restore relationship", relationship_id=rel.relationship_id, error=str(e))

        return restored
