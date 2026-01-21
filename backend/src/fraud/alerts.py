"""PostgreSQL-backed fraud alerts and manual review queue."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.logging import get_logger

from .models import AlertSeverity, FraudAlert, FraudPatternHit

logger = get_logger(__name__)

TABLE = "fraud_alerts"


def ensure_alerts_table() -> None:
    """Create fraud_alerts table if it does not exist."""
    sql = f"""
    CREATE TABLE IF NOT EXISTS {TABLE} (
        id BIGSERIAL PRIMARY KEY,
        business_id VARCHAR(255) NOT NULL,
        pattern VARCHAR(100) NOT NULL,
        severity VARCHAR(20) NOT NULL,
        score NUMERIC(5,2) NOT NULL,
        description TEXT,
        metadata JSONB,
        is_false_positive BOOLEAN NOT NULL DEFAULT false,
        status VARCHAR(20) NOT NULL DEFAULT 'open',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_fraud_alerts_business ON {TABLE}(business_id, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_fraud_alerts_status ON {TABLE}(status);
    """
    with postgres_client.get_session() as s:
        for stmt in (x.strip() for x in sql.split(";") if x.strip()):
            s.execute(text(stmt))


def _classify_severity(total_score: float) -> AlertSeverity:
    if total_score >= 80:
        return AlertSeverity.CRITICAL
    if total_score >= 60:
        return AlertSeverity.HIGH
    if total_score >= 40:
        return AlertSeverity.MEDIUM
    return AlertSeverity.LOW


def create_alert_from_hits(business_id: str, hits: List[FraudPatternHit]) -> Optional[FraudAlert]:
    """Create a single aggregated alert for a business from pattern hits."""
    if not hits:
        return None
    ensure_alerts_table()
    total_score = sum(h.score_contribution for h in hits)
    severity = _classify_severity(total_score)
    description = "; ".join({h.description for h in hits})
    metadata: Dict[str, Any] = {
        "patterns": [
            {
                "pattern": h.pattern,
                "score": h.score_contribution,
                "context": h.context,
            }
            for h in hits
        ]
    }
    now = datetime.utcnow()
    with postgres_client.get_session() as s:
        r = s.execute(
            text(
                f"""
                INSERT INTO {TABLE}
                  (business_id, pattern, severity, score, description, metadata, created_at, updated_at)
                VALUES
                  (:business_id, :pattern, :severity, :score, :description, CAST(:metadata AS jsonb), :created_at, :updated_at)
                RETURNING id
                """
            ),
            {
                "business_id": business_id,
                "pattern": "combined",
                "severity": severity.value,
                "score": float(total_score),
                "description": description,
                "metadata": __import__("json").dumps(metadata),
                "created_at": now,
                "updated_at": now,
            },
        )
        (alert_id,) = r.fetchone()
    return FraudAlert(
        id=alert_id,
        business_id=business_id,
        pattern="combined",
        severity=severity,
        score=float(total_score),
        description=description,
        created_at=now,
        metadata=metadata,
    )


def list_alerts(
    business_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """List alerts, optionally filtered by business and status."""
    ensure_alerts_table()
    conditions = ["1=1"]
    params: Dict[str, Any] = {"limit": limit, "offset": offset}
    if business_id:
        conditions.append("business_id = :business_id")
        params["business_id"] = business_id
    if status:
        conditions.append("status = :status")
        params["status"] = status
    with postgres_client.get_session() as s:
        r = s.execute(
            text(
                f"""
                SELECT id, business_id, pattern, severity, score, description,
                       metadata, is_false_positive, status, created_at, updated_at
                FROM {TABLE}
                WHERE {" AND ".join(conditions)}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            params,
        )
        rows = r.fetchall()
    keys = [
        "id",
        "business_id",
        "pattern",
        "severity",
        "score",
        "description",
        "metadata",
        "is_false_positive",
        "status",
        "created_at",
        "updated_at",
    ]
    return [dict(zip(keys, row)) for row in rows]


def mark_false_positive(alert_id: int, *, note: Optional[str] = None) -> None:
    """Mark an alert as false positive and close it."""
    ensure_alerts_table()
    with postgres_client.get_session() as s:
        s.execute(
            text(
                f"""
                UPDATE {TABLE}
                SET is_false_positive = true,
                    status = 'closed',
                    updated_at = now(),
                    metadata = jsonb_set(
                        coalesce(metadata, '{{}}'::jsonb),
                        '{{false_positive_note}}',
                        to_jsonb(:note)
                    )
                WHERE id = :id
                """
            ),
            {"id": alert_id, "note": note or ""},
        )

