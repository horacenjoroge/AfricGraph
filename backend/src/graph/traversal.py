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

    query = f"""
    MATCH (start) WHERE id(start) = $node_id
    MATCH path = (start)-[{rel_filter}*1..{max_hops}]-(n)
    {node_filter}
    WITH start, collect(DISTINCT n) as nodes, relationships(path) as rels
    UNWIND rels as r
    WITH start, nodes, collect(DISTINCT r) as rel_list
    RETURN 
        id(start) as center_id,
        [x in nodes | {{id: id(x), labels: labels(x), props: properties(x)}}] as nodes,
        [x in rel_list | {{type: type(x), from: id(startNode(x)), to: id(endNode(x)), props: properties(x)}}] as relationships
    """
    rows = neo4j_client.execute_cypher(query, {"node_id": int(node_id)})
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
        center_node = neo4j_client.find_node("Business", {"id": center_id})
        if center_node:
            nodes.insert(0, GraphNode(id=center_id, labels=["Business"], properties=center_node))

    rels = [
        GraphRelationship(
            type=r["type"],
            from_id=str(r["from"]),
            to_id=str(r["to"]),
            properties=r.get("props", {}),
        )
        for r in row.get("relationships", [])
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
    MATCH (a), (b) WHERE id(a) = $start_id AND id(b) = $end_id
    MATCH path = shortestPath((a)-[{rel_filter}*1..{max_depth}]->(b))
    RETURN 
        [n in nodes(path) | {{id: id(n), labels: labels(n), props: properties(n)}}] as nodes,
        [r in relationships(path) | {{type: type(r), from: id(startNode(r)), to: id(endNode(r)), props: properties(r)}}] as rels,
        length(path) as path_length
    """
    rows = neo4j_client.execute_cypher(query, {"start_id": int(start_id), "end_id": int(end_id)})
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
    MATCH (a), (b) WHERE id(a) = $start_id AND id(b) = $end_id
    MATCH path = (a)-[{rel_filter}*1..{max_depth}]->(b)
    RETURN 
        [n in nodes(path) | {{id: id(n), labels: labels(n), props: properties(n)}}] as nodes,
        [r in relationships(path) | {{type: type(r), from: id(startNode(r)), to: id(endNode(r)), props: properties(r)}}] as rels,
        length(path) as path_length
    ORDER BY path_length ASC
    LIMIT $limit
    """
    rows = neo4j_client.execute_cypher(
        query, {"start_id": int(start_id), "end_id": int(end_id), "limit": limit}
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
