"""Relationship GraphQL types."""
import strawberry
from typing import Optional, List


@strawberry.type
class RelationshipType:
    """GraphQL type for relationships."""

    type: str
    from_id: str
    to_id: str
    properties: Optional[str] = None  # JSON string


@strawberry.type
class PathType:
    """GraphQL type for graph paths."""

    nodes: List[str]  # Node IDs
    relationships: List[RelationshipType]
    length: int
    strength_score: Optional[float] = None
