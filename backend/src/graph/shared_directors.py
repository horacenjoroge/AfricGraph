"""Shared director discovery between entities."""
from typing import Dict, List

from src.infrastructure.database.neo4j_client import neo4j_client

from .models import GraphNode


def find_shared_directors(entity_a_id: str, entity_b_id: str) -> Dict:
    """
    Find shared directors between two businesses.

    Returns persons who are directors of both entities.
    """
    query = """
    MATCH (a), (b) WHERE id(a) = $entity_a_id AND id(b) = $entity_b_id
    MATCH (director:Person)-[:DIRECTOR_OF]->(a), (director)-[:DIRECTOR_OF]->(b)
    WITH director,
         [(director)-[r1:DIRECTOR_OF]->(a) | r1.role] as role_a,
         [(director)-[r2:DIRECTOR_OF]->(b) | r2.role] as role_b
    RETURN 
        id(director) as director_id,
        labels(director) as director_labels,
        properties(director) as director_props,
        role_a[0] as role_a,
        role_b[0] as role_b
    """
    rows = neo4j_client.execute_cypher(
        query, {"entity_a_id": int(entity_a_id), "entity_b_id": int(entity_b_id)}
    )

    shared_directors = []
    for row in rows:
        director_node = GraphNode(
            id=str(row["director_id"]),
            labels=row.get("director_labels", []),
            properties=row.get("director_props", {}),
        )
        shared_directors.append(
            {
                "director": director_node.model_dump(mode="json"),
                "role_at_a": row.get("role_a"),
                "role_at_b": row.get("role_b"),
            }
        )

    return {
        "entity_a_id": entity_a_id,
        "entity_b_id": entity_b_id,
        "shared_directors": shared_directors,
        "count": len(shared_directors),
    }


def find_director_network_path(entity_a_id: str, entity_b_id: str) -> Optional[Dict]:
    """
    Find path connecting two entities through director relationships.

    Looks for paths like: EntityA <-DIRECTOR_OF- Person -DIRECTOR_OF-> EntityB
    or longer chains through multiple directors.
    """
    query = """
    MATCH (a), (b) WHERE id(a) = $entity_a_id AND id(b) = $entity_b_id
    MATCH path = shortestPath((a)<-[:DIRECTOR_OF*1..3]-(:Person)-[:DIRECTOR_OF*1..3]->(b))
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
    from .models import GraphRelationship

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
