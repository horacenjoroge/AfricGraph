"""Dependency graph extraction for supplier relationships."""
from __future__ import annotations

from typing import Dict, List, TypedDict

from src.infrastructure.database.neo4j_client import neo4j_client


class GraphNode(TypedDict):
    id: int
    labels: List[str]
    props: Dict


class GraphRel(TypedDict):
    type: str
    from_id: int
    to_id: int
    props: Dict


class SupplierDependencyGraph(TypedDict):
    business_internal_id: int | None
    nodes: List[GraphNode]
    relationships: List[GraphRel]


def build_supplier_dependency_graph(business_id: str) -> SupplierDependencyGraph:
    """
    Build a small dependency graph of a business and its suppliers for visualization.

    Extracts:
      - The business node
      - Direct suppliers
      - BUYS_FROM relationships
    """
    query = """
    MATCH (b:Business {id: $business_id})
    OPTIONAL MATCH (b)-[r:BUYS_FROM]->(s:Supplier)
    RETURN
      id(b) AS business_internal_id,
      collect(DISTINCT {id: id(b), labels: labels(b), props: properties(b)}) +
      collect(DISTINCT {id: id(s), labels: labels(s), props: properties(s)}) AS nodes,
      collect(DISTINCT {type: type(r), from_id: id(b), to_id: id(s), props: properties(r)}) AS rels
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    if not rows:
        return SupplierDependencyGraph(
            business_internal_id=None,
            nodes=[],
            relationships=[],
        )
    row = rows[0]
    nodes = row.get("nodes") or []
    rels = row.get("rels") or []
    return SupplierDependencyGraph(
        business_internal_id=row.get("business_internal_id"),
        nodes=nodes,
        relationships=rels,
    )

