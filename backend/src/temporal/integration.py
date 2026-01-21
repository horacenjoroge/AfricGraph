"""Integration with Neo4j client for automatic versioning."""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.logging import get_logger
from src.temporal.versioning import TemporalVersioning

logger = get_logger(__name__)

# Global versioning instance
_versioning = None


def get_versioning() -> TemporalVersioning:
    """Get or create temporal versioning instance."""
    global _versioning
    if _versioning is None:
        _versioning = TemporalVersioning()
    return _versioning


def version_node_on_create(
    node_id: str,
    labels: List[str],
    properties: Dict[str, Any],
    created_by: Optional[str] = None,
) -> None:
    """Automatically version a node when created in Neo4j."""
    try:
        versioning = get_versioning()
        versioning.version_node(
            node_id=node_id,
            labels=labels,
            properties=properties,
            timestamp=datetime.now(timezone.utc),
            created_by=created_by,
        )
        logger.debug("Node versioned", node_id=node_id)
    except Exception as e:
        logger.exception("Failed to version node", node_id=node_id, error=str(e))


def version_node_on_update(
    node_id: str,
    labels: List[str],
    properties: Dict[str, Any],
    created_by: Optional[str] = None,
) -> None:
    """Automatically version a node when updated in Neo4j."""
    try:
        versioning = get_versioning()
        versioning.version_node(
            node_id=node_id,
            labels=labels,
            properties=properties,
            timestamp=datetime.now(timezone.utc),
            created_by=created_by,
        )
        logger.debug("Node versioned on update", node_id=node_id)
    except Exception as e:
        logger.exception("Failed to version node on update", node_id=node_id, error=str(e))


def version_relationship_on_create(
    relationship_id: str,
    rel_type: str,
    from_node_id: str,
    to_node_id: str,
    properties: Dict[str, Any],
    created_by: Optional[str] = None,
) -> None:
    """Automatically version a relationship when created in Neo4j."""
    try:
        versioning = get_versioning()
        versioning.version_relationship(
            relationship_id=relationship_id,
            rel_type=rel_type,
            from_node_id=from_node_id,
            to_node_id=to_node_id,
            properties=properties,
            timestamp=datetime.now(timezone.utc),
            created_by=created_by,
        )
        logger.debug("Relationship versioned", relationship_id=relationship_id)
    except Exception as e:
        logger.exception("Failed to version relationship", relationship_id=relationship_id, error=str(e))


def version_relationship_on_update(
    relationship_id: str,
    rel_type: str,
    from_node_id: str,
    to_node_id: str,
    properties: Dict[str, Any],
    created_by: Optional[str] = None,
) -> None:
    """Automatically version a relationship when updated in Neo4j."""
    try:
        versioning = get_versioning()
        versioning.version_relationship(
            relationship_id=relationship_id,
            rel_type=rel_type,
            from_node_id=from_node_id,
            to_node_id=to_node_id,
            properties=properties,
            timestamp=datetime.now(timezone.utc),
            created_by=created_by,
        )
        logger.debug("Relationship versioned on update", relationship_id=relationship_id)
    except Exception as e:
        logger.exception("Failed to version relationship on update", relationship_id=relationship_id, error=str(e))
