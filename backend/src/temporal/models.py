"""Temporal data models for versioning."""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class TemporalNode(BaseModel):
    """Versioned node with temporal information."""
    node_id: str
    version: int
    valid_from: datetime
    valid_to: Optional[datetime]
    labels: list[str]
    properties: Dict[str, Any]
    created_at: datetime
    created_by: Optional[str] = None


class TemporalRelationship(BaseModel):
    """Versioned relationship with temporal information."""
    relationship_id: str
    version: int
    valid_from: datetime
    valid_to: Optional[datetime]
    type: str
    from_node_id: str
    to_node_id: str
    properties: Dict[str, Any]
    created_at: datetime
    created_by: Optional[str] = None


class GraphSnapshot(BaseModel):
    """Point-in-time graph snapshot."""
    snapshot_id: str
    timestamp: datetime
    description: Optional[str] = None
    node_count: int = 0
    relationship_count: int = 0
    created_at: datetime
    created_by: Optional[str] = None


class ChangeHistory(BaseModel):
    """Change history entry."""
    change_id: str
    entity_id: str
    entity_type: str  # "node" or "relationship"
    change_type: str  # "created", "updated", "deleted"
    timestamp: datetime
    version: int
    old_properties: Optional[Dict[str, Any]] = None
    new_properties: Optional[Dict[str, Any]] = None
    changed_by: Optional[str] = None


class TemporalQueryResult(BaseModel):
    """Result of a temporal query."""
    nodes: list[TemporalNode]
    relationships: list[TemporalRelationship]
    timestamp: datetime
    total_nodes: int
    total_relationships: int
