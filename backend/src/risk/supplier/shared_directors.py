"""Shared director detection between business and suppliers."""
from __future__ import annotations

from typing import List, TypedDict

from src.infrastructure.database.neo4j_client import neo4j_client


class SharedDirectorHit(TypedDict):
    supplier_id: str
    supplier_name: str | None
    director_count: int


def find_shared_directors(business_id: str) -> List[SharedDirectorHit]:
    """
    Find suppliers that share directors with the given business.
    """
    query = """
    MATCH (b:Business {id: $business_id})-[:BUYS_FROM]->(s:Supplier)
    MATCH (d:Person)-[:DIRECTOR_OF]->(b)
    MATCH (d)-[:DIRECTOR_OF]->(s)
    RETURN s.id AS supplier_id, s.name AS supplier_name, count(DISTINCT d) AS director_count
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    hits: List[SharedDirectorHit] = []
    for r in rows:
        hits.append(
            SharedDirectorHit(
                supplier_id=str(r.get("supplier_id")),
                supplier_name=r.get("supplier_name"),
                director_count=int(r.get("director_count") or 0),
            )
        )
    return hits

