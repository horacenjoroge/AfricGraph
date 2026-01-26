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
    format: str = Query("json", pattern="^(json|visualization|cypher)$"),
) -> dict:
    """Extract N-hop neighborhood subgraph."""
    from src.graph.models import Subgraph, GraphNode, GraphRelationship
    from src.tenancy.context import get_current_tenant
    from src.infrastructure.logging import get_logger
    
    logger = get_logger(__name__)
    tenant = get_current_tenant()
    
    logger.info(
        "Subgraph endpoint called",
        node_id=node_id,
        max_hops=max_hops,
        has_tenant=tenant is not None,
        tenant_id=tenant.tenant_id if tenant else None,
    )
    
    try:
        subgraph_result = extract_subgraph(node_id, max_hops, rel_types, node_labels)
    except Exception as e:
        logger.error("Error extracting subgraph", error=str(e), node_id=node_id, exc_info=True)
        # Return empty subgraph on error
        subgraph = Subgraph(nodes=[], relationships=[], center_node_id=node_id)
        if format == "visualization":
            return export_subgraph_for_visualization(subgraph)
        return subgraph.model_dump(mode="json")
    
    # Handle case where cache returns a dict instead of Subgraph object
    # (cache serializes/deserializes Pydantic models as dicts)
    if isinstance(subgraph_result, dict):
        # Reconstruct nested objects
        nodes = [GraphNode(**n) if isinstance(n, dict) else n for n in subgraph_result.get("nodes", [])]
        relationships = [GraphRelationship(**r) if isinstance(r, dict) else r for r in subgraph_result.get("relationships", [])]
        subgraph = Subgraph(
            nodes=nodes,
            relationships=relationships,
            center_node_id=subgraph_result.get("center_node_id")
        )
    elif isinstance(subgraph_result, str) and subgraph_result.strip():
        # If it's a non-empty string, try to parse it as JSON
        import json
        try:
            data = json.loads(subgraph_result)
            nodes = [GraphNode(**n) for n in data.get("nodes", [])]
            relationships = [GraphRelationship(**r) for r in data.get("relationships", [])]
            subgraph = Subgraph(
                nodes=nodes,
                relationships=relationships,
                center_node_id=data.get("center_node_id")
            )
        except json.JSONDecodeError:
            # If JSON parsing fails, return empty subgraph
            subgraph = Subgraph(nodes=[], relationships=[], center_node_id=node_id)
    else:
        # If it's already a Subgraph object or None/empty, use it directly
        if isinstance(subgraph_result, Subgraph):
            subgraph = subgraph_result
        else:
            # Return empty subgraph if result is None or invalid
            subgraph = Subgraph(nodes=[], relationships=[], center_node_id=node_id)

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
    format: str = Query("json", pattern="^(json|visualization)$"),
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


@router.get("/node/{node_id}/details")
def get_node_details(node_id: str) -> dict:
    """Get detailed information about a node including connections and owners."""
    from src.infrastructure.database.neo4j_client import neo4j_client
    
    # Get node basic info
    node_query = """
    MATCH (n {id: $node_id})
    RETURN n, labels(n) as labels
    LIMIT 1
    """
    node_rows = neo4j_client.execute_cypher(node_query, {"node_id": node_id})
    if not node_rows:
        raise HTTPException(status_code=404, detail="Node not found")
    
    node_data = node_rows[0]
    node_props = dict(node_data.get("n", {}))
    labels = node_data.get("labels", [])
    
    # Get owners (if Business)
    owners = []
    if "Business" in labels:
        owners_query = """
        MATCH (b:Business {id: $node_id})<-[:OWNS]-(owner)
        RETURN owner, labels(owner) as owner_labels, 
               [(owner)-[r:OWNS]->(b) | r.percentage] as ownership_percentages
        LIMIT 20
        """
        owners_rows = neo4j_client.execute_cypher(owners_query, {"node_id": node_id})
        for row in owners_rows:
            owner_props = dict(row.get("owner", {}))
            owner_labels = row.get("owner_labels", [])
            percentages = row.get("ownership_percentages", [])
            owners.append({
                "id": owner_props.get("id", ""),
                "name": owner_props.get("name", ""),
                "labels": owner_labels,
                "properties": owner_props,
                "ownership_percentage": percentages[0] if percentages else None,
            })
    
    # Get direct connections (1-hop neighbors)
    connections_query = """
    MATCH (n {id: $node_id})-[r]-(connected)
    RETURN connected, labels(connected) as connected_labels, 
           type(r) as rel_type, properties(r) as rel_props
    LIMIT 50
    """
    connections_rows = neo4j_client.execute_cypher(connections_query, {"node_id": node_id})
    connections = []
    for row in connections_rows:
        connected_props = dict(row.get("connected", {}))
        connected_labels = row.get("connected_labels", [])
        connections.append({
            "id": connected_props.get("id", ""),
            "name": connected_props.get("name", connected_props.get("id", "")),
            "labels": connected_labels,
            "properties": connected_props,
            "relationship_type": row.get("rel_type", ""),
            "relationship_properties": row.get("rel_props", {}),
        })
    
    return {
        "node": {
            "id": node_id,
            "name": node_props.get("name", node_id),
            "labels": labels,
            "properties": node_props,
        },
        "owners": owners,
        "connections": connections,
        "owner_count": len(owners),
        "connection_count": len(connections),
    }


