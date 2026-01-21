"""Cash flow trend analyzer."""
from __future__ import annotations

from typing import Dict

from src.infrastructure.database.neo4j_client import neo4j_client

from .models import FactorScore


def analyze_cashflow_health(business_id: str) -> FactorScore:
    """
    Compute cash flow health score (0-100).

    Heuristic:
      - Based on net cash flow trend over recent periods (e.g. months).
      - Positive and improving -> higher score, negative and deteriorating -> lower.
    """
    query = """
    // Aggregate monthly incoming and outgoing amounts for this business
    MATCH (b:Business {id: $business_id})-[:INVOLVES]-(t:Transaction)
    WITH t, date.truncate('month', t.date) AS m, t.amount AS amt, t.type AS ttype
    WITH m,
         sum(CASE WHEN ttype = 'inflow' THEN amt ELSE 0 END) AS inflow,
         sum(CASE WHEN ttype = 'outflow' THEN amt ELSE 0 END) AS outflow
    WITH m, inflow, outflow, inflow - outflow AS net
    ORDER BY m ASC
    RETURN collect({month: m, net: net}) AS series
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    if not rows or not rows[0].get("series"):
        return FactorScore(
            name="cashflow_health",
            score=50.0,
            details={"reason": "no_cashflow_data"},
        )
    series = rows[0]["series"]
    if not series:
        return FactorScore(
            name="cashflow_health",
            score=50.0,
            details={"reason": "no_cashflow_data"},
        )

    nets = [row.get("net", 0.0) for row in series]
    if not nets:
        return FactorScore(
            name="cashflow_health",
            score=50.0,
            details={"reason": "no_cashflow_data"},
        )

    # Recent window (last 6 months if available).
    window = nets[-6:]
    avg_net = sum(window) / len(window)
    # Simple trend: difference between last and first.
    trend = window[-1] - window[0]

    # Base from average net relative to absolute magnitude.
    magnitude = max(abs(x) for x in window) or 1.0
    normalized = max(-1.0, min(1.0, avg_net / magnitude))
    score = (normalized * 50.0) + 50.0  # map [-1,1] -> [0,100]

    # Adjust by trend: improving trend adds up to +10, worsening up to -10.
    trend_norm = max(-1.0, min(1.0, trend / magnitude))
    score += trend_norm * 10.0

    score = max(0.0, min(100.0, score))

    return FactorScore(
        name="cashflow_health",
        score=score,
        details={
            "months": len(window),
            "avg_net": avg_net,
            "trend": trend,
        },
    )

