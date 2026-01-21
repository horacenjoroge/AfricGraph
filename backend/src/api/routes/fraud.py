"""Fraud detection API endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException

from src.fraud.alerts import list_alerts, mark_false_positive
from src.fraud.detector import run_fraud_checks_for_business

router = APIRouter(prefix="/fraud", tags=["fraud"])


@router.post("/business/{business_id}/scan")
def scan_business_for_fraud(business_id: str) -> dict:
    """Run fraud checks for a business and create an alert if needed."""
    result = run_fraud_checks_for_business(business_id)
    return result


@router.get("/alerts")
def get_alerts(
    business_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """List fraud alerts (manual review queue)."""
    items = list_alerts(business_id=business_id, status=status, limit=limit, offset=offset)
    return {"items": items, "limit": limit, "offset": offset}


@router.post("/alerts/{alert_id}/false-positive")
def mark_alert_false_positive(alert_id: int, note: Optional[str] = None) -> dict:
    """Mark an alert as a false positive and close it (feedback loop)."""
    mark_false_positive(alert_id, note=note)
    return {"id": alert_id, "status": "closed", "false_positive": True}

