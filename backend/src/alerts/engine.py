"""Alert engine - rule evaluation and alert creation."""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.infrastructure.logging import get_logger

from .cooldown import check_cooldown
from .models import Alert, AlertRule, AlertSeverity, AlertStatus, AlertType
from .persistence import create_alert
from .routing import route_alert
from .rules import evaluate_condition, get_default_rules

logger = get_logger(__name__)

# In-memory rule store (could be moved to DB later)
_rules: Dict[str, AlertRule] = {}


def initialize_rules() -> None:
    """Load default rules into memory."""
    global _rules
    for rule in get_default_rules():
        _rules[rule.id] = rule
    logger.info("Alert rules initialized", count=len(_rules))


def get_rule(rule_id: str) -> Optional[AlertRule]:
    """Get rule by ID."""
    return _rules.get(rule_id)


def list_rules() -> List[AlertRule]:
    """List all rules."""
    return list(_rules.values())


def evaluate_and_trigger(
    rule_id: str,
    data: Dict[str, Any],
    business_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
) -> Optional[Alert]:
    """
    Evaluate rule condition against data and trigger alert if condition is met.

    Returns Alert if triggered, None if condition not met or suppressed.
    """
    rule = get_rule(rule_id)
    if not rule or not rule.enabled:
        return None

    # Evaluate condition
    if not evaluate_condition(rule.condition, data):
        return None

    # Check cooldown
    if check_cooldown(rule_id, business_id, entity_id, rule.cooldown_minutes):
        logger.debug("Alert suppressed by cooldown", rule_id=rule_id, business_id=business_id)
        return None

    # Create alert
    alert_id = str(uuid.uuid4())
    message = _build_message(rule, data)

    alert = Alert(
        id=alert_id,
        rule_id=rule_id,
        alert_type=rule.alert_type,
        severity=rule.severity,
        status=AlertStatus.PENDING,
        business_id=business_id,
        entity_type=entity_type,
        entity_id=entity_id,
        message=message,
        details=data,
        created_at=datetime.now(timezone.utc),
    )

    # Persist
    try:
        create_alert(alert)
    except Exception as e:
        logger.exception("Failed to create alert", alert_id=alert_id, error=str(e))
        return None

    # Route
    try:
        route_alert(alert.model_dump(mode="json"), rule.routing)
    except Exception as e:
        logger.exception("Failed to route alert", alert_id=alert_id, error=str(e))

    logger.info("Alert triggered", alert_id=alert_id, rule_id=rule_id, severity=rule.severity.value)
    return alert


def _build_message(rule: AlertRule, data: Dict[str, Any]) -> str:
    """Build human-readable alert message."""
    business_id = data.get("business_id", "Unknown")
    if rule.alert_type == AlertType.HIGH_RISK_SCORE:
        score = data.get("risk_score", 0)
        return f"High risk score detected for business {business_id}: {score:.1f}"
    elif rule.alert_type == AlertType.PAYMENT_DEFAULT:
        days = data.get("days_overdue", 0)
        return f"Payment default: {days} days overdue for business {business_id}"
    elif rule.alert_type == AlertType.FRAUD_PATTERN:
        pattern = data.get("pattern_type", "unknown")
        return f"Fraud pattern detected ({pattern}) for business {business_id}"
    elif rule.alert_type == AlertType.NEGATIVE_CASHFLOW:
        months = data.get("consecutive_negative_months", 0)
        return f"Negative cash flow for {months} consecutive months for business {business_id}"
    elif rule.alert_type == AlertType.SUPPLIER_CONCENTRATION:
        share = data.get("top_supplier_share", 0)
        return f"Supplier concentration risk: top supplier represents {share:.1%} for business {business_id}"
    else:
        return f"Alert: {rule.name} for business {business_id}"
