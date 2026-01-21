"""Detect shell company patterns."""
from __future__ import annotations

from typing import List

from src.infrastructure.database.neo4j_client import neo4j_client

from ..models import FraudPatternHit


def detect_shell_company_signals(business_id: str) -> List[FraudPatternHit]:
    """
    Heuristic shell company detection:
      - Few or no employees
      - Shared directors with many other entities
      - High transaction volume relative to age/size
    """
    query = """
    MATCH (b:Business {id: $business_id})
    OPTIONAL MATCH (b)<-[:EMPLOYED_BY]-(:Person) AS emp
    WITH b, count(emp) AS employees
    OPTIONAL MATCH (d:Person)-[:DIRECTOR_OF]->(b)
    WITH b, employees, collect(DISTINCT d) AS directors
    WITH b, employees, directors, size(directors) AS director_count
    OPTIONAL MATCH (b)-[:INVOLVES]-(t:Transaction)
    WITH b, employees, director_count, directors,
         count(t) AS tx_count,
         sum(coalesce(t.amount, 0)) AS volume
    RETURN employees, director_count, tx_count, volume
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    if not rows:
        return []
    row = rows[0]
    employees = row.get("employees") or 0
    director_count = row.get("director_count") or 0
    tx_count = row.get("tx_count") or 0
    volume = float(row.get("volume") or 0.0)

    hits: List[FraudPatternHit] = []
    if employees == 0 and tx_count > 0:
        hits.append(
            FraudPatternHit(
                pattern="shell_company",
                description="No employees but active transaction volume.",
                business_id=business_id,
                score_contribution=15.0,
                context={
                    "employees": employees,
                    "tx_count": tx_count,
                    "volume": volume,
                    "director_count": director_count,
                },
            )
        )
    if director_count >= 3 and tx_count > 50:
        hits.append(
            FraudPatternHit(
                pattern="shell_company",
                description="Many directors and high transaction count.",
                business_id=business_id,
                score_contribution=10.0,
                context={
                    "employees": employees,
                    "tx_count": tx_count,
                    "volume": volume,
                    "director_count": director_count,
                },
            )
        )
    return hits

