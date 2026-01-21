"""Risk scoring API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.risk.scoring.engine import compute_business_risk
from src.risk.scoring.history import get_latest_risk_score

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

