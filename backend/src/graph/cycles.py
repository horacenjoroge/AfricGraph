"""Cycle detection in graph."""
from typing import List, Optional

from src.infrastructure.database.neo4j_client import neo4j_client

from .models import Cycle, GraphNode, GraphRelationship


def detect_cycles(
    start_node_id: Optional[str] = None,
    max_depth: int = 10,
    rel_types: Optional[List[str]] = None,
) -> List[Cycle]:
    """
    Detect cycles in the graph.

    If start_node_id is provided, only detect cycles involving that node.
    Otherwise, detect all cycles (may be expensive on large graphs).
    """
    rel_filter = ""
    if rel_types:
        types_str = "|".join(rel_types)
        rel_filter = f":{types_str}"

    if start_node_id:
        # Cycles involving specific node
        query = f"""
        MATCH (start) WHERE id(start) = $node_id
        MATCH path = (start)-[{rel_filter}*2..{max_depth}]->(start)
        WHERE length(path) >= 2
        RETURN DISTINCT
            [n in nodes(path) | {{id: id(n), labels: labels(n), props: properties(n)}}] as nodes,
            [r in relationships(path) | {{type: type(r), from: id(startNode(r)), to: id(endNode(r)), props: properties(r)}}] as rels,
            length(path) as cycle_length
        LIMIT 100
        """
        rows = neo4j_client.execute_cypher(query, {"node_id": int(start_node_id)})
    else:
        # All cycles (more expensive)
        query = f"""
        MATCH path = (a)-[{rel_filter}*2..{max_depth}]->(a)
        WHERE length(path) >= 2
        WITH path, a, length(path) as cycle_length
        ORDER BY cycle_length ASC
        RETURN DISTINCT
            [n in nodes(path) | {{id: id(n), labels: labels(n), props: properties(n)}}] as nodes,
            [r in relationships(path) | {{type: type(r), from: id(startNode(r)), to: id(endNode(r)), props: properties(r)}}] as rels,
            cycle_length
        LIMIT 100
        """
        rows = neo4j_client.execute_cypher(query, {})

    cycles = []
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
        cycles.append(Cycle(nodes=nodes, relationships=rels, length=row.get("cycle_length", 0)))

    return cycles
