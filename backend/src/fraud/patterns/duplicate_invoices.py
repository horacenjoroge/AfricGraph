"""Detect duplicate invoices."""
from __future__ import annotations

from typing import List

from src.infrastructure.database.neo4j_client import neo4j_client

from ..models import FraudPatternHit


def detect_duplicate_invoices(business_id: str) -> List[FraudPatternHit]:
    """
    Detect invoices with same number, amount, and counterparty for the same business.
    """
    query = """
    MATCH (b:Business {id: $business_id})-[:ISSUED]->(i1:Invoice)
    MATCH (b)-[:ISSUED]->(i2:Invoice)
    WHERE i1 <> i2
      AND i1.number = i2.number
      AND i1.amount = i2.amount
      AND coalesce(i1.currency, '') = coalesce(i2.currency, '')
    RETURN DISTINCT i1.number AS number, i1.amount AS amount, i1.currency AS currency, count(*) AS cnt
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    hits: List[FraudPatternHit] = []
    for row in rows:
        hits.append(
            FraudPatternHit(
                pattern="duplicate_invoices",
                description="Potential duplicate invoices detected.",
                business_id=business_id,
                score_contribution=8.0,
                context={
                    "number": row.get("number"),
                    "amount": row.get("amount"),
                    "currency": row.get("currency"),
                    "count": row.get("cnt"),
                },
            )
        )
    return hits

