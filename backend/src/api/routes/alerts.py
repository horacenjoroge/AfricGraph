"""Alert system API endpoints."""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.alerts.engine import evaluate_and_trigger, get_rule, initialize_rules, list_rules
from src.alerts.models import AlertSeverity, AlertStatus, AlertType
from src.alerts.persistence import (
    acknowledge_alert,
    ensure_alerts_table,
    get_alert,
    get_alert_metrics,
    list_alerts,
    resolve_alert,
)

router = APIRouter(prefix="/alerts", tags=["alerts"])


class TriggerAlertRequest(BaseModel):
    rule_id: str
    data: dict
    business_id: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None


@router.post("/trigger")
def trigger_alert(body: TriggerAlertRequest) -> dict:
    """Manually trigger an alert evaluation."""
    alert = evaluate_and_trigger(
        body.rule_id,
        body.data,
        business_id=body.business_id,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
    )
    if not alert:
        return {"triggered": False, "reason": "condition not met or suppressed"}
    return {"triggered": True, "alert_id": alert.id}


@router.get("/rules")
def get_rules() -> dict:
    """List all alert rules."""
    return {"rules": [r.model_dump() for r in list_rules()]}


@router.get("/rules/{rule_id}")
def get_rule_endpoint(rule_id: str) -> dict:
    """Get alert rule by ID."""
    rule = get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="rule not found")
    return rule.model_dump()


@router.get("")
def get_alerts(
    business_id: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    alert_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """List alerts with optional filters."""
    status_enum = AlertStatus(status) if status else None
    severity_enum = AlertSeverity(severity) if severity else None
    type_enum = AlertType(alert_type) if alert_type else None

    alerts = list_alerts(
        business_id=business_id,
        status=status_enum,
        severity=severity_enum,
        alert_type=type_enum,
        limit=limit,
        offset=offset,
    )
    return {"alerts": [a.model_dump(mode="json") for a in alerts]}


@router.get("/{alert_id}")
def get_alert_endpoint(alert_id: str) -> dict:
    """Get alert by ID."""
    alert = get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="alert not found")
    return alert.model_dump(mode="json")


@router.post("/{alert_id}/acknowledge")
def acknowledge_alert_endpoint(alert_id: str, user_id: str) -> dict:
    """Acknowledge an alert."""
    alert = acknowledge_alert(alert_id, user_id)
    if not alert:
        raise HTTPException(status_code=404, detail="alert not found")
    return alert.model_dump(mode="json")


@router.post("/{alert_id}/resolve")
def resolve_alert_endpoint(alert_id: str, user_id: str) -> dict:
    """Resolve an alert."""
    alert = resolve_alert(alert_id, user_id)
    if not alert:
        raise HTTPException(status_code=404, detail="alert not found")
    return alert.model_dump(mode="json")


@router.get("/metrics/summary")
def get_metrics(business_id: Optional[str] = None) -> dict:
    """Get alert statistics."""
    metrics = get_alert_metrics(business_id=business_id)
    return metrics.model_dump(mode="json")
