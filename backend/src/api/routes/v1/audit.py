"""Audit log query endpoints."""
from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime

from src.api.schemas.audit import AuditLogQuery, AuditLogResponse
from src.api.schemas.common import PaginatedResponse
from src.api.utils.pagination import paginate
from src.infrastructure.audit import audit_logger

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=PaginatedResponse[AuditLogResponse])
def query_audit_logs(
    event_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    actor_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    from_ts: Optional[datetime] = Query(None),
    to_ts: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[AuditLogResponse]:
    """Query audit logs with filters."""
    events = audit_logger.query(
        event_type=event_type,
        action=action,
        actor_id=actor_id,
        resource_type=resource_type,
        resource_id=resource_id,
        from_ts=from_ts,
        to_ts=to_ts,
        limit=limit,
        offset=offset,
    )

    # Get total count (simplified - would need separate count query for accuracy)
    total = len(events) if len(events) < limit else limit + 1  # Approximation

    items = [
        AuditLogResponse(
            id=e["id"],
            created_at=e["created_at"],
            event_type=e["event_type"],
            action=e["action"],
            actor_id=e.get("actor_id"),
            resource_type=e.get("resource_type"),
            resource_id=e.get("resource_id"),
            outcome=e.get("outcome", ""),
            reason=e.get("reason"),
        )
        for e in events
    ]

    return paginate(items, total, limit, offset)
