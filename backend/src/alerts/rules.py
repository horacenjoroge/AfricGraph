"""Alert rule definitions and condition evaluation."""
from typing import Any, Dict, List

from src.alerts.models import AlertRule, AlertSeverity, AlertType


def get_default_rules() -> List[AlertRule]:
    """Return predefined alert rules."""
    return [
        AlertRule(
            id="high_risk_score",
            name="High Risk Score",
            alert_type=AlertType.HIGH_RISK_SCORE,
            condition={"field": "risk_score", "operator": ">", "value": 80},
            severity=AlertSeverity.HIGH,
            cooldown_minutes=1440,  # 24 hours
        ),
        AlertRule(
            id="payment_default",
            name="Payment Default",
            alert_type=AlertType.PAYMENT_DEFAULT,
            condition={"field": "days_overdue", "operator": ">=", "value": 60},
            severity=AlertSeverity.CRITICAL,
            cooldown_minutes=1440,
        ),
        AlertRule(
            id="fraud_pattern",
            name="Fraud Pattern Detected",
            alert_type=AlertType.FRAUD_PATTERN,
            condition={"field": "fraud_score", "operator": ">", "value": 50},
            severity=AlertSeverity.CRITICAL,
            cooldown_minutes=60,
        ),
        AlertRule(
            id="negative_cashflow",
            name="Negative Cash Flow",
            alert_type=AlertType.NEGATIVE_CASHFLOW,
            condition={"field": "consecutive_negative_months", "operator": ">=", "value": 3},
            severity=AlertSeverity.HIGH,
            cooldown_minutes=1440,
        ),
        AlertRule(
            id="supplier_concentration",
            name="Supplier Concentration Risk",
            alert_type=AlertType.SUPPLIER_CONCENTRATION,
            condition={"field": "top_supplier_share", "operator": ">", "value": 0.5},
            severity=AlertSeverity.MEDIUM,
            cooldown_minutes=1440,
        ),
    ]


def evaluate_condition(condition: Dict[str, Any], data: Dict[str, Any]) -> bool:
    """
    Evaluate alert condition against data.

    condition: {"field": "risk_score", "operator": ">", "value": 80}
    data: {"risk_score": 85, "business_id": "b123"}
    """
    field = condition.get("field")
    operator = condition.get("operator")
    threshold = condition.get("value")

    if field not in data:
        return False

    value = data[field]

    if operator == ">":
        return float(value) > float(threshold)
    elif operator == ">=":
        return float(value) >= float(threshold)
    elif operator == "<":
        return float(value) < float(threshold)
    elif operator == "<=":
        return float(value) <= float(threshold)
    elif operator == "==":
        return value == threshold
    elif operator == "!=":
        return value != threshold
    elif operator == "in":
        return value in threshold
    elif operator == "contains":
        return threshold in str(value)
    else:
        return False
