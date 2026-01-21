"""Detect circular payment patterns A->B->C->A."""
from __future__ import annotations

from typing import List

from src.infrastructure.database.neo4j_client import neo4j_client

from ..models import FraudPatternHit


def detect_circular_payments(business_id: str) -> List[FraudPatternHit]:
    """
    Find short payment cycles involving the given business.

    Assumes:
      (a:Business)-[:SENT]->(t1:Transaction)-[:TO]->(b:Business) etc.
    """
    query = """
    MATCH (b:Business {id: $business_id})
    MATCH path = (b)-[:SENT]->(:Transaction)-[:TO]->(:Business)-[:SENT]->(:Transaction)-[:TO]->(b)
    RETURN DISTINCT path LIMIT 50
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    hits: List[FraudPatternHit] = []
    for idx, row in enumerate(rows):
        hits.append(
            FraudPatternHit(
                pattern="circular_payments",
                description="Detected circular payment path involving this business.",
                business_id=business_id,
                score_contribution=10.0,
                context={"path_index": idx},
            )
        )
    return hits

