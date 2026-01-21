"""Fraud detection orchestrator and scoring."""
from __future__ import annotations

from typing import Dict, List

from src.infrastructure.logging import get_logger

from .alerts import create_alert_from_hits
from .models import FraudPatternHit
from .patterns.circular_payments import detect_circular_payments
from .patterns.shell_companies import detect_shell_company_signals
from .patterns.duplicate_invoices import detect_duplicate_invoices
from .patterns.invoice_fraud import detect_invoice_fraud_signals
from .patterns.structuring import detect_structuring
from .patterns.round_amounts import detect_round_amounts
from .patterns.unusual_patterns import detect_unusual_patterns

logger = get_logger(__name__)


def run_fraud_checks_for_business(business_id: str) -> Dict[str, object]:
    """Run all fraud pattern detectors, create an alert, and return details."""
    all_hits: List[FraudPatternHit] = []

    detectors = [
        detect_circular_payments,
        detect_shell_company_signals,
        detect_duplicate_invoices,
        detect_invoice_fraud_signals,
        detect_structuring,
        detect_round_amounts,
        detect_unusual_patterns,
    ]

    for fn in detectors:
        try:
            hits = fn(business_id)
            all_hits.extend(hits)
        except Exception as e:
            logger.exception("fraud detector failed", pattern_fn=fn.__name__, business_id=business_id, error=str(e))

    alert = create_alert_from_hits(business_id, all_hits)
    return {
        "business_id": business_id,
        "patterns": [
            {
                "pattern": h.pattern,
                "description": h.description,
                "score_contribution": h.score_contribution,
                "context": h.context,
            }
            for h in all_hits
        ],
        "alert": {
            "id": alert.id,
            "severity": alert.severity.value,
            "score": alert.score,
            "description": alert.description,
            "created_at": alert.created_at,
        }
        if alert
        else None,
    }

