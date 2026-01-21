"""Temporal query support for point-in-time queries."""
from datetime import datetime
from typing import Optional, List, Dict, Any

from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.logging import get_logger
from src.temporal.models import TemporalNode, TemporalRelationship, TemporalQueryResult

logger = get_logger(__name__)


class TemporalQueryEngine:
    """Engine for executing temporal queries."""

    def query_at_time(
        self,
        timestamp: datetime,
        node_ids: Optional[List[str]] = None,
        relationship_ids: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        rel_types: Optional[List[str]] = None,
    ) -> TemporalQueryResult:
        """
        Query graph state at a specific point in time.

        Args:
            timestamp: Point in time to query
            node_ids: Optional list of node IDs to filter
            relationship_ids: Optional list of relationship IDs to filter
            labels: Optional list of node labels to filter
            rel_types: Optional list of relationship types to filter

        Returns:
            TemporalQueryResult with nodes and relationships valid at timestamp
        """
        # Query nodes valid at timestamp
        nodes = self._query_nodes_at_time(timestamp, node_ids, labels)
        
        # Query relationships valid at timestamp
        relationships = self._query_relationships_at_time(timestamp, relationship_ids, rel_types)

        return TemporalQueryResult(
            nodes=nodes,
            relationships=relationships,
            timestamp=timestamp,
            total_nodes=len(nodes),
            total_relationships=len(relationships),
        )

    def _query_nodes_at_time(
        self,
        timestamp: datetime,
        node_ids: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
    ) -> List[TemporalNode]:
        """Query nodes valid at a specific timestamp."""
        conditions = [
            "valid_from <= %(timestamp)s",
            "(valid_to IS NULL OR valid_to > %(timestamp)s)",
        ]
        params = {"timestamp": timestamp}

        if node_ids:
            conditions.append("node_id = ANY(%(node_ids)s)")
            params["node_ids"] = node_ids

        if labels:
            conditions.append("labels && %(labels)s")
            params["labels"] = labels

        where_clause = " AND ".join(conditions)

        query = f"""
        SELECT node_id, version, valid_from, valid_to, labels, properties, created_at, created_by
        FROM temporal_nodes
        WHERE {where_clause}
        ORDER BY node_id, version DESC
        """
        
        # Get latest version for each node
        rows = postgres_client.fetch_all(query, params)
        
        # Group by node_id and take latest version
        nodes_by_id = {}
        for row in rows:
            node_id = row["node_id"]
            if node_id not in nodes_by_id:
                nodes_by_id[node_id] = row

        return [
            TemporalNode(
                node_id=row["node_id"],
                version=row["version"],
                valid_from=row["valid_from"],
                valid_to=row["valid_to"],
                labels=row["labels"],
                properties=row["properties"],
                created_at=row["created_at"],
                created_by=row.get("created_by"),
            )
            for row in nodes_by_id.values()
        ]

    def _query_relationships_at_time(
        self,
        timestamp: datetime,
        relationship_ids: Optional[List[str]] = None,
        rel_types: Optional[List[str]] = None,
    ) -> List[TemporalRelationship]:
        """Query relationships valid at a specific timestamp."""
        conditions = [
            "valid_from <= %(timestamp)s",
            "(valid_to IS NULL OR valid_to > %(timestamp)s)",
        ]
        params = {"timestamp": timestamp}

        if relationship_ids:
            conditions.append("relationship_id = ANY(%(relationship_ids)s)")
            params["relationship_ids"] = relationship_ids

        if rel_types:
            conditions.append("type = ANY(%(rel_types)s)")
            params["rel_types"] = rel_types

        where_clause = " AND ".join(conditions)

        query = f"""
        SELECT relationship_id, version, valid_from, valid_to, type, from_node_id, to_node_id, 
               properties, created_at, created_by
        FROM temporal_relationships
        WHERE {where_clause}
        ORDER BY relationship_id, version DESC
        """
        
        rows = postgres_client.fetch_all(query, params)
        
        # Group by relationship_id and take latest version
        rels_by_id = {}
        for row in rows:
            rel_id = row["relationship_id"]
            if rel_id not in rels_by_id:
                rels_by_id[rel_id] = row

        return [
            TemporalRelationship(
                relationship_id=row["relationship_id"],
                version=row["version"],
                valid_from=row["valid_from"],
                valid_to=row["valid_to"],
                type=row["type"],
                from_node_id=row["from_node_id"],
                to_node_id=row["to_node_id"],
                properties=row["properties"],
                created_at=row["created_at"],
                created_by=row.get("created_by"),
            )
            for row in rels_by_id.values()
        ]

    def query_node_history(
        self,
        node_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[TemporalNode]:
        """
        Get version history for a node.

        Args:
            node_id: Node identifier
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            List of all versions of the node
        """
        conditions = ["node_id = %(node_id)s"]
        params = {"node_id": node_id}

        if start_time:
            conditions.append("valid_from >= %(start_time)s")
            params["start_time"] = start_time

        if end_time:
            conditions.append("(valid_to IS NULL OR valid_to <= %(end_time)s)")
            params["end_time"] = end_time

        where_clause = " AND ".join(conditions)

        query = f"""
        SELECT node_id, version, valid_from, valid_to, labels, properties, created_at, created_by
        FROM temporal_nodes
        WHERE {where_clause}
        ORDER BY version ASC
        """
        
        rows = postgres_client.fetch_all(query, params)
        
        return [
            TemporalNode(
                node_id=row["node_id"],
                version=row["version"],
                valid_from=row["valid_from"],
                valid_to=row["valid_to"],
                labels=row["labels"],
                properties=row["properties"],
                created_at=row["created_at"],
                created_by=row.get("created_by"),
            )
            for row in rows
        ]

    def query_relationship_history(
        self,
        relationship_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[TemporalRelationship]:
        """
        Get version history for a relationship.

        Args:
            relationship_id: Relationship identifier
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            List of all versions of the relationship
        """
        conditions = ["relationship_id = %(relationship_id)s"]
        params = {"relationship_id": relationship_id}

        if start_time:
            conditions.append("valid_from >= %(start_time)s")
            params["start_time"] = start_time

        if end_time:
            conditions.append("(valid_to IS NULL OR valid_to <= %(end_time)s)")
            params["end_time"] = end_time

        where_clause = " AND ".join(conditions)

        query = f"""
        SELECT relationship_id, version, valid_from, valid_to, type, from_node_id, to_node_id,
               properties, created_at, created_by
        FROM temporal_relationships
        WHERE {where_clause}
        ORDER BY version ASC
        """
        
        rows = postgres_client.fetch_all(query, params)
        
        return [
            TemporalRelationship(
                relationship_id=row["relationship_id"],
                version=row["version"],
                valid_from=row["valid_from"],
                valid_to=row["valid_to"],
                type=row["type"],
                from_node_id=row["from_node_id"],
                to_node_id=row["to_node_id"],
                properties=row["properties"],
                created_at=row["created_at"],
                created_by=row.get("created_by"),
            )
            for row in rows
        ]
