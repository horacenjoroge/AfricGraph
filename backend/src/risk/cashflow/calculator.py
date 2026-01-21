"""Cash flow aggregation and health score calculation."""
from __future__ import annotations

from typing import List

from src.infrastructure.database.neo4j_client import neo4j_client

from .models import CashHealthSummary, MonthlyCashflow
from .trend_analyzer import detect_negative_trend


def _fetch_monthly_cashflows(business_id: str) -> List[MonthlyCashflow]:
    """Aggregate inflow/outflow/net by month from transactions involving the business."""
    query = """
    MATCH (b:Business {id: $business_id})-[:INVOLVES]-(t:Transaction)
    WITH date.truncate('month', t.date) AS m,
         sum(CASE WHEN t.type = 'inflow' THEN t.amount ELSE 0 END) AS inflow,
         sum(CASE WHEN t.type = 'outflow' THEN t.amount ELSE 0 END) AS outflow
    RETURN m AS month, inflow, outflow, inflow - outflow AS net
    ORDER BY month ASC
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    series: List[MonthlyCashflow] = []
    for r in rows:
        m = r.get("month")
        inflow = float(r.get("inflow") or 0.0)
        outflow = float(r.get("outflow") or 0.0)
        net = float(r.get("net") or inflow - outflow)
        series.append(MonthlyCashflow(month=m, inflow=inflow, outflow=outflow, net=net))
    return series


def compute_cash_health(business_id: str) -> CashHealthSummary:
    """Compute cash flow health score, burn rate, runway, and trend flags."""
    series = _fetch_monthly_cashflows(business_id)
    if not series:
        return CashHealthSummary(
            business_id=business_id,
            health_score=50.0,
            burn_rate=0.0,
            runway_months=0.0,
            has_negative_trend=False,
            series=[],
        )

    nets = [m.net for m in series]
    # Use last 6 months if possible.
    window = nets[-6:]
    avg_net = sum(window) / len(window)

    # Burn rate: if net is negative, use absolute value; else 0.
    burn_rate = -avg_net if avg_net < 0 else 0.0

    # Simple runway estimation: assume current cash is sum of all historical net.
    cumulative_cash = sum(nets)
    runway_months = float("inf")
    if burn_rate > 0:
        runway_months = max(0.0, cumulative_cash / burn_rate)

    # Health score: map avg_net vs turnover and runway.
    magnitude = max(abs(x) for x in window) or 1.0
    normalized = max(-1.0, min(1.0, avg_net / magnitude))
    score = (normalized * 50.0) + 50.0  # [-1,1] -> [0,100]

    # Adjust by runway: very short runway pulls score down.
    if runway_months != float("inf"):
        if runway_months < 3:
            score -= 20.0
        elif runway_months < 6:
            score -= 10.0

    has_negative_trend = detect_negative_trend(series)

    if has_negative_trend:
        score -= 10.0

    score = max(0.0, min(100.0, score))

    return CashHealthSummary(
        business_id=business_id,
        health_score=score,
        burn_rate=burn_rate,
        runway_months=runway_months if runway_months != float("inf") else 9999.0,
        has_negative_trend=has_negative_trend,
        series=series,
    )

