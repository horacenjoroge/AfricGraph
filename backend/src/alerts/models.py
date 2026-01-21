"""Alert system models."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status."""

    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class AlertType(str, Enum):
    """Predefined alert types."""

    HIGH_RISK_SCORE = "high_risk_score"
    PAYMENT_DEFAULT = "payment_default"
    FRAUD_PATTERN = "fraud_pattern"
    NEGATIVE_CASHFLOW = "negative_cashflow"
    SUPPLIER_CONCENTRATION = "supplier_concentration"


class AlertRule(BaseModel):
    """Alert rule definition."""

    id: str
    name: str
    alert_type: AlertType
    condition: Dict[str, Any]  # e.g. {"field": "risk_score", "operator": ">", "value": 80}
    severity: AlertSeverity
    enabled: bool = True
    cooldown_minutes: int = 60  # Minimum minutes between same alert
    routing: Dict[str, Any] = Field(default_factory=dict)  # email, slack, webhook configs


class Alert(BaseModel):
    """Alert instance."""

    id: str
    rule_id: str
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.PENDING
    business_id: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None


class AlertMetrics(BaseModel):
    """Alert statistics."""

    total_alerts: int
    by_severity: Dict[str, int]
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    unacknowledged_count: int
    recent_alerts: List[Alert]
