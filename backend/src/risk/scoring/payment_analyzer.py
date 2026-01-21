"""Payment behavior analyzer: late payments, defaults."""
from __future__ import annotations

from datetime import date
from typing import Dict, List

from src.infrastructure.database.neo4j_client import neo4j_client

from .models import FactorScore


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def analyze_payment_behavior(business_id: str) -> FactorScore:
    """
    Compute payment behavior score (0-100).

    Heuristic:
      - On-time/early share improves score.
      - Late days and defaulted invoices reduce score.
    """
    # This Cypher assumes relationships:
    # (b:Business {id: $business_id})-[:ISSUED]->(inv:Invoice)
    # and (p:Payment)-[:SETTLES]->(inv)
    query = """
    MATCH (b:Business {id: $business_id})-[:ISSUED]->(inv:Invoice)
    OPTIONAL MATCH (p:Payment)-[:SETTLES]->(inv)
    RETURN
      count(inv) AS total_invoices,
      sum(CASE
            WHEN inv.due_date IS NOT NULL AND p.date IS NOT NULL AND p.date > inv.due_date
            THEN duration.between(inv.due_date, p.date).days
            ELSE 0
          END) AS total_late_days,
      sum(CASE
            WHEN inv.due_date IS NOT NULL AND p.date IS NOT NULL AND p.date <= inv.due_date
            THEN 1
            ELSE 0
          END) AS on_time_count,
      sum(CASE
            WHEN inv.due_date IS NOT NULL AND p IS NULL AND inv.due_date < date()
            THEN 1
            ELSE 0
          END) AS defaults
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    if not rows:
        return FactorScore(
            name="payment_behavior",
            score=50.0,
            details={"reason": "no_invoices"},
        )
    row = rows[0]
    total_invoices = row.get("total_invoices") or 0
    total_late_days = row.get("total_late_days") or 0
    on_time_count = row.get("on_time_count") or 0
    defaults = row.get("defaults") or 0

    if total_invoices == 0:
        return FactorScore(
            name="payment_behavior",
            score=50.0,
            details={"reason": "no_invoices"},
        )

    on_time_ratio = _safe_div(on_time_count, total_invoices)
    avg_late_days = _safe_div(total_late_days, max(total_invoices - on_time_count, 1))

    # Base from on-time ratio (0-100).
    score = on_time_ratio * 100.0
    # Penalty for late days (capped).
    score -= min(avg_late_days * 2.0, 30.0)
    # Penalty per default (capped).
    score -= min(defaults * 10.0, 40.0)
    score = max(0.0, min(100.0, score))

    return FactorScore(
        name="payment_behavior",
        score=score,
        details={
            "total_invoices": total_invoices,
            "on_time_count": on_time_count,
            "defaults": defaults,
            "total_late_days": total_late_days,
            "avg_late_days": avg_late_days,
        },
    )

