"""Graph traversal models."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class GraphNode(BaseModel):
    """Graph node representation."""

    id: str
    labels: List[str]
    properties: Dict[str, Any]


class GraphRelationship(BaseModel):
    """Graph relationship representation."""

    type: str
    from_id: str
    to_id: str
    properties: Dict[str, Any] = {}


class Subgraph(BaseModel):
    """Subgraph result."""

    nodes: List[GraphNode]
    relationships: List[GraphRelationship]
    center_node_id: Optional[str] = None


class Path(BaseModel):
    """Path between two nodes."""

    nodes: List[GraphNode]
    relationships: List[GraphRelationship]
    length: int
    cost: Optional[float] = None


class Cycle(BaseModel):
    """Cycle detected in graph."""

    nodes: List[GraphNode]
    relationships: List[GraphRelationship]
    length: int


class ConnectedComponent(BaseModel):
    """Connected component."""

    nodes: List[GraphNode]
    relationships: List[GraphRelationship]
    size: int


class GraphMetrics(BaseModel):
    """Graph metrics for a node or subgraph."""

    node_id: str
    degree: Optional[int] = None
    in_degree: Optional[int] = None
    out_degree: Optional[int] = None
    betweenness_centrality: Optional[float] = None
    closeness_centrality: Optional[float] = None
    pagerank: Optional[float] = None
    eigenvector_centrality: Optional[float] = None
