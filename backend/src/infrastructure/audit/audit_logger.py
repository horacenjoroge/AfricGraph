"""PostgreSQL-backed append-only audit logger."""
import json
import hashlib
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import text

from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.logging import get_logger

from .models import AuditEvent, AuditEventType, AuditAction

logger = get_logger(__name__)

AUDIT_TABLE = "audit_events"


def _serialize_jsonb(v: Any) -> Optional[str]:
    if v is None:
        return None
    return json.dumps(v, default=str, sort_keys=True)


def _event_hash(row: dict) -> str:
    """Hash of canonical event for tamper detection. Excludes id and event_hash."""
    parts = [
        str(row.get("created_at") or ""),
        str(row.get("event_type") or ""),
        str(row.get("action") or ""),
        str(row.get("actor_id") or ""),
        str(row.get("resource_type") or ""),
        str(row.get("resource_id") or ""),
        str(row.get("outcome") or ""),
        str(row.get("reason") or ""),
        _serialize_jsonb(row.get("before_snapshot")) or "",
        _serialize_jsonb(row.get("after_snapshot")) or "",
        _serialize_jsonb(row.get("extra")) or "",
    ]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


class AuditLogger:
    """Append-only audit logger. All writes are INSERT; no UPDATE or DELETE."""

    def __init__(self, pg=postgres_client):
        self._pg = pg

    def ensure_audit_table(self) -> None:
        """Create audit_events table if it does not exist."""
        sql = f"""
        CREATE TABLE IF NOT EXISTS {AUDIT_TABLE} (
            id BIGSERIAL PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            event_type VARCHAR(50) NOT NULL,
            action VARCHAR(100) NOT NULL,
            actor_id VARCHAR(255),
            actor_type VARCHAR(50),
            resource_type VARCHAR(100),
            resource_id VARCHAR(255),
            outcome VARCHAR(50),
            reason TEXT,
            before_snapshot JSONB,
            after_snapshot JSONB,
            extra JSONB,
            ip_address VARCHAR(45),
            user_agent VARCHAR(500),
            event_hash VARCHAR(64)
        );
        CREATE INDEX IF NOT EXISTS idx_audit_events_created_at ON {AUDIT_TABLE}(created_at);
        CREATE INDEX IF NOT EXISTS idx_audit_events_event_type ON {AUDIT_TABLE}(event_type);
        CREATE INDEX IF NOT EXISTS idx_audit_events_actor_id ON {AUDIT_TABLE}(actor_id);
        CREATE INDEX IF NOT EXISTS idx_audit_events_resource ON {AUDIT_TABLE}(resource_type, resource_id);
        """
        with self._pg.get_session() as s:
            for stmt in (x.strip() for x in sql.split(";") if x.strip()):
                s.execute(text(stmt))

    def _insert(self, ev: AuditEvent) -> int:
        """Append one event. Returns inserted id. Raises if postgres not ready."""
        created = ev.created_at or datetime.utcnow()
        row = {
            "created_at": created,
            "event_type": ev.event_type.value,
            "action": ev.action,
            "actor_id": ev.actor_id,
            "actor_type": ev.actor_type,
            "resource_type": ev.resource_type,
            "resource_id": ev.resource_id,
            "outcome": ev.outcome,
            "reason": ev.reason,
            "before_snapshot": ev.before_snapshot,
            "after_snapshot": ev.after_snapshot,
            "extra": ev.extra,
            "ip_address": ev.ip_address,
            "user_agent": ev.user_agent,
        }
        h = _event_hash({**row, "event_type": ev.event_type.value})
        with self._pg.get_session() as s:
            r = s.execute(
                text(f"""
                INSERT INTO {AUDIT_TABLE}
                (created_at, event_type, action, actor_id, actor_type, resource_type, resource_id,
                 outcome, reason, before_snapshot, after_snapshot, extra, ip_address, user_agent, event_hash)
                VALUES
                (:created_at, :event_type, :action, :actor_id, :actor_type, :resource_type, :resource_id,
                 :outcome, :reason, CAST(:before_snapshot AS jsonb), CAST(:after_snapshot AS jsonb), CAST(:extra AS jsonb),
                 :ip_address, :user_agent, :event_hash)
                RETURNING id
                """),
                {
                    **{k: v for k, v in row.items()},
                    "before_snapshot": _serialize_jsonb(ev.before_snapshot),
                    "after_snapshot": _serialize_jsonb(ev.after_snapshot),
                    "extra": _serialize_jsonb(ev.extra),
                    "event_hash": h,
                },
            )
            (id_,) = r.fetchone()
            return id_

    def log_access(
        self,
        action: str,
        actor_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        reason: Optional[str] = None,
        extra: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> int:
        """Log access: view, search, export."""
        ev = AuditEvent(
            event_type=AuditEventType.ACCESS,
            action=action,
            actor_id=actor_id,
            actor_type="user",
            resource_type=resource_type,
            resource_id=resource_id,
            reason=reason,
            extra=extra,
            ip_address=ip_address,
            user_agent=user_agent,
            outcome="success",
        )
        return self._insert(ev)

    def log_modification(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        actor_id: Optional[str] = None,
        before_snapshot: Optional[dict] = None,
        after_snapshot: Optional[dict] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> int:
        """Log create, update, delete with optional before/after."""
        ev = AuditEvent(
            event_type=AuditEventType.MODIFICATION,
            action=action,
            actor_id=actor_id,
            actor_type="user",
            resource_type=resource_type,
            resource_id=resource_id,
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
            outcome="success",
        )
        return self._insert(ev)

    def log_permission(
        self,
        granted: bool,
        actor_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        reason: Optional[str] = None,
        extra: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> int:
        """Log permission granted or denied."""
        ev = AuditEvent(
            event_type=AuditEventType.PERMISSION,
            action=AuditAction.GRANTED.value if granted else AuditAction.DENIED.value,
            actor_id=actor_id,
            actor_type="user",
            resource_type=resource_type,
            resource_id=resource_id,
            outcome="granted" if granted else "denied",
            reason=reason,
            extra=extra,
            ip_address=ip_address,
        )
        return self._insert(ev)

    def log_decision(
        self,
        action: str,
        actor_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        inputs: Optional[dict] = None,
        outputs: Optional[dict] = None,
        reasoning: Optional[str] = None,
        extra: Optional[dict] = None,
    ) -> int:
        """Log risk score, fraud alert, or other decisions. inputs/outputs/reasoning in extra."""
        ex = dict(extra or {})
        if inputs is not None:
            ex["inputs"] = inputs
        if outputs is not None:
            ex["outputs"] = outputs
        if reasoning is not None:
            ex["reasoning"] = reasoning
        ev = AuditEvent(
            event_type=AuditEventType.DECISION,
            action=action,
            actor_id=actor_id,
            actor_type="system",
            resource_type=resource_type,
            resource_id=resource_id,
            reason=reasoning,
            extra=ex or None,
            outcome="success",
        )
        return self._insert(ev)

    def log_system(
        self,
        action: str,
        actor_id: Optional[str] = None,
        reason: Optional[str] = None,
        extra: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> int:
        """Log login, logout, config change."""
        ev = AuditEvent(
            event_type=AuditEventType.SYSTEM,
            action=action,
            actor_id=actor_id,
            actor_type="user",
            reason=reason,
            extra=extra,
            ip_address=ip_address,
            outcome="success",
        )
        return self._insert(ev)


audit_logger = AuditLogger()
