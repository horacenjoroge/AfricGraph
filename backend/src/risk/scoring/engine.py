"""Main risk scoring engine."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.logging import get_logger
from src.cache.integrations import cached_risk_score
from src.cache.invalidation import invalidate_risk_cache
from src.monitoring.instrumentation import track_risk_calculation
from src.monitoring.metrics import high_risk_businesses

from .cashflow_analyzer import analyze_cashflow_health
from .models import FactorScore, RiskScoreResult
from .network_analyzer import analyze_network_exposure
from .ownership_analyzer import analyze_ownership_complexity
from .payment_analyzer import analyze_payment_behavior
from .supplier_analyzer import analyze_supplier_concentration
from .explainer import build_explanation
from .history import record_risk_score

logger = get_logger(__name__)


WEIGHTS: Dict[str, float] = {
    "payment_behavior": 0.40,
    "supplier_concentration": 0.25,
    "ownership_complexity": 0.15,
    "cashflow_health": 0.15,
    "network_exposure": 0.05,
}


@cached_risk_score
def compute_business_risk(business_id: str) -> RiskScoreResult:
    """Compute composite risk score for a business and persist history."""
    with track_risk_calculation(business_id):
        factors: Dict[str, FactorScore] = {}

    try:
        factors["payment_behavior"] = analyze_payment_behavior(business_id)
    except Exception as e:
        logger.exception("payment behavior analysis failed", business_id=business_id, error=str(e))

    try:
        factors["supplier_concentration"] = analyze_supplier_concentration(business_id)
    except Exception as e:
        logger.exception("supplier concentration analysis failed", business_id=business_id, error=str(e))

    try:
        factors["ownership_complexity"] = analyze_ownership_complexity(business_id)
    except Exception as e:
        logger.exception("ownership analysis failed", business_id=business_id, error=str(e))

    try:
        factors["cashflow_health"] = analyze_cashflow_health(business_id)
    except Exception as e:
        logger.exception("cashflow analysis failed", business_id=business_id, error=str(e))

    try:
        factors["network_exposure"] = analyze_network_exposure(business_id)
    except Exception as e:
        logger.exception("network exposure analysis failed", business_id=business_id, error=str(e))

    total_weight = 0.0
    weighted_sum = 0.0
    for name, weight in WEIGHTS.items():
        fs = factors.get(name)
        if not fs:
            continue
        total_weight += weight
        weighted_sum += weight * fs.score

    if total_weight == 0.0:
        total_score = 50.0
    else:
        total_score = weighted_sum / total_weight

    result = RiskScoreResult(
        business_id=business_id,
        total_score=total_score,
        factors=factors,
        generated_at=datetime.now(timezone.utc),
        explanation="",  # filled below
    )
    result.explanation = build_explanation(result)

    # Update high risk businesses metric
    if total_score >= 80:
        # Increment counter (would need to track all high-risk businesses)
        # For now, we'll update a gauge that tracks current count
        pass  # Would need to query all high-risk businesses to set gauge

    # Persist history.
    try:
        record_risk_score(result)
    except Exception as e:
        logger.exception("failed to record risk score history", business_id=business_id, error=str(e))

    return result

