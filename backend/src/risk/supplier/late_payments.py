"""Late payment patterns per supplier."""
from __future__ import annotations

from typing import List, TypedDict

from src.infrastructure.database.neo4j_client import neo4j_client


class SupplierLatePaymentStats(TypedDict):
    supplier_id: str
    supplier_name: str | None
    total_invoices: int
    late_invoices: int
    late_ratio: float


def compute_late_payment_stats(business_id: str) -> List[SupplierLatePaymentStats]:
    """
    Compute late payment ratios per supplier for the given business.

    Assumes:
      (b:Business)-[:BUYS_FROM]->(s:Supplier)
      (s)-[:ISSUED]->(inv:Invoice)
      (p:Payment)-[:SETTLES]->(inv)
    """
    query = """
    MATCH (b:Business {id: $business_id})-[:BUYS_FROM]->(s:Supplier)
    MATCH (s)-[:ISSUED]->(inv:Invoice)
    OPTIONAL MATCH (p:Payment)-[:SETTLES]->(inv)
    WITH s, inv, p
    RETURN
      s.id AS supplier_id,
      s.name AS supplier_name,
      count(inv) AS total_invoices,
      sum(
        CASE
          WHEN inv.due_date IS NOT NULL
               AND p.date IS NOT NULL
               AND p.date > inv.due_date
          THEN 1 ELSE 0
        END
      ) AS late_invoices
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    stats: List[SupplierLatePaymentStats] = []
    for r in rows:
        total = int(r.get("total_invoices") or 0)
        late = int(r.get("late_invoices") or 0)
        ratio = (late / total) if total else 0.0
        stats.append(
            SupplierLatePaymentStats(
                supplier_id=str(r.get("supplier_id")),
                supplier_name=r.get("supplier_name"),
                total_invoices=total,
                late_invoices=late,
                late_ratio=ratio,
            )
        )
    return stats

