"""Connected components analysis."""
from typing import List, Optional

from src.infrastructure.database.neo4j_client import neo4j_client

from .models import ConnectedComponent, GraphNode, GraphRelationship


def find_connected_components(
    node_label: Optional[str] = None,
    rel_types: Optional[List[str]] = None,
    min_size: int = 2,
) -> List[ConnectedComponent]:
    """
    Find all connected components in the graph.

    Uses APOC's weakly connected components algorithm.
    """
    label_filter = f":{node_label}" if node_label else ""
    rel_filter = ""
    if rel_types:
        types_str = "|".join(rel_types)
        rel_filter = f":{types_str}"

    # Use APOC to find components
    query = f"""
    CALL apoc.path.subgraphNodes(
        (n{label_filter}),
        {{
            relationshipFilter: "{rel_filter[1:] if rel_filter else ''}",
            minLevel: 0,
            maxLevel: -1
        }}
    ) YIELD node
    WITH collect(DISTINCT id(node)) as component_nodes
    WHERE size(component_nodes) >= $min_size
    WITH component_nodes
    ORDER BY size(component_nodes) DESC
    LIMIT 50
    UNWIND component_nodes as node_id
    MATCH (n) WHERE id(n) = node_id
    WITH collect(DISTINCT n) as nodes, component_nodes[0] as first_id
    MATCH (a)-[r{rel_filter}]-(b)
    WHERE id(a) IN component_nodes AND id(b) IN component_nodes
    WITH nodes, collect(DISTINCT r) as rels, size(nodes) as comp_size
    RETURN 
        [n in nodes | {{id: id(n), labels: labels(n), props: properties(n)}}] as nodes,
        [r in rels | {{type: type(r), from: id(startNode(r)), to: id(endNode(r)), props: properties(r)}}] as relationships,
        comp_size as size
    """
    rows = neo4j_client.execute_cypher(query, {"min_size": min_size})

    components = []
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
            for r in row.get("relationships", [])
        ]
        components.append(
            ConnectedComponent(
                nodes=nodes, relationships=rels, size=row.get("size", len(nodes))
            )
        )

    return components


def get_component_for_node(node_id: str) -> Optional[ConnectedComponent]:
    """Get the connected component containing a specific node."""
    query = """
    MATCH (start) WHERE id(start) = $node_id
    CALL apoc.path.subgraphNodes(
        start,
        {
            relationshipFilter: "",
            minLevel: 0,
            maxLevel: -1
        }
    ) YIELD node
    WITH collect(DISTINCT id(node)) as component_nodes
    UNWIND component_nodes as node_id
    MATCH (n) WHERE id(n) = node_id
    WITH collect(DISTINCT n) as nodes
    MATCH (a)-[r]-(b)
    WHERE id(a) IN component_nodes AND id(b) IN component_nodes
    WITH nodes, collect(DISTINCT r) as rels
    RETURN 
        [n in nodes | {id: id(n), labels: labels(n), props: properties(n)}] as nodes,
        [r in rels | {type: type(r), from: id(startNode(r)), to: id(endNode(r)), props: properties(r)}] as relationships,
        size(nodes) as size
    """
    rows = neo4j_client.execute_cypher(query, {"node_id": int(node_id)})
    if not rows:
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
        for r in row.get("relationships", [])
    ]
    return ConnectedComponent(nodes=nodes, relationships=rels, size=row.get("size", len(nodes)))
