"""Integration hooks for triggering alerts from other systems."""
from typing import Optional

from src.alerts.engine import evaluate_and_trigger


def check_risk_score_alert(business_id: str, risk_score: float) -> Optional[str]:
    """Check and trigger high risk score alert if threshold exceeded."""
    alert = evaluate_and_trigger(
        "high_risk_score",
        {"risk_score": risk_score, "business_id": business_id},
        business_id=business_id,
    )
    return alert.id if alert else None


def check_payment_default_alert(business_id: str, days_overdue: int, invoice_id: Optional[str] = None) -> Optional[str]:
    """Check and trigger payment default alert if overdue threshold exceeded."""
    alert = evaluate_and_trigger(
        "payment_default",
        {"days_overdue": days_overdue, "business_id": business_id, "invoice_id": invoice_id},
        business_id=business_id,
        entity_type="invoice" if invoice_id else None,
        entity_id=invoice_id,
    )
    return alert.id if alert else None


def check_fraud_pattern_alert(business_id: str, fraud_score: float, pattern_type: str) -> Optional[str]:
    """Check and trigger fraud pattern alert."""
    alert = evaluate_and_trigger(
        "fraud_pattern",
        {"fraud_score": fraud_score, "pattern_type": pattern_type, "business_id": business_id},
        business_id=business_id,
    )
    return alert.id if alert else None


def check_negative_cashflow_alert(business_id: str, consecutive_negative_months: int) -> Optional[str]:
    """Check and trigger negative cashflow alert."""
    alert = evaluate_and_trigger(
        "negative_cashflow",
        {"consecutive_negative_months": consecutive_negative_months, "business_id": business_id},
        business_id=business_id,
    )
    return alert.id if alert else None


def check_supplier_concentration_alert(business_id: str, top_supplier_share: float) -> Optional[str]:
    """Check and trigger supplier concentration alert."""
    alert = evaluate_and_trigger(
        "supplier_concentration",
        {"top_supplier_share": top_supplier_share, "business_id": business_id},
        business_id=business_id,
    )
    return alert.id if alert else None
