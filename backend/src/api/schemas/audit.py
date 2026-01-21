"""Audit log API schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AuditLogQuery(BaseModel):
    """Request schema for querying audit logs."""

    event_type: Optional[str] = None
    action: Optional[str] = None
    actor_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    from_ts: Optional[datetime] = None
    to_ts: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class AuditLogResponse(BaseModel):
    """Response schema for audit log entry."""

    id: int
    created_at: datetime
    event_type: str
    action: str
    actor_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    outcome: str
    reason: Optional[str] = None
