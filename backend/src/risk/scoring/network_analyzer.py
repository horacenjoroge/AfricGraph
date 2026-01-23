"""Network exposure analyzer: connected high-risk entities."""
from __future__ import annotations

from typing import Dict

from src.infrastructure.database.neo4j_client import neo4j_client

from .models import FactorScore


def analyze_network_exposure(business_id: str) -> FactorScore:
    """
    Compute network exposure score (0-100).

    Heuristic:
      - Counts known high-risk counterparties within N hops.
      - More high-risk neighbors -> lower score.
    """
    query = """
    MATCH (b:Business {id: $business_id})
    OPTIONAL MATCH path = (b)-[:INVOLVES|BUYS_FROM|SELLS_TO*1..3]-(other:Business)
    WHERE other.high_risk_flag = true
    WITH collect(DISTINCT other) AS risky
    RETURN size(risky) AS risky_count
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    if not rows:
        return FactorScore(
            name="network_exposure",
            score=50.0,
            details={"reason": "no_network_data"},
        )
    risky_count = rows[0].get("risky_count") or 0

    if risky_count == 0:
        return FactorScore(
            name="network_exposure",
            score=100.0,
            details={"risky_neighbors": 0},
        )

    # Simple mapping: up to 20 risky neighbors; beyond that, clamp at 0.
    risk_ratio = min(risky_count / 20.0, 1.0)
    score = max(0.0, 100.0 * (1.0 - risk_ratio))

    return FactorScore(
        name="network_exposure",
        score=score,
        details={"risky_neighbors": risky_count},
    )

