"""Detect suspicious round-amount transactions."""
from __future__ import annotations

from typing import List

from src.infrastructure.database.neo4j_client import neo4j_client

from ..models import FraudPatternHit


def detect_round_amounts(business_id: str) -> List[FraudPatternHit]:
    """
    Detect an unusually high share of round-amount transactions for a business.
    """
    query = """
    MATCH (b:Business {id: $business_id})-[:INVOLVES]-(t:Transaction)
    WITH b,
         count(t) AS total,
         count(CASE WHEN t.amount % 100 = 0 THEN 1 END) AS round_count
    WHERE total >= 10
    RETURN total, round_count, round_count * 1.0 / total AS ratio
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    if not rows:
        return []
    row = rows[0]
    total = row.get("total") or 0
    round_count = row.get("round_count") or 0
    ratio = float(row.get("ratio") or 0.0)
    if total < 10 or ratio < 0.5:
        return []

    return [
        FraudPatternHit(
            pattern="round_amounts",
            description="High share of round-amount transactions.",
            business_id=business_id,
            score_contribution=5.0 + min(10.0, ratio * 20.0),
            context={"total": total, "round_count": round_count, "ratio": ratio},
        )
    ]

