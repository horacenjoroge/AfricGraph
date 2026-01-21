"""Cash flow trend analyzer."""
from __future__ import annotations

from src.risk.cashflow.calculator import compute_cash_health

from .models import FactorScore


def analyze_cashflow_health(business_id: str) -> FactorScore:
    """Compute cash flow health score (0-100) using the cashflow calculator."""
    summary = compute_cash_health(business_id)
    return FactorScore(
        name="cashflow_health",
        score=summary.health_score,
        details={
            "burn_rate": summary.burn_rate,
            "runway_months": summary.runway_months,
            "has_negative_trend": summary.has_negative_trend,
        },
    )

