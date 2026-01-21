"""Detect rapid succession / structuring transactions."""
from __future__ import annotations

from typing import List

from src.infrastructure.database.neo4j_client import neo4j_client

from ..models import FraudPatternHit


def detect_structuring(business_id: str) -> List[FraudPatternHit]:
    """
    Detect many small transactions in short time windows (smurfing).
    """
    query = """
    MATCH (b:Business {id: $business_id})-[:INVOLVES]-(t:Transaction)
    WITH b, t
    ORDER BY t.date, t.time
    WITH b,
         collect({dt: datetime({date: t.date, time: t.time}), amount: t.amount}) AS txs
    UNWIND txs AS tx
    WITH b, tx,
         [x IN txs WHERE x.dt >= tx.dt AND x.dt <= tx.dt + duration('PT1H')] AS window
    WITH b,
         tx.dt AS start_dt,
         size(window) AS count_in_hour,
         reduce(s = 0.0, x IN window | s + coalesce(x.amount, 0)) AS total_amount
    WHERE count_in_hour >= 5 AND total_amount < 100000
    RETURN start_dt, count_in_hour, total_amount
    LIMIT 50
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    hits: List[FraudPatternHit] = []
    for row in rows:
        hits.append(
            FraudPatternHit(
                pattern="structuring",
                description="Multiple smaller transactions within 1 hour (possible structuring).",
                business_id=business_id,
                score_contribution=7.0,
                context={
                    "start_dt": row.get("start_dt"),
                    "count_in_hour": row.get("count_in_hour"),
                    "total_amount": row.get("total_amount"),
                },
            )
        )
    return hits

