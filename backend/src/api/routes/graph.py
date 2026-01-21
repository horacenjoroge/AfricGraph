"""Graph traversal and analysis API endpoints."""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.graph.common_ownership import find_common_owners, find_ownership_path
from src.graph.components import find_connected_components, get_component_for_node
from src.graph.cycles import detect_cycles
from src.graph.export import (
    export_path_for_visualization,
    export_subgraph_for_visualization,
)
from src.graph.metrics import compute_node_metrics, compute_pagerank_for_subgraph
from src.graph.relationship_search import find_connections
from src.graph.shared_directors import find_director_network_path, find_shared_directors
from src.graph.traversal import extract_subgraph, find_all_paths, find_shortest_path

router = APIRouter(prefix="/graph", tags=["graph"])


class PathRequest(BaseModel):
    start_id: str
    end_id: str
    max_depth: int = 10
    rel_types: Optional[List[str]] = None


@router.get("/subgraph/{node_id}")
def get_subgraph(
    node_id: str,
    max_hops: int = Query(2, ge=1, le=5),
    rel_types: Optional[List[str]] = Query(None),
    node_labels: Optional[List[str]] = Query(None),
    format: str = Query("json", regex="^(json|visualization|cypher)$"),
) -> dict:
    """Extract N-hop neighborhood subgraph."""
    subgraph = extract_subgraph(node_id, max_hops, rel_types, node_labels)

    if format == "visualization":
        return export_subgraph_for_visualization(subgraph)
    elif format == "cypher":
        from src.graph.export import export_cypher

        return {"cypher": export_cypher(subgraph)}
    else:
        return subgraph.model_dump(mode="json")


@router.post("/path/shortest")
def get_shortest_path(body: PathRequest) -> dict:
    """Find shortest path between two nodes."""
    path = find_shortest_path(body.start_id, body.end_id, body.max_depth, body.rel_types)
    if not path:
        raise HTTPException(status_code=404, detail="No path found")
    return path.model_dump(mode="json")


@router.post("/path/all")
def get_all_paths(
    body: PathRequest,
    limit: int = Query(100, ge=1, le=1000),
) -> dict:
    """Find all paths between two nodes."""
    paths = find_all_paths(body.start_id, body.end_id, body.max_depth, limit, body.rel_types)
    return {"paths": [p.model_dump(mode="json") for p in paths], "count": len(paths)}


@router.get("/cycles")
def get_cycles(
    node_id: Optional[str] = None,
    max_depth: int = Query(10, ge=2, le=20),
    rel_types: Optional[List[str]] = Query(None),
) -> dict:
    """Detect cycles in graph."""
    cycles = detect_cycles(node_id, max_depth, rel_types)
    return {"cycles": [c.model_dump(mode="json") for c in cycles], "count": len(cycles)}


@router.get("/components")
def get_components(
    node_label: Optional[str] = None,
    rel_types: Optional[List[str]] = None,
    min_size: int = Query(2, ge=1),
) -> dict:
    """Find connected components."""
    components = find_connected_components(node_label, rel_types, min_size)
    return {
        "components": [c.model_dump(mode="json") for c in components],
        "count": len(components),
    }


@router.get("/components/node/{node_id}")
def get_node_component(node_id: str) -> dict:
    """Get connected component containing a specific node."""
    component = get_component_for_node(node_id)
    if not component:
        raise HTTPException(status_code=404, detail="Node not found or isolated")
    return component.model_dump(mode="json")


@router.get("/metrics/{node_id}")
def get_metrics(
    node_id: str,
    include_centrality: bool = Query(True),
) -> dict:
    """Compute graph metrics for a node."""
    metrics = compute_node_metrics(node_id, include_centrality)
    return metrics.model_dump(mode="json")


@router.post("/metrics/pagerank")
def compute_pagerank(
    node_ids: List[str],
    iterations: int = Query(20, ge=1, le=100),
) -> dict:
    """Compute PageRank for a set of nodes."""
    scores = compute_pagerank_for_subgraph(node_ids, iterations)
    return {"pagerank_scores": scores}


@router.get("/path/{start_id}/{end_id}/visualization")
def get_path_visualization(start_id: str, end_id: str) -> dict:
    """Get path in visualization format."""
    path = find_shortest_path(start_id, end_id)
    if not path:
        raise HTTPException(status_code=404, detail="No path found")
    return export_path_for_visualization(path)


@router.get("/relationships/connect/{entity_a_id}/{entity_b_id}")
def get_connections(
    entity_a_id: str,
    entity_b_id: str,
    max_depth: int = Query(5, ge=1, le=10),
    include_all_paths: bool = Query(False),
    format: str = Query("json", regex="^(json|visualization)$"),
) -> dict:
    """
    Find how two entities are connected.

    Returns all connection paths with strength scores.
    """
    connections = find_connections(entity_a_id, entity_b_id, max_depth, include_all_paths)

    if format == "visualization":
        # Return visualization-ready format
        result = {
            "entity_a_id": entity_a_id,
            "entity_b_id": entity_b_id,
            "connections": [],
        }
        for conn in connections:
            vis_data = export_path_for_visualization(conn.path)
            vis_data["strength_score"] = conn.strength_score
            vis_data["connection_type"] = conn.connection_type
            vis_data["details"] = conn.details
            result["connections"].append(vis_data)
        return result
    else:
        return {
            "entity_a_id": entity_a_id,
            "entity_b_id": entity_b_id,
            "connections": [c.to_dict() for c in connections],
            "count": len(connections),
        }


@router.get("/relationships/common-ownership/{entity_a_id}/{entity_b_id}")
def get_common_ownership(entity_a_id: str, entity_b_id: str) -> dict:
    """Find common owners between two entities."""
    return find_common_owners(entity_a_id, entity_b_id)


@router.get("/relationships/ownership-path/{entity_a_id}/{entity_b_id}")
def get_ownership_path(entity_a_id: str, entity_b_id: str) -> dict:
    """Find ownership chain connecting two entities."""
    path = find_ownership_path(entity_a_id, entity_b_id)
    if not path:
        raise HTTPException(status_code=404, detail="No ownership path found")
    return path


@router.get("/relationships/shared-directors/{entity_a_id}/{entity_b_id}")
def get_shared_directors(entity_a_id: str, entity_b_id: str) -> dict:
    """Find shared directors between two businesses."""
    return find_shared_directors(entity_a_id, entity_b_id)


@router.get("/relationships/director-path/{entity_a_id}/{entity_b_id}")
def get_director_path(entity_a_id: str, entity_b_id: str) -> dict:
    """Find path connecting two entities through director relationships."""
    path = find_director_network_path(entity_a_id, entity_b_id)
    if not path:
        raise HTTPException(status_code=404, detail="No director path found")
    return path
