"""Anomaly alert management."""
from typing import List, Optional
from datetime import datetime

from src.infrastructure.database.postgres_client import postgres_client
from src.anomaly.models import AnomalyAlert
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def ensure_alerts_table():
    """Create table for storing anomaly alerts."""
    query = """
    CREATE TABLE IF NOT EXISTS anomaly_alerts (
        id VARCHAR(255) PRIMARY KEY,
        entity_id VARCHAR(255) NOT NULL,
        entity_type VARCHAR(50) NOT NULL,
        anomaly_score FLOAT NOT NULL,
        severity VARCHAR(20) NOT NULL,
        description TEXT NOT NULL,
        detected_at TIMESTAMP NOT NULL,
        acknowledged BOOLEAN DEFAULT FALSE,
        acknowledged_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_anomaly_alerts_entity ON anomaly_alerts(entity_id);
    CREATE INDEX IF NOT EXISTS idx_anomaly_alerts_severity ON anomaly_alerts(severity);
    CREATE INDEX IF NOT EXISTS idx_anomaly_alerts_acknowledged ON anomaly_alerts(acknowledged);
    """
    postgres_client.execute_query(query)


def save_alert(alert: AnomalyAlert) -> str:
    """Save an anomaly alert to database."""
    ensure_alerts_table()

    query = """
    INSERT INTO anomaly_alerts 
    (id, entity_id, entity_type, anomaly_score, severity, description, detected_at, acknowledged)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    ON CONFLICT (id) DO NOTHING
    RETURNING id
    """
    rows = postgres_client.execute_query(
        query,
        (
            alert.id,
            alert.entity_id,
            alert.entity_type,
            alert.anomaly_score,
            alert.severity,
            alert.description,
            alert.detected_at,
            alert.acknowledged,
        ),
    )

    if rows:
        return rows[0]["id"]
    return alert.id


def list_alerts(
    entity_id: Optional[str] = None,
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    limit: int = 100,
) -> List[AnomalyAlert]:
    """List anomaly alerts with filters."""
    ensure_alerts_table()

    conditions = []
    params = []

    if entity_id:
        conditions.append("entity_id = $" + str(len(params) + 1))
        params.append(entity_id)

    if severity:
        conditions.append("severity = $" + str(len(params) + 1))
        params.append(severity)

    if acknowledged is not None:
        conditions.append("acknowledged = $" + str(len(params) + 1))
        params.append(acknowledged)

    where_clause = " AND ".join(conditions) if conditions else "1=1"
    params.append(limit)

    query = f"""
    SELECT * FROM anomaly_alerts
    WHERE {where_clause}
    ORDER BY detected_at DESC
    LIMIT ${len(params)}
    """
    rows = postgres_client.execute_query(query, tuple(params))

    alerts = []
    for row in rows:
        alerts.append(
            AnomalyAlert(
                id=row["id"],
                entity_id=row["entity_id"],
                entity_type=row["entity_type"],
                anomaly_score=float(row["anomaly_score"]),
                severity=row["severity"],
                description=row["description"],
                detected_at=row["detected_at"],
                acknowledged=row.get("acknowledged", False),
            )
        )

    return alerts


def acknowledge_alert(alert_id: str) -> bool:
    """Acknowledge an anomaly alert."""
    ensure_alerts_table()

    query = """
    UPDATE anomaly_alerts
    SET acknowledged = TRUE, acknowledged_at = CURRENT_TIMESTAMP
    WHERE id = $1
    RETURNING id
    """
    rows = postgres_client.execute_query(query, (alert_id,))

    return len(rows) > 0
