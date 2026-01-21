"""Relationship search: find connections between entities."""
from typing import Dict, List, Optional

from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.logging import get_logger

from .models import GraphNode, GraphRelationship, Path
from .traversal import find_all_paths, find_shortest_path

logger = get_logger(__name__)


class RelationshipConnection:
    """Connection path between two entities with strength score."""

    def __init__(
        self,
        path: Path,
        strength_score: float,
        connection_type: str,
        details: Dict,
    ):
        self.path = path
        self.strength_score = strength_score
        self.connection_type = connection_type
        self.details = details

    def to_dict(self) -> Dict:
        """Convert to dictionary for API response."""
        return {
            "path": self.path.model_dump(mode="json"),
            "strength_score": self.strength_score,
            "connection_type": self.connection_type,
            "details": self.details,
        }


def find_connections(
    entity_a_id: str,
    entity_b_id: str,
    max_depth: int = 5,
    include_all_paths: bool = False,
) -> List[RelationshipConnection]:
    """
    Find all connection paths between two entities.

    Returns paths sorted by strength score (strongest first).
    """
    if include_all_paths:
        paths = find_all_paths(entity_a_id, entity_b_id, max_depth=max_depth, limit=50)
    else:
        shortest = find_shortest_path(entity_a_id, entity_b_id, max_depth=max_depth)
        paths = [shortest] if shortest else []

    connections = []
    for path in paths:
        strength = _calculate_relationship_strength(path)
        conn_type = _classify_connection_type(path)
        details = _extract_connection_details(path)

        connections.append(
            RelationshipConnection(
                path=path,
                strength_score=strength,
                connection_type=conn_type,
                details=details,
            )
        )

    # Sort by strength (highest first)
    connections.sort(key=lambda c: c.strength_score, reverse=True)
    return connections


def _calculate_relationship_strength(path: Path) -> float:
    """
    Calculate relationship strength score (0-1).

    Factors:
    - Shorter paths = stronger
    - Direct relationships = strongest
    - Ownership relationships = high strength
    - Director relationships = high strength
    - Transaction relationships = medium strength
    """
    if path.length == 0:
        return 1.0

    # Base score from path length (shorter = stronger)
    length_penalty = 1.0 / (path.length + 1)

    # Boost for specific relationship types
    type_boost = 0.0
    for rel in path.relationships:
        rel_type = rel.type.lower()
        if "owns" in rel_type or "owner" in rel_type:
            type_boost += 0.3
        elif "director" in rel_type:
            type_boost += 0.25
        elif "transaction" in rel_type or "payment" in rel_type:
            type_boost += 0.15
        elif "supplier" in rel_type or "customer" in rel_type:
            type_boost += 0.1

    # Normalize boost
    type_boost = min(0.5, type_boost / len(path.relationships)) if path.relationships else 0.0

    strength = length_penalty + type_boost
    return min(1.0, strength)


def _classify_connection_type(path: Path) -> str:
    """Classify the type of connection between entities."""
    if path.length == 0:
        return "direct"
    if path.length == 1:
        rel_type = path.relationships[0].type if path.relationships else ""
        return f"direct_{rel_type.lower()}"

    # Analyze path for common patterns
    rel_types = [r.type.lower() for r in path.relationships]

    if any("owns" in rt for rt in rel_types):
        return "ownership_chain"
    if any("director" in rt for rt in rel_types):
        return "director_network"
    if any("supplier" in rt or "customer" in rt for rt in rel_types):
        return "business_network"
    if any("transaction" in rt or "payment" in rt for rt in rel_types):
        return "transaction_network"

    return "indirect"


def _extract_connection_details(path: Path) -> Dict:
    """Extract relevant details about the connection."""
    details = {
        "path_length": path.length,
        "relationship_types": [r.type for r in path.relationships],
        "intermediate_nodes": [n.id for n in path.nodes[1:-1]] if len(path.nodes) > 2 else [],
    }

    # Count specific relationship types
    ownership_count = sum(1 for r in path.relationships if "owns" in r.type.lower())
    director_count = sum(1 for r in path.relationships if "director" in r.type.lower())
    transaction_count = sum(1 for r in path.relationships if "transaction" in r.type.lower() or "payment" in r.type.lower())

    details["ownership_links"] = ownership_count
    details["director_links"] = director_count
    details["transaction_links"] = transaction_count

    return details
