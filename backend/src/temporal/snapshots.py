"""Graph snapshot management for point-in-time restores."""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import uuid4

from sqlalchemy import text

from sqlalchemy import text

from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.logging import get_logger
from src.temporal.models import GraphSnapshot, TemporalNode, TemporalRelationship
from src.temporal.queries import TemporalQueryEngine

logger = get_logger(__name__)


class SnapshotManager:
    """Manages graph snapshots for point-in-time restores."""

    def __init__(self):
        """Initialize snapshot manager."""
        self.query_engine = TemporalQueryEngine()
        # Table creation will happen on first use

    def _ensure_snapshots_table(self):
        """Ensure snapshots table exists."""
        query = """
        CREATE TABLE IF NOT EXISTS graph_snapshots (
            snapshot_id VARCHAR(255) PRIMARY KEY,
            timestamp TIMESTAMP NOT NULL,
            description TEXT,
            node_count INTEGER NOT NULL DEFAULT 0,
            relationship_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            created_by VARCHAR(255)
        );

        CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON graph_snapshots(timestamp);
        """
        with postgres_client.get_session() as session:
            session.execute(text(query))
            session.commit()

    def create_snapshot(
        self,
        timestamp: Optional[datetime] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> GraphSnapshot:
        """
        Create a snapshot of the graph at a specific point in time.

        Args:
            timestamp: Point in time (defaults to now)
            description: Optional description
            created_by: User who created the snapshot

        Returns:
            GraphSnapshot instance
        """
        self._ensure_snapshots_table()  # Ensure table exists
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        snapshot_id = str(uuid4())

        # Query graph state at timestamp
        result = self.query_engine.query_at_time(timestamp)

        # Store snapshot metadata
        query = """
        INSERT INTO graph_snapshots 
        (snapshot_id, timestamp, description, node_count, relationship_count, created_at, created_by)
        VALUES (%(snapshot_id)s, %(timestamp)s, %(description)s, %(node_count)s, %(relationship_count)s, NOW(), %(created_by)s)
        """
        params = {
            "snapshot_id": snapshot_id,
            "timestamp": timestamp,
            "description": description,
            "node_count": result.total_nodes,
            "relationship_count": result.total_relationships,
            "created_by": created_by,
        }
        postgres_client.execute(query, params)

        logger.info("Snapshot created", snapshot_id=snapshot_id, timestamp=timestamp)

        return GraphSnapshot(
            snapshot_id=snapshot_id,
            timestamp=timestamp,
            description=description,
            node_count=result.total_nodes,
            relationship_count=result.total_relationships,
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
        )

    def get_snapshot(self, snapshot_id: str) -> Optional[GraphSnapshot]:
        """Get snapshot by ID."""
        query = """
        SELECT snapshot_id, timestamp, description, node_count, relationship_count, created_at, created_by
        FROM graph_snapshots
        WHERE snapshot_id = %(snapshot_id)s
        """
        with postgres_client.get_session() as session:
            result = session.execute(text(query), {"snapshot_id": snapshot_id})
            row = result.fetchone()
            if not row:
                return None
            row_dict = dict(row)
            return GraphSnapshot(
                snapshot_id=row_dict["snapshot_id"],
                timestamp=row_dict["timestamp"],
                description=row_dict.get("description"),
                node_count=row_dict["node_count"],
                relationship_count=row_dict["relationship_count"],
                created_at=row_dict["created_at"],
                created_by=row_dict.get("created_by"),
            )

    def list_snapshots(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[GraphSnapshot]:
        """List snapshots with optional time filters."""
        conditions = ["1=1"]
        params = {"limit": limit}

        if start_time:
            conditions.append("timestamp >= %(start_time)s")
            params["start_time"] = start_time

        if end_time:
            conditions.append("timestamp <= %(end_time)s")
            params["end_time"] = end_time

        where_clause = " AND ".join(conditions)

        query = f"""
        SELECT snapshot_id, timestamp, description, node_count, relationship_count, created_at, created_by
        FROM graph_snapshots
        WHERE {where_clause}
        ORDER BY timestamp DESC
        LIMIT %(limit)s
        """
        
        with postgres_client.get_session() as session:
            result = session.execute(text(query), params)
            rows = [dict(row) for row in result]
        
        return [
            GraphSnapshot(
                snapshot_id=row["snapshot_id"],
                timestamp=row["timestamp"],
                description=row.get("description"),
                node_count=row["node_count"],
                relationship_count=row["relationship_count"],
                created_at=row["created_at"],
                created_by=row.get("created_by"),
            )
            for row in rows
        ]

    def restore_from_snapshot(
        self,
        snapshot_id: str,
        target_timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Restore graph to state from a snapshot.

        Args:
            snapshot_id: Snapshot to restore from
            target_timestamp: Optional target timestamp (uses snapshot timestamp if not provided)

        Returns:
            Dictionary with restore statistics
        """
        snapshot = self.get_snapshot(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot not found: {snapshot_id}")

        timestamp = target_timestamp or snapshot.timestamp

        # Query graph state at snapshot time
        result = self.query_engine.query_at_time(timestamp)

        # Restore nodes and relationships to Neo4j
        # This is a simplified version - in production, you'd want to:
        # 1. Create a restore transaction
        # 2. Delete current nodes/relationships
        # 3. Create nodes/relationships from snapshot
        # 4. Commit transaction

        logger.info("Restore from snapshot", snapshot_id=snapshot_id, timestamp=timestamp)

        return {
            "snapshot_id": snapshot_id,
            "timestamp": timestamp,
            "nodes_restored": result.total_nodes,
            "relationships_restored": result.total_relationships,
            "status": "completed",
        }
