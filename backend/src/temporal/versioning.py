"""Node and relationship versioning."""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import uuid4

from sqlalchemy import text

from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.logging import get_logger
from src.temporal.models import TemporalNode, TemporalRelationship, ChangeHistory

logger = get_logger(__name__)


class TemporalVersioning:
    """Manages versioning of nodes and relationships."""

    def __init__(self):
        """Initialize temporal versioning."""
        self._ensure_versioning_tables()

    def _ensure_versioning_tables(self):
        """Ensure versioning tables exist in PostgreSQL."""
        query = """
        CREATE TABLE IF NOT EXISTS temporal_nodes (
            node_id VARCHAR(255) NOT NULL,
            version INTEGER NOT NULL,
            valid_from TIMESTAMP NOT NULL,
            valid_to TIMESTAMP,
            labels TEXT[] NOT NULL,
            properties JSONB NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            created_by VARCHAR(255),
            PRIMARY KEY (node_id, version)
        );

        CREATE TABLE IF NOT EXISTS temporal_relationships (
            relationship_id VARCHAR(255) NOT NULL,
            version INTEGER NOT NULL,
            valid_from TIMESTAMP NOT NULL,
            valid_to TIMESTAMP,
            type VARCHAR(255) NOT NULL,
            from_node_id VARCHAR(255) NOT NULL,
            to_node_id VARCHAR(255) NOT NULL,
            properties JSONB NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            created_by VARCHAR(255),
            PRIMARY KEY (relationship_id, version)
        );

        CREATE TABLE IF NOT EXISTS change_history (
            change_id VARCHAR(255) PRIMARY KEY,
            entity_id VARCHAR(255) NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            change_type VARCHAR(50) NOT NULL,
            timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
            version INTEGER NOT NULL,
            old_properties JSONB,
            new_properties JSONB,
            changed_by VARCHAR(255)
        );

        CREATE INDEX IF NOT EXISTS idx_temporal_nodes_id_time ON temporal_nodes(node_id, valid_from, valid_to);
        CREATE INDEX IF NOT EXISTS idx_temporal_relationships_id_time ON temporal_relationships(relationship_id, valid_from, valid_to);
        CREATE INDEX IF NOT EXISTS idx_change_history_entity ON change_history(entity_id, entity_type);
        CREATE INDEX IF NOT EXISTS idx_change_history_timestamp ON change_history(timestamp);
        """
        postgres_client.execute(query)

    def version_node(
        self,
        node_id: str,
        labels: List[str],
        properties: Dict[str, Any],
        timestamp: Optional[datetime] = None,
        created_by: Optional[str] = None,
    ) -> TemporalNode:
        """
        Create a new version of a node.

        Args:
            node_id: Node identifier
            labels: Node labels
            properties: Node properties
            timestamp: Version timestamp (defaults to now)
            created_by: User who created this version

        Returns:
            TemporalNode instance
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Get current version
        current_version = self._get_current_node_version(node_id)

        # Close previous version
        if current_version is not None:
            self._close_node_version(node_id, current_version, timestamp)

        # Create new version
        new_version = current_version + 1 if current_version is not None else 1

        query = """
        INSERT INTO temporal_nodes 
        (node_id, version, valid_from, valid_to, labels, properties, created_at, created_by)
        VALUES (%(node_id)s, %(version)s, %(valid_from)s, %(valid_to)s, %(labels)s, %(properties)s, %(created_at)s, %(created_by)s)
        """
        params = {
            "node_id": node_id,
            "version": new_version,
            "valid_from": timestamp,
            "valid_to": None,
            "labels": labels,
            "properties": properties,
            "created_at": timestamp,
            "created_by": created_by,
        }
        with postgres_client.get_session() as session:
            session.execute(text(query), params)

        # Log change
        self._log_change(
            entity_id=node_id,
            entity_type="node",
            change_type="created" if current_version is None else "updated",
            version=new_version,
            old_properties=None if current_version is None else self._get_node_properties(node_id, current_version),
            new_properties=properties,
            changed_by=created_by,
        )

        return TemporalNode(
            node_id=node_id,
            version=new_version,
            valid_from=timestamp,
            valid_to=None,
            labels=labels,
            properties=properties,
            created_at=timestamp,
            created_by=created_by,
        )

    def version_relationship(
        self,
        relationship_id: str,
        rel_type: str,
        from_node_id: str,
        to_node_id: str,
        properties: Dict[str, Any],
        timestamp: Optional[datetime] = None,
        created_by: Optional[str] = None,
    ) -> TemporalRelationship:
        """
        Create a new version of a relationship.

        Args:
            relationship_id: Relationship identifier
            rel_type: Relationship type
            from_node_id: Source node ID
            to_node_id: Target node ID
            properties: Relationship properties
            timestamp: Version timestamp (defaults to now)
            created_by: User who created this version

        Returns:
            TemporalRelationship instance
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Get current version
        current_version = self._get_current_relationship_version(relationship_id)

        # Close previous version
        if current_version is not None:
            self._close_relationship_version(relationship_id, current_version, timestamp)

        # Create new version
        new_version = current_version + 1 if current_version is not None else 1

        query = """
        INSERT INTO temporal_relationships 
        (relationship_id, version, valid_from, valid_to, type, from_node_id, to_node_id, properties, created_at, created_by)
        VALUES (%(relationship_id)s, %(version)s, %(valid_from)s, %(valid_to)s, %(type)s, %(from_node_id)s, %(to_node_id)s, %(properties)s, %(created_at)s, %(created_by)s)
        """
        params = {
            "relationship_id": relationship_id,
            "version": new_version,
            "valid_from": timestamp,
            "valid_to": None,
            "type": rel_type,
            "from_node_id": from_node_id,
            "to_node_id": to_node_id,
            "properties": properties,
            "created_at": timestamp,
            "created_by": created_by,
        }
        with postgres_client.get_session() as session:
            session.execute(text(query), params)

        # Log change
        self._log_change(
            entity_id=relationship_id,
            entity_type="relationship",
            change_type="created" if current_version is None else "updated",
            version=new_version,
            old_properties=None if current_version is None else self._get_relationship_properties(relationship_id, current_version),
            new_properties=properties,
            changed_by=created_by,
        )

        return TemporalRelationship(
            relationship_id=relationship_id,
            version=new_version,
            valid_from=timestamp,
            valid_to=None,
            type=rel_type,
            from_node_id=from_node_id,
            to_node_id=to_node_id,
            properties=properties,
            created_at=timestamp,
            created_by=created_by,
        )

    def _get_current_node_version(self, node_id: str) -> Optional[int]:
        """Get current version number for a node."""
        query = "SELECT MAX(version) as max_version FROM temporal_nodes WHERE node_id = %(node_id)s"
        with postgres_client.get_session() as session:
            result = session.execute(text(query), {"node_id": node_id})
            row = result.fetchone()
            return row["max_version"] if row and row["max_version"] else None

    def _get_current_relationship_version(self, relationship_id: str) -> Optional[int]:
        """Get current version number for a relationship."""
        query = "SELECT MAX(version) as max_version FROM temporal_relationships WHERE relationship_id = %(relationship_id)s"
        with postgres_client.get_session() as session:
            result = session.execute(text(query), {"relationship_id": relationship_id})
            row = result.fetchone()
            return row["max_version"] if row and row["max_version"] else None

    def _close_node_version(self, node_id: str, version: int, timestamp: datetime):
        """Close a node version by setting valid_to."""
        query = """
        UPDATE temporal_nodes 
        SET valid_to = %(timestamp)s 
        WHERE node_id = %(node_id)s AND version = %(version)s
        """
        with postgres_client.get_session() as session:
            session.execute(text(query), {"timestamp": timestamp, "node_id": node_id, "version": version})

    def _close_relationship_version(self, relationship_id: str, version: int, timestamp: datetime):
        """Close a relationship version by setting valid_to."""
        query = """
        UPDATE temporal_relationships 
        SET valid_to = %(timestamp)s 
        WHERE relationship_id = %(relationship_id)s AND version = %(version)s
        """
        with postgres_client.get_session() as session:
            session.execute(text(query), {"timestamp": timestamp, "relationship_id": relationship_id, "version": version})

    def _get_node_properties(self, node_id: str, version: int) -> Optional[Dict[str, Any]]:
        """Get node properties for a specific version."""
        query = "SELECT properties FROM temporal_nodes WHERE node_id = %(node_id)s AND version = %(version)s"
        with postgres_client.get_session() as session:
            result = session.execute(text(query), {"node_id": node_id, "version": version})
            row = result.fetchone()
            return row["properties"] if row else None

    def _get_relationship_properties(self, relationship_id: str, version: int) -> Optional[Dict[str, Any]]:
        """Get relationship properties for a specific version."""
        query = "SELECT properties FROM temporal_relationships WHERE relationship_id = %(relationship_id)s AND version = %(version)s"
        with postgres_client.get_session() as session:
            result = session.execute(text(query), {"relationship_id": relationship_id, "version": version})
            row = result.fetchone()
            return row["properties"] if row else None

    def _log_change(
        self,
        entity_id: str,
        entity_type: str,
        change_type: str,
        version: int,
        old_properties: Optional[Dict[str, Any]],
        new_properties: Optional[Dict[str, Any]],
        changed_by: Optional[str],
    ):
        """Log a change to change history."""
        change_id = str(uuid4())
        query = """
        INSERT INTO change_history 
        (change_id, entity_id, entity_type, change_type, timestamp, version, old_properties, new_properties, changed_by)
        VALUES (%(change_id)s, %(entity_id)s, %(entity_type)s, %(change_type)s, NOW(), %(version)s, %(old_properties)s, %(new_properties)s, %(changed_by)s)
        """
        params = {
            "change_id": change_id,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "change_type": change_type,
            "version": version,
            "old_properties": old_properties,
            "new_properties": new_properties,
            "changed_by": changed_by,
        }
        with postgres_client.get_session() as session:
            session.execute(text(query), params)
