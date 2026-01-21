"""Alert persistence and history tracking."""
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import text

from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.logging import get_logger

from .models import Alert, AlertMetrics, AlertSeverity, AlertStatus, AlertType

logger = get_logger(__name__)

ALERTS_TABLE = "alerts"


def ensure_alerts_table() -> None:
    """Create alerts table if it does not exist."""
    sql = f"""
    CREATE TABLE IF NOT EXISTS {ALERTS_TABLE} (
        id VARCHAR(255) PRIMARY KEY,
        rule_id VARCHAR(255) NOT NULL,
        alert_type VARCHAR(50) NOT NULL,
        severity VARCHAR(20) NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        business_id VARCHAR(255),
        entity_type VARCHAR(50),
        entity_id VARCHAR(255),
        message TEXT NOT NULL,
        details JSONB,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        acknowledged_at TIMESTAMPTZ,
        acknowledged_by VARCHAR(255),
        resolved_at TIMESTAMPTZ,
        resolved_by VARCHAR(255)
    );
    CREATE INDEX IF NOT EXISTS idx_alerts_business_id ON {ALERTS_TABLE}(business_id);
    CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON {ALERTS_TABLE}(created_at);
    CREATE INDEX IF NOT EXISTS idx_alerts_status ON {ALERTS_TABLE}(status);
    CREATE INDEX IF NOT EXISTS idx_alerts_rule_id ON {ALERTS_TABLE}(rule_id);
    """
    with postgres_client.get_session() as s:
        for stmt in (x.strip() for x in sql.split(";") if x.strip()):
            s.execute(text(stmt))


def create_alert(alert: Alert) -> None:
    """Create a new alert."""
    with postgres_client.get_session() as s:
        s.execute(
            text(f"""
            INSERT INTO {ALERTS_TABLE}
            (id, rule_id, alert_type, severity, status, business_id, entity_type, entity_id,
             message, details, created_at)
            VALUES
            (:id, :rule_id, :alert_type, :severity, :status, :business_id, :entity_type, :entity_id,
             :message, CAST(:details AS jsonb), :created_at)
            """),
            {
                "id": alert.id,
                "rule_id": alert.rule_id,
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "business_id": alert.business_id,
                "entity_type": alert.entity_type,
                "entity_id": alert.entity_id,
                "message": alert.message,
                "details": json.dumps(alert.details),
                "created_at": alert.created_at,
            },
        )


def acknowledge_alert(alert_id: str, user_id: str) -> Optional[Alert]:
    """Mark alert as acknowledged."""
    with postgres_client.get_session() as s:
        s.execute(
            text(f"""
            UPDATE {ALERTS_TABLE}
            SET status = 'acknowledged', acknowledged_at = :now, acknowledged_by = :user_id
            WHERE id = :alert_id AND status = 'pending'
            """),
            {"alert_id": alert_id, "user_id": user_id, "now": datetime.now(timezone.utc)},
        )
    return get_alert(alert_id)


def resolve_alert(alert_id: str, user_id: str) -> Optional[Alert]:
    """Mark alert as resolved."""
    with postgres_client.get_session() as s:
        s.execute(
            text(f"""
            UPDATE {ALERTS_TABLE}
            SET status = 'resolved', resolved_at = :now, resolved_by = :user_id
            WHERE id = :alert_id
            """),
            {"alert_id": alert_id, "user_id": user_id, "now": datetime.now(timezone.utc)},
        )
    return get_alert(alert_id)


def get_alert(alert_id: str) -> Optional[Alert]:
    """Get alert by ID."""
    with postgres_client.get_session() as s:
        r = s.execute(
            text(f"SELECT * FROM {ALERTS_TABLE} WHERE id = :alert_id"),
            {"alert_id": alert_id},
        )
        row = r.fetchone()
    if not row:
        return None
    return _row_to_alert(dict(row._mapping))


def list_alerts(
    business_id: Optional[str] = None,
    status: Optional[AlertStatus] = None,
    severity: Optional[AlertSeverity] = None,
    alert_type: Optional[AlertType] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Alert]:
    """List alerts with filters."""
    conditions = ["1=1"]
    params = {"limit": limit, "offset": offset}

    if business_id:
        conditions.append("business_id = :business_id")
        params["business_id"] = business_id
    if status:
        conditions.append("status = :status")
        params["status"] = status.value
    if severity:
        conditions.append("severity = :severity")
        params["severity"] = severity.value
    if alert_type:
        conditions.append("alert_type = :alert_type")
        params["alert_type"] = alert_type.value

    with postgres_client.get_session() as s:
        r = s.execute(
            text(f"""
            SELECT * FROM {ALERTS_TABLE}
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
            """),
            params,
        )
        rows = r.fetchall()
    return [_row_to_alert(dict(row._mapping)) for row in rows]


def get_alert_metrics(business_id: Optional[str] = None) -> AlertMetrics:
    """Get alert statistics."""
    conditions = ["1=1"]
    params = {}
    if business_id:
        conditions.append("business_id = :business_id")
        params["business_id"] = business_id

    with postgres_client.get_session() as s:
        # Total count
        r = s.execute(
            text(f"SELECT COUNT(*) FROM {ALERTS_TABLE} WHERE {' AND '.join(conditions)}"),
            params,
        )
        total = r.fetchone()[0]

        # By severity
        r = s.execute(
            text(f"""
            SELECT severity, COUNT(*) as cnt
            FROM {ALERTS_TABLE}
            WHERE {' AND '.join(conditions)}
            GROUP BY severity
            """),
            params,
        )
        by_severity = {row[0]: row[1] for row in r.fetchall()}

        # By type
        r = s.execute(
            text(f"""
            SELECT alert_type, COUNT(*) as cnt
            FROM {ALERTS_TABLE}
            WHERE {' AND '.join(conditions)}
            GROUP BY alert_type
            """),
            params,
        )
        by_type = {row[0]: row[1] for row in r.fetchall()}

        # By status
        r = s.execute(
            text(f"""
            SELECT status, COUNT(*) as cnt
            FROM {ALERTS_TABLE}
            WHERE {' AND '.join(conditions)}
            GROUP BY status
            """),
            params,
        )
        by_status = {row[0]: row[1] for row in r.fetchall()}

        # Unacknowledged
        r = s.execute(
            text(f"""
            SELECT COUNT(*) FROM {ALERTS_TABLE}
            WHERE {' AND '.join(conditions)} AND status = 'pending'
            """),
            params,
        )
        unacknowledged = r.fetchone()[0]

        # Recent alerts
        recent = list_alerts(business_id=business_id, limit=10)

    return AlertMetrics(
        total_alerts=total,
        by_severity=by_severity,
        by_type=by_type,
        by_status=by_status,
        unacknowledged_count=unacknowledged,
        recent_alerts=recent,
    )


def _row_to_alert(row: Dict) -> Alert:
    """Convert database row to Alert model."""
    return Alert(
        id=row["id"],
        rule_id=row["rule_id"],
        alert_type=AlertType(row["alert_type"]),
        severity=AlertSeverity(row["severity"]),
        status=AlertStatus(row["status"]),
        business_id=row.get("business_id"),
        entity_type=row.get("entity_type"),
        entity_id=row.get("entity_id"),
        message=row["message"],
        details=row.get("details") or {},
        created_at=row["created_at"],
        acknowledged_at=row.get("acknowledged_at"),
        acknowledged_by=row.get("acknowledged_by"),
        resolved_at=row.get("resolved_at"),
        resolved_by=row.get("resolved_by"),
    )