@router.get("/transactions")
def list_transactions(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
) -> dict:
    """List all transactions with pagination and optional filters."""
    from src.infrastructure.database.neo4j_client import neo4j_client
    from src.tenancy.context import get_current_tenant
    from src.infrastructure.logging import get_logger
    
    logger = get_logger(__name__)
    tenant = get_current_tenant()
    logger.info(
        "Transactions endpoint called",
        has_tenant=tenant is not None,
        tenant_id=tenant.tenant_id if tenant else None,
    )
    
    conditions = []
    params = {"limit": limit, "offset": offset}
    
    if search:
        conditions.append("(t.description CONTAINS $search OR t.id CONTAINS $search)")
        params["search"] = search
    if transaction_type:
        conditions.append("t.type = $transaction_type")
        params["transaction_type"] = transaction_type
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    # Get total count - use node_alias='t' to match the Transaction alias
    count_query = f"MATCH (t:Transaction) WHERE {where_clause} RETURN count(t) as total"
    logger.info("Executing count query", query=count_query, params=params, tenant_id=tenant.tenant_id if tenant else None)
    count_rows = neo4j_client.execute_cypher(count_query, params, node_alias="t")
    total = count_rows[0]["total"] if count_rows else 0
    logger.info("Count query result", total=total, tenant_id=tenant.tenant_id if tenant else None)
    
    # Get transactions - use node_alias='t' to match the Transaction alias
    query = f"""
    MATCH (t:Transaction)
    WHERE {where_clause}
    OPTIONAL MATCH (t)-[:INVOLVES]->(p:Person)
    RETURN t, collect(DISTINCT {{id: p.id, name: p.name}}) as people
    ORDER BY t.date DESC, t.id ASC
    SKIP $offset LIMIT $limit
    """
    logger.info("Executing transactions query", query_preview=query[:200], params=params, tenant_id=tenant.tenant_id if tenant else None)
    rows = neo4j_client.execute_cypher(query, params, node_alias="t")
    logger.info("Transactions query result", row_count=len(rows), tenant_id=tenant.tenant_id if tenant else None)
    
    transactions = []
    for row in rows:
        tx_props = dict(row["t"])
        transactions.append({
            "id": tx_props.get("id", ""),
            "amount": tx_props.get("amount"),
            "currency": tx_props.get("currency", "KES"),
            "date": tx_props.get("date"),
            "type": tx_props.get("type"),
            "description": tx_props.get("description", ""),
            "source_provider": tx_props.get("source_provider", ""),
            "people": row.get("people", []),
            "properties": tx_props,
        })
    
    return {
        "transactions": transactions,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/people")
def list_people(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
) -> dict:
    """List all people with pagination and optional search."""
    from src.infrastructure.database.neo4j_client import neo4j_client
    
    conditions = []
    params = {"limit": limit, "offset": offset}
    
    if search:
        conditions.append("(p.name CONTAINS $search OR p.id CONTAINS $search)")
        params["search"] = search
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    # Get total count - use node_alias='p' to match the Person alias
    count_query = f"MATCH (p:Person) WHERE {where_clause} RETURN count(p) as total"
    count_rows = neo4j_client.execute_cypher(count_query, params, node_alias="p")
    total = count_rows[0]["total"] if count_rows else 0
    
    # Get people with transaction counts - use node_alias='p' to match the Person alias
    query = f"""
    MATCH (p:Person)
    WHERE {where_clause}
    OPTIONAL MATCH (p)<-[:INVOLVES]-(t:Transaction)
    RETURN p, count(DISTINCT t) as transaction_count
    ORDER BY transaction_count DESC, p.name ASC
    SKIP $offset LIMIT $limit
    """
    rows = neo4j_client.execute_cypher(query, params, node_alias="p")
    
    people = []
    for row in rows:
        person_props = dict(row["p"])
        people.append({
            "id": person_props.get("id", ""),
            "name": person_props.get("name", "Unknown"),
            "transaction_count": row.get("transaction_count", 0),
            "properties": person_props,
        })
    
    return {
        "people": people,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
