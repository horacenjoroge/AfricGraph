"""Risk scoring API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.risk.scoring.engine import compute_business_risk
from src.risk.scoring.history import get_latest_risk_score
from src.risk.cashflow.calculator import compute_cash_health
from src.risk.cashflow.forecaster import forecast_cashflow

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/business/{business_id}")
def get_business_risk(business_id: str) -> dict:
    """Compute and return current risk score for a business."""
    result = compute_business_risk(business_id)
    return {
        "business_id": result.business_id,
        "score": result.total_score,
        "factors": {
            name: {
                "score": fs.score,
                "details": fs.details,
            }
            for name, fs in result.factors.items()
        },
        "generated_at": result.generated_at,
        "explanation": result.explanation,
    }


@router.get("/business/{business_id}/latest")
def get_latest_business_risk(business_id: str) -> dict:
    """Return the most recently stored risk score for a business, if any."""
    row = get_latest_risk_score(business_id)
    if not row:
        raise HTTPException(status_code=404, detail="no risk score found")
    return row


@router.get("/cashflow/{business_id}")
def get_cashflow_health(business_id: str, horizon_months: int = 6) -> dict:
    """
    Return cash flow health summary and forecast for a business.

    Includes:
      - health_score (0-100)
      - burn_rate
      - runway_months
      - has_negative_trend
      - monthly series
      - forecasted series (3-6 months)
    """
    summary = compute_cash_health(business_id)
    forecast = forecast_cashflow(business_id, summary.series, horizon_months=horizon_months)
    return {
        "business_id": summary.business_id,
        "health_score": summary.health_score,
        "burn_rate": summary.burn_rate,
        "runway_months": summary.runway_months,
        "has_negative_trend": summary.has_negative_trend,
        "series": [
            {
                "month": m.month,
                "inflow": m.inflow,
                "outflow": m.outflow,
                "net": m.net,
            }
            for m in summary.series
        ],
        "forecast": [
            {
                "month": m.month,
                "inflow": m.inflow,
                "outflow": m.outflow,
                "net": m.net,
            }
            for m in forecast.projected_months
        ],
        "horizon_months": forecast.horizon_months,
    }


