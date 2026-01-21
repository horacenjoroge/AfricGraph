"""Ownership structure complexity analyzer."""
from __future__ import annotations

from typing import Dict

from src.infrastructure.database.neo4j_client import neo4j_client

from .models import FactorScore


def analyze_ownership_complexity(business_id: str) -> FactorScore:
    """
    Compute ownership complexity score (0-100).

    Heuristic based on:
      - Number of direct owners
      - Depth of ownership chain
      - Cross-shareholdings (cycles)
    """
    query = """
    MATCH (b:Business {id: $business_id})
    OPTIONAL MATCH path = (o)-[:OWNS*1..5]->(b)
    WITH b, collect(DISTINCT o) AS owners, collect(path) AS paths
    WITH b,
         owners,
         paths,
         size(owners) AS owner_count,
         reduce(maxDepth = 0, p IN paths | CASE WHEN length(p) > maxDepth THEN length(p) ELSE maxDepth END) AS max_depth
    // Detect cycles involving this business
    OPTIONAL MATCH cyclePath = (b)-[:OWNS*1..5]->(b)
    WITH b, owners, owner_count, max_depth, cyclePath
    RETURN
      owner_count,
      max_depth,
      CASE WHEN cyclePath IS NULL THEN 0 ELSE 1 END AS has_cycle
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    if not rows:
        return FactorScore(
            name="ownership_complexity",
            score=50.0,
            details={"reason": "no_ownership_data"},
        )
    row = rows[0]
    owner_count = row.get("owner_count") or 0
    max_depth = row.get("max_depth") or 0
    has_cycle = bool(row.get("has_cycle") or 0)

    # Start from simple structure (high score) and penalize complexity.
    score = 100.0
    # More than 3 direct owners starts to reduce score.
    if owner_count > 3:
        score -= min((owner_count - 3) * 5.0, 30.0)
    # Deep chains reduce score.
    if max_depth > 2:
        score -= min((max_depth - 2) * 10.0, 30.0)
    # Cycles are highly suspicious.
    if has_cycle:
        score -= 30.0

    score = max(0.0, min(100.0, score))

    return FactorScore(
        name="ownership_complexity",
        score=score,
        details={
            "owner_count": owner_count,
            "max_depth": max_depth,
            "has_cycle": has_cycle,
        },
    )

