"""Common ownership detection between entities."""
from typing import Dict, List

from src.infrastructure.database.neo4j_client import neo4j_client

from .models import GraphNode, GraphRelationship


def find_common_owners(entity_a_id: str, entity_b_id: str) -> Dict:
    """
    Find common owners (persons or businesses) between two entities.

    Returns owners that have OWNS relationships to both entities.
    """
    query = """
    MATCH (a), (b) WHERE id(a) = $entity_a_id AND id(b) = $entity_b_id
    MATCH (owner)-[:OWNS]->(a), (owner)-[:OWNS]->(b)
    WITH owner, 
         [(owner)-[r1:OWNS]->(a) | r1.percentage] as pct_a,
         [(owner)-[r2:OWNS]->(b) | r2.percentage] as pct_b
    RETURN 
        id(owner) as owner_id,
        labels(owner) as owner_labels,
        properties(owner) as owner_props,
        pct_a[0] as ownership_a,
        pct_b[0] as ownership_b
    """
    rows = neo4j_client.execute_cypher(
        query, {"entity_a_id": int(entity_a_id), "entity_b_id": int(entity_b_id)}
    )

    common_owners = []
    for row in rows:
        owner_node = GraphNode(
            id=str(row["owner_id"]),
            labels=row.get("owner_labels", []),
            properties=row.get("owner_props", {}),
        )
        common_owners.append(
            {
                "owner": owner_node.model_dump(mode="json"),
                "ownership_percentage_a": row.get("ownership_a"),
                "ownership_percentage_b": row.get("ownership_b"),
            }
        )

    return {
        "entity_a_id": entity_a_id,
        "entity_b_id": entity_b_id,
        "common_owners": common_owners,
        "count": len(common_owners),
    }


def find_ownership_path(entity_a_id: str, entity_b_id: str) -> Optional[Dict]:
    """
    Find ownership chain connecting two entities.

    Looks for paths through OWNS relationships.
    """
    query = """
    MATCH (a), (b) WHERE id(a) = $entity_a_id AND id(b) = $entity_b_id
    MATCH path = shortestPath((a)-[:OWNS*1..5]-(b))
    RETURN 
        [n in nodes(path) | {id: id(n), labels: labels(n), props: properties(n)}] as nodes,
        [r in relationships(path) | {type: type(r), from: id(startNode(r)), to: id(endNode(r)), props: properties(r)}] as rels,
        length(path) as path_length
    LIMIT 1
    """
    rows = neo4j_client.execute_cypher(
        query, {"entity_a_id": int(entity_a_id), "entity_b_id": int(entity_b_id)}
    )

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

    return {
        "nodes": [n.model_dump(mode="json") for n in nodes],
        "relationships": [r.model_dump(mode="json") for r in rels],
        "path_length": row.get("path_length", 0),
    }
