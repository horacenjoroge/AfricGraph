"""Detect unusual payment patterns (simple heuristic)."""
from __future__ import annotations

from typing import List

from src.infrastructure.database.neo4j_client import neo4j_client

from ..models import FraudPatternHit


def detect_unusual_patterns(business_id: str) -> List[FraudPatternHit]:
    """
    Simple anomaly heuristic:
      - Compares recent average transaction size to historical median.
    """
    query = """
    MATCH (b:Business {id: $business_id})-[:INVOLVES]-(t:Transaction)
    WITH b, t
    ORDER BY t.date DESC, t.time DESC
    WITH b,
         collect(t.amount) AS amounts
    WITH b,
         amounts,
         amounts[0..20] AS recent,
         CASE WHEN size(amounts) = 0 THEN 0 ELSE percentileCont(amounts, 0.5) END AS median_all
    WITH b,
         median_all,
         CASE WHEN size(recent) = 0 THEN 0 ELSE reduce(s=0.0, x IN recent | s + x) / size(recent) END AS avg_recent
    WHERE median_all > 0 AND (avg_recent > median_all * 3 OR avg_recent < median_all * 0.2)
    RETURN median_all, avg_recent
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    if not rows:
        return []
    row = rows[0]
    median_all = float(row.get("median_all") or 0.0)
    avg_recent = float(row.get("avg_recent") or 0.0)
    if median_all <= 0:
        return []

    return [
        FraudPatternHit(
            pattern="unusual_patterns",
            description="Recent transaction sizes deviate strongly from historical median.",
            business_id=business_id,
            score_contribution=10.0,
            context={"median_all": median_all, "avg_recent": avg_recent},
        )
    ]

