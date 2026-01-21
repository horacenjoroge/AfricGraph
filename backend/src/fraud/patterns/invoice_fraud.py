"""Detect invoice fraud patterns (fake suppliers, inflated amounts)."""
from __future__ import annotations

from typing import List

from src.infrastructure.database.neo4j_client import neo4j_client

from ..models import FraudPatternHit


def detect_invoice_fraud_signals(business_id: str) -> List[FraudPatternHit]:
    """
    Heuristic invoice fraud:
      - Invoices linked to suppliers with little or no history.
      - Amounts significantly higher than median for that supplier.
    """
    query = """
    MATCH (b:Business {id: $business_id})-[:BUYS_FROM]->(s:Supplier)
    MATCH (s)-[:ISSUED]->(i:Invoice)
    OPTIONAL MATCH (s)-[:ISSUED]->(all:Invoice)
    WITH b, s, i,
         percentileCont(all.amount, 0.5) AS median_amount,
         count(all) AS supplier_invoice_count
    WHERE supplier_invoice_count <= 3
       OR i.amount > median_amount * 2.5
    RETURN s.id AS supplier_id,
           i.number AS invoice_number,
           i.amount AS amount,
           median_amount,
           supplier_invoice_count
    LIMIT 50
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    hits: List[FraudPatternHit] = []
    for row in rows:
        supplier_invoice_count = row.get("supplier_invoice_count") or 0
        median_amount = float(row.get("median_amount") or 0.0)
        amount = float(row.get("amount") or 0.0)
        score = 0.0
        if supplier_invoice_count <= 3:
            score += 6.0
        if median_amount and amount > median_amount * 2.5:
            score += 8.0
        hits.append(
            FraudPatternHit(
                pattern="invoice_fraud",
                description="Suspicious invoice characteristics for supplier.",
                business_id=business_id,
                score_contribution=score or 5.0,
                context={
                    "supplier_id": row.get("supplier_id"),
                    "invoice_number": row.get("invoice_number"),
                    "amount": amount,
                    "median_amount": median_amount,
                    "supplier_invoice_count": supplier_invoice_count,
                },
            )
        )
    return hits

