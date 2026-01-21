"""Supplier concentration analyzer using HHI index."""
from __future__ import annotations

from typing import Dict

from src.infrastructure.database.neo4j_client import neo4j_client

from .models import FactorScore


def analyze_supplier_concentration(business_id: str) -> FactorScore:
    """
    Compute supplier concentration score (0-100) using a simple HHI-style heuristic.

    Assumes relationships:
      (b:Business {id: $business_id})-[:BUYS_FROM]->(s:Supplier)
      and optionally weights via relationships or transaction volumes.
    """
    query = """
    MATCH (b:Business {id: $business_id})-[:BUYS_FROM]->(s:Supplier)
    OPTIONAL MATCH (b)-[:BUYS_FROM]->(s)-[:INVOLVES|:SUPPLIES*0..1]->(t:Transaction)
    WITH s, coalesce(sum(t.amount), 1.0) AS volume
    WITH collect(volume) AS vols
    WITH vols, reduce(total = 0.0, v IN vols | total + v) AS total
    WITH [v IN vols | v / CASE WHEN total = 0.0 THEN 1.0 ELSE total END] AS shares
    WITH shares, reduce(hhi = 0.0, s IN shares | hhi + s * s) AS hhi
    RETURN hhi, size(shares) AS supplier_count
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    if not rows:
        return FactorScore(
            name="supplier_concentration",
            score=50.0,
            details={"reason": "no_suppliers"},
        )
    row = rows[0]
    hhi = row.get("hhi") or 0.0
    supplier_count = row.get("supplier_count") or 0

    if supplier_count == 0:
        return FactorScore(
            name="supplier_concentration",
            score=50.0,
            details={"reason": "no_suppliers"},
        )

    # For HHI in [0,1], map high concentration (1) -> low score, diversified (~0) -> high score.
    # Score = (1 - hhi) * 100, but clamp.
    score = max(0.0, min(100.0, (1.0 - min(hhi, 1.0)) * 100.0))

    return FactorScore(
        name="supplier_concentration",
        score=score,
        details={
            "hhi": hhi,
            "supplier_count": supplier_count,
        },
    )

