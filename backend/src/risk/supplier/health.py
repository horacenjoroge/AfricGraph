"""Supplier financial health heuristics and alternative suggestions."""
from __future__ import annotations

from typing import List, TypedDict

from src.infrastructure.database.neo4j_client import neo4j_client

from .late_payments import SupplierLatePaymentStats


class SupplierHealth(TypedDict):
    supplier_id: str
    supplier_name: str | None
    late_ratio: float
    health_label: str


class AlternativeSupplier(TypedDict):
    supplier_id: str
    supplier_name: str | None
    reason: str


def classify_supplier_health(late_stats: List[SupplierLatePaymentStats]) -> List[SupplierHealth]:
    """Classify suppliers as good/ok/poor based on late payment ratios."""
    health: List[SupplierHealth] = []
    for s in late_stats:
        ratio = s["late_ratio"]
        if ratio <= 0.05:
            label = "good"
        elif ratio <= 0.20:
            label = "ok"
        else:
            label = "poor"
        health.append(
            SupplierHealth(
                supplier_id=s["supplier_id"],
                supplier_name=s["supplier_name"],
                late_ratio=ratio,
                health_label=label,
            )
        )
    return health


def suggest_alternative_suppliers(business_id: str) -> List[AlternativeSupplier]:
    """
    Suggest alternative suppliers based on other businesses' supplier choices.

    Simple heuristic:
      - Find suppliers used by peer businesses in the same sector.
    """
    query = """
    MATCH (b:Business {id: $business_id})
    OPTIONAL MATCH (b)-[:BUYS_FROM]->(current:Supplier)
    OPTIONAL MATCH (b)-[:BUYS_FROM]->(:Supplier)<-[:BUYS_FROM]-(peer:Business)
    OPTIONAL MATCH (peer)-[:BUYS_FROM]->(alt:Supplier)
    WHERE NOT (b)-[:BUYS_FROM]->(alt)
    RETURN DISTINCT alt.id AS supplier_id, alt.name AS supplier_name
    LIMIT 20
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    alts: List[AlternativeSupplier] = []
    for r in rows:
        if not r.get("supplier_id"):
            continue
        alts.append(
            AlternativeSupplier(
                supplier_id=str(r.get("supplier_id")),
                supplier_name=r.get("supplier_name"),
                reason="Used by peer businesses but not currently a supplier.",
            )
        )
    return alts

