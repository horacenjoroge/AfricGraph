"""Audit event models and enums."""
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    ACCESS = "access"
    MODIFICATION = "modification"
    PERMISSION = "permission"
    DECISION = "decision"
    SYSTEM = "system"


class AuditAction(str, Enum):
    # Access
    VIEW = "view"
    SEARCH = "search"
    EXPORT = "export"
    # Modification
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    # Permission
    GRANTED = "granted"
    DENIED = "denied"
    # Decision
    RISK_SCORE = "risk_score"
    FRAUD_ALERT = "fraud_alert"
    # System
    LOGIN = "login"
    LOGOUT = "logout"
    CONFIG_CHANGE = "config_change"


class AuditEvent(BaseModel):
    """In-memory event before persisting. All fields optional except event_type and action."""

    event_type: AuditEventType
    action: str = Field(..., min_length=1, max_length=100)
    actor_id: Optional[str] = Field(None, max_length=255)
    actor_type: Optional[str] = Field(None, max_length=50)
    resource_type: Optional[str] = Field(None, max_length=100)
    resource_id: Optional[str] = Field(None, max_length=255)
    outcome: Optional[str] = Field(None, max_length=50)
    reason: Optional[str] = None
    before_snapshot: Optional[dict[str, Any]] = None
    after_snapshot: Optional[dict[str, Any]] = None
    extra: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=500)
    created_at: Optional[datetime] = None
