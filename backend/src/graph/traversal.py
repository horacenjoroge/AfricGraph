"""Graph traversal operations: subgraph extraction, path finding."""
from typing import List, Optional

from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.logging import get_logger
from src.cache.integrations import cached_graph_query
from src.cache.config import CacheKey, CacheTTL

from .models import GraphNode, GraphRelationship, Path, Subgraph

logger = get_logger(__name__)


@cached_graph_query(key_type=CacheKey.SUBGRAPH, ttl=CacheTTL.SUBGRAPH)
def extract_subgraph(
    node_id: str,
    max_hops: int = 2,
    rel_types: Optional[List[str]] = None,
    node_labels: Optional[List[str]] = None,
) -> Subgraph:
    """
    Extract N-hop neighborhood subgraph from a starting node.

    Returns all nodes and relationships within max_hops distance.
    """
    rel_filter = ""
    if rel_types:
        types_str = "|".join(rel_types)
        rel_filter = f":{types_str}"

    node_filter = ""
    if node_labels:
        labels_str = ":".join(node_labels)
        node_filter = f"AND '{labels_str}' IN labels(n)"

    # Optimized query to prevent memory issues
    # Use a simpler pattern that limits results and avoids collecting all paths
    # Limit to 200 nodes max to prevent memory overflow
    max_nodes_limit = 200
    query = f"""
    MATCH (start {{id: $node_id}})
    // Get distinct nodes within max_hops (limited to prevent memory issues)
    MATCH (start)-[{rel_filter}*1..{max_hops}]-(n)
    {node_filter}
    WITH start, collect(DISTINCT n) as all_nodes
    // Limit nodes to prevent memory overflow - use head() function
    WITH start, 
         all_nodes[0..{max_nodes_limit}] as nodes
    // Get relationships only between the limited set of nodes
    UNWIND nodes as n1
    UNWIND nodes as n2
    WITH start, nodes, n1, n2
    WHERE id(n1) < id(n2)
    OPTIONAL MATCH (n1)-[r{rel_filter}]-(n2)
    // Filter out NULL relationships (when OPTIONAL MATCH doesn't find a relationship)
    WITH start, nodes, n1, n2, r
    WHERE r IS NOT NULL
    WITH start, nodes, collect(DISTINCT {{
        from: coalesce(n1.id, toString(id(n1))),
        to: coalesce(n2.id, toString(id(n2))),
        type: type(r),
        props: properties(r)
    }}) as relationships
    RETURN 
        start.id as center_id,
        [x in nodes | {{
            id: coalesce(x.id, toString(id(x))), 
            labels: labels(x), 
            props: properties(x)
        }}] as nodes,
        relationships
    LIMIT 1
    """
    rows = neo4j_client.execute_cypher(query, {"node_id": node_id})
    if not rows:
        return Subgraph(nodes=[], relationships=[], center_node_id=node_id)

    row = rows[0]
    nodes = [
        GraphNode(id=str(n["id"]), labels=n.get("labels", []), properties=n.get("props", {}))
        for n in row.get("nodes", [])
    ]
    # Add center node if not already included
    center_id = str(row.get("center_id", node_id))
    if not any(n.id == center_id for n in nodes):
        # Try to find center node by id property
        center_query = "MATCH (n {id: $node_id}) RETURN n, labels(n) as labels LIMIT 1"
        center_rows = neo4j_client.execute_cypher(center_query, {"node_id": center_id})
        if center_rows:
            center_data = center_rows[0]
            center_node = center_data.get("n", {})
            center_labels = center_data.get("labels", [])
            nodes.insert(0, GraphNode(id=center_id, labels=center_labels, properties=center_node))

    rels = [
        GraphRelationship(
            type=r["type"],
            from_id=str(r["from"]),
            to_id=str(r["to"]),
            properties=r.get("props", {}) or {},
        )
        for r in row.get("relationships", [])
        if r.get("type") is not None  # Skip NULL relationships (defensive check)
    ]

    return Subgraph(nodes=nodes, relationships=rels, center_node_id=center_id)


@cached_graph_query(key_type=CacheKey.PATH, ttl=CacheTTL.PATH)
def find_shortest_path(
    start_id: str,
    end_id: str,
    max_depth: int = 10,
    rel_types: Optional[List[str]] = None,
) -> Optional[Path]:
    """Find shortest path between two nodes."""
    rel_filter = ""
    if rel_types:
        types_str = "|".join(rel_types)
        rel_filter = f":{types_str}"

    query = f"""
    MATCH (a {{id: $start_id}}), (b {{id: $end_id}})
    MATCH path = shortestPath((a)-[{rel_filter}*1..{max_depth}]->(b))
    RETURN 
        [n in nodes(path) | {{id: coalesce(n.id, toString(id(n))), labels: labels(n), props: properties(n)}}] as nodes,
        [r in relationships(path) | {{type: type(r), from: coalesce(startNode(r).id, toString(id(startNode(r)))), to: coalesce(endNode(r).id, toString(id(endNode(r)))), props: properties(r)}}] as rels,
        length(path) as path_length
    """
    rows = neo4j_client.execute_cypher(query, {"start_id": start_id, "end_id": end_id})
    if not rows or not rows[0].get("nodes"):
        return None

    row = rows[0]
    nodes = [
        GraphNode(id=str(n["id"]), labels=n.get("labels", []), properties=n.get("props", {}))
        for n in row.get("nodes", [])
    ]
    rels = [
        GraphRelationship(
            type=r["type"],
            from_id=str(r["from"]),
            to_id=str(r["to"]),
            properties=r.get("props", {}),
        )
        for r in row.get("rels", [])
    ]

    return Path(nodes=nodes, relationships=rels, length=row.get("path_length", 0))


def find_all_paths(
    start_id: str,
    end_id: str,
    max_depth: int = 5,
    limit: int = 100,
    rel_types: Optional[List[str]] = None,
) -> List[Path]:
    """Find all paths between two nodes (up to limit)."""
    rel_filter = ""
    if rel_types:
        types_str = "|".join(rel_types)
        rel_filter = f":{types_str}"

    query = f"""
    MATCH (a {{id: $start_id}}), (b {{id: $end_id}})
    MATCH path = (a)-[{rel_filter}*1..{max_depth}]->(b)
    RETURN 
        [n in nodes(path) | {{id: coalesce(n.id, toString(id(n))), labels: labels(n), props: properties(n)}}] as nodes,
        [r in relationships(path) | {{type: type(r), from: coalesce(startNode(r).id, toString(id(startNode(r)))), to: coalesce(endNode(r).id, toString(id(endNode(r)))), props: properties(r)}}] as rels,
        length(path) as path_length
    ORDER BY path_length ASC
    LIMIT $limit
    """
    rows = neo4j_client.execute_cypher(
        query, {"start_id": start_id, "end_id": end_id, "limit": limit}
    )

    paths = []
    for row in rows:
        nodes = [
            GraphNode(id=str(n["id"]), labels=n.get("labels", []), properties=n.get("props", {}))
            for n in row.get("nodes", [])
        ]
        rels = [
            GraphRelationship(
                type=r["type"],
                from_id=str(r["from"]),
                to_id=str(r["to"]),
                properties=r.get("props", {}),
            )
            for r in row.get("rels", [])
        ]
        paths.append(Path(nodes=nodes, relationships=rels, length=row.get("path_length", 0)))

    return paths
