"""Supplier concentration and single-point-of-failure analysis."""
from __future__ import annotations

from typing import Dict, List, TypedDict

from src.infrastructure.database.neo4j_client import neo4j_client


class SupplierShare(TypedDict):
    supplier_id: str
    supplier_name: str | None
    volume: float
    share: float


class SupplierConcentrationResult(TypedDict):
    hhi: float
    supplier_count: int
    top_share: float
    suppliers: List[SupplierShare]
    is_single_point_of_failure: bool


def compute_supplier_concentration(business_id: str) -> SupplierConcentrationResult:
    """
    Compute supplier concentration metrics for a business.

    Uses transaction volume per supplier as weights and returns:
      - HHI index
      - top supplier share
      - SPOF flag (very high top share or only one supplier)
    """
    query = """
    MATCH (b:Business {id: $business_id})-[:BUYS_FROM]->(s:Supplier)
    OPTIONAL MATCH (b)-[:BUYS_FROM]->(s)-[:INVOLVES|SUPPLIES*0..1]->(t:Transaction)
    WITH s, coalesce(sum(t.amount), 1.0) AS volume
    RETURN s.id AS supplier_id, s.name AS supplier_name, volume
    ORDER BY volume DESC
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    suppliers: List[SupplierShare] = []
    total = 0.0
    for r in rows:
        vol = float(r.get("volume") or 0.0)
        total += vol
        suppliers.append(
            SupplierShare(
                supplier_id=str(r.get("supplier_id")),
                supplier_name=r.get("supplier_name"),
                volume=vol,
                share=0.0,  # filled below
            )
        )

    if not suppliers or total <= 0:
        return SupplierConcentrationResult(
            hhi=0.0,
            supplier_count=len(suppliers),
            top_share=0.0,
            suppliers=[],
            is_single_point_of_failure=False,
        )

    # Compute shares and HHI.
    hhi = 0.0
    for s in suppliers:
        share = s["volume"] / total
        s["share"] = share
        hhi += share * share

    top_share = suppliers[0]["share"]
    supplier_count = len(suppliers)
    spof = supplier_count == 1 or top_share >= 0.6

    return SupplierConcentrationResult(
        hhi=hhi,
        supplier_count=supplier_count,
        top_share=top_share,
        suppliers=suppliers,
        is_single_point_of_failure=spof,
    )

