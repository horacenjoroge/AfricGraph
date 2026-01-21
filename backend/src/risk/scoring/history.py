"""Risk score history persistence."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import text

from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.logging import get_logger

from .models import RiskScoreResult

logger = get_logger(__name__)

TABLE = "risk_scores"


def ensure_risk_scores_table() -> None:
    """Create risk_scores table if it does not exist."""
    sql = f"""
    CREATE TABLE IF NOT EXISTS {TABLE} (
        id BIGSERIAL PRIMARY KEY,
        business_id VARCHAR(255) NOT NULL,
        score NUMERIC(5,2) NOT NULL,
        factors JSONB NOT NULL,
        explanation TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_risk_scores_business ON {TABLE}(business_id, created_at DESC);
    """
    with postgres_client.get_session() as s:
        for stmt in (x.strip() for x in sql.split(";") if x.strip()):
            s.execute(text(stmt))


def record_risk_score(result: RiskScoreResult) -> None:
    """Append a risk score record for a business."""
    ensure_risk_scores_table()
    payload: Dict[str, Any] = {
        "business_id": result.business_id,
        "score": float(result.total_score),
        "factors": {
            name: {
                "score": fs.score,
                "details": fs.details,
            }
            for name, fs in result.factors.items()
        },
        "explanation": result.explanation,
        "created_at": result.generated_at,
    }
    with postgres_client.get_session() as s:
        s.execute(
            text(
                f"""
                INSERT INTO {TABLE} (business_id, score, factors, explanation, created_at)
                VALUES (:business_id, :score, CAST(:factors AS jsonb), :explanation, :created_at)
                """
            ),
            {
                "business_id": payload["business_id"],
                "score": payload["score"],
                "factors": __import__("json").dumps(payload["factors"]),
                "explanation": payload["explanation"],
                "created_at": payload["created_at"],
            },
        )


def get_latest_risk_score(business_id: str) -> Dict[str, Any] | None:
    """Fetch the most recent risk score for a business."""
    ensure_risk_scores_table()
    with postgres_client.get_session() as s:
        r = s.execute(
            text(
                f"""
                SELECT business_id, score, factors, explanation, created_at
                FROM {TABLE}
                WHERE business_id = :business_id
                ORDER BY created_at DESC
                LIMIT 1
                """
            ),
            {"business_id": business_id},
        )
        row = r.fetchone()
    if not row:
        return None
    return {
        "business_id": row[0],
        "score": float(row[1]),
        "factors": row[2],
        "explanation": row[3],
        "created_at": row[4],
    }

