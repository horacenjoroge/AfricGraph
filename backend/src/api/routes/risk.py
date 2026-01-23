"""Risk scoring API endpoints."""
from __future__ import annotations

import json
from datetime import datetime
from fastapi import APIRouter, HTTPException

from src.risk.scoring.engine import compute_business_risk
from src.risk.scoring.history import get_latest_risk_score
from src.risk.scoring.models import RiskScoreResult, FactorScore
from src.risk.cashflow.calculator import compute_cash_health
from src.risk.cashflow.forecaster import forecast_cashflow
from src.risk.supplier.analyzer import analyze_supplier_risk

router = APIRouter(prefix="/risk", tags=["risk"])


def _convert_to_risk_score_result(data: any, business_id: str) -> RiskScoreResult:
    """Convert dict/string to RiskScoreResult object."""
    from src.infrastructure.logging import get_logger
    logger = get_logger(__name__)
    
    # If already RiskScoreResult, return as-is
    if isinstance(data, RiskScoreResult):
        logger.debug(f"Result for {business_id} is already RiskScoreResult")
        return data
    
    # Log what type we received
    logger.debug(f"Converting {type(data)} to RiskScoreResult for {business_id}")
    
    # If string, try to parse as JSON
    if isinstance(data, str):
        # Log the actual string value for debugging (truncate if too long)
        log_value = data[:200] if len(data) > 200 else data
        logger.warning(f"Cached risk score for {business_id} is a string (length: {len(data)}): {log_value}")
        
        # Check if it's a string representation of RiskScoreResult (from repr())
        if data.startswith("RiskScoreResult("):
            logger.warning(f"Cache contains string repr of RiskScoreResult for {business_id}, invalidating")
            from src.cache.invalidation import invalidate_risk_cache
            invalidate_risk_cache(business_id)
            raise ValueError(f"Invalid cached risk score format for {business_id} - cache invalidated, please retry")
        
        try:
            data = json.loads(data)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse risk score JSON for {business_id}: {e}, value: {log_value}")
            # Invalidate the bad cache entry
            from src.cache.invalidation import invalidate_risk_cache
            invalidate_risk_cache(business_id)
            raise ValueError(f"Invalid cached risk score format for {business_id} - cache invalidated, please retry")
    
    # If dict, reconstruct RiskScoreResult
    if isinstance(data, dict):
        factors = {}
        for name, factor_data in data.get("factors", {}).items():
            if isinstance(factor_data, dict):
                factors[name] = FactorScore(
                    name=name,
                    score=factor_data.get("score", 0.0),
                    details=factor_data.get("details", {})
                )
            elif isinstance(factor_data, FactorScore):
                factors[name] = factor_data
            else:
                # Try to create FactorScore from other formats
                factors[name] = FactorScore(
                    name=name,
                    score=getattr(factor_data, "score", 0.0),
                    details=getattr(factor_data, "details", {})
                )
        
        # Handle generated_at - could be string, datetime, or dict (from dataclass.asdict)
        generated_at = data.get("generated_at")
        if isinstance(generated_at, datetime):
            # Already a datetime, use as-is
            pass
        elif isinstance(generated_at, str):
            try:
                # Try ISO format first
                generated_at = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                try:
                    # Try parsing with dateutil if available
                    from dateutil import parser
                    generated_at = parser.parse(generated_at)
                except (ImportError, ValueError, AttributeError):
                    from datetime import timezone
                    generated_at = datetime.now(timezone.utc)
        elif generated_at is None:
            from datetime import timezone
            generated_at = datetime.now(timezone.utc)
        else:
            # Unknown type, use current time
            from datetime import timezone
            generated_at = datetime.now(timezone.utc)
        
        return RiskScoreResult(
            business_id=data.get("business_id", business_id),
            total_score=data.get("total_score", data.get("score", 0.0)),
            factors=factors,
            generated_at=generated_at,
            explanation=data.get("explanation", "")
        )
    
    raise ValueError(f"Unable to convert {type(data)} to RiskScoreResult")


@router.get("/business/{business_id}")
def get_business_risk(business_id: str) -> dict:
    """Compute and return current risk score for a business."""
    from src.infrastructure.logging import get_logger
    from src.cache.service import make_cache_key, CacheService
    from src.cache.config import CacheKey
    logger = get_logger(__name__)
    
    # First, try to get result (may be from cache or fresh computation)
    result = compute_business_risk(business_id)
    
    # Log what we got for debugging
    logger.debug(f"compute_business_risk returned type {type(result)} for {business_id}")
    
    try:
        # Convert to RiskScoreResult if needed (cache may return dict/string)
        result = _convert_to_risk_score_result(result, business_id)
    except ValueError as e:
        # If conversion failed due to invalid cache, invalidate using the correct cache key pattern
        # Cache key format: risk:score:compute_business_risk:BIZ003
        logger.info(f"Invalidating cache and retrying for {business_id}")
        # Invalidate all risk cache entries for this business (using pattern)
        from src.cache.invalidation import invalidate_risk_cache
        invalidate_risk_cache(business_id)
        
        # Also manually delete the specific cache key if it exists
        cache_key = make_cache_key(CacheKey.RISK_SCORE, "compute_business_risk", business_id)
        CacheService.delete(cache_key)
        logger.debug(f"Deleted specific cache key: {cache_key}")
        
        # Small delay to ensure cache deletion propagates
        import time
        time.sleep(0.1)
        
        # Now retry with fresh computation
        logger.info(f"Retrying risk score computation for {business_id} after cache invalidation")
        try:
            result = compute_business_risk(business_id)
            result = _convert_to_risk_score_result(result, business_id)
        except Exception as retry_error:
            logger.error(f"Retry failed for {business_id}: {retry_error}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to compute risk score for business '{business_id}': {str(retry_error)}"
            )
    except Exception as e:
        logger.error(f"Unexpected error processing risk score for {business_id}: {e}", exc_info=True)
        # Invalidate cache and retry once
        from src.cache.invalidation import invalidate_risk_cache
        invalidate_risk_cache(business_id)
        # Also manually delete the specific cache key
        cache_key = make_cache_key(CacheKey.RISK_SCORE, "compute_business_risk", business_id)
        CacheService.delete(cache_key)
        import time
        time.sleep(0.1)
        try:
            result = compute_business_risk(business_id)
            result = _convert_to_risk_score_result(result, business_id)
        except Exception as retry_error:
            logger.error(f"Retry failed for {business_id}: {retry_error}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to compute risk score for business '{business_id}': {str(retry_error)}"
            )
    
    return {
        "business_id": result.business_id,
        "score": result.total_score,
        "factors": {
            name: {
                "score": fs.score if isinstance(fs, FactorScore) else fs.get("score", 0.0),
                "details": fs.details if isinstance(fs, FactorScore) else fs.get("details", {}),
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


@router.get("/suppliers/{business_id}")
def get_supplier_risk(business_id: str) -> dict:
    """
    Return supplier risk analysis for a business.

    Includes:
      - concentration ratio / HHI / SPOF
      - shared directors
      - late payment patterns
      - supplier health labels
      - alternative supplier suggestions
      - dependency graph for visualization
    """
    return analyze_supplier_risk(business_id)


@router.get("/{business_id}")
def get_risk_score(business_id: str) -> dict:
    """
    Compute and return current risk score for a business.
    
    This is an alias for /business/{business_id} to match frontend expectations.
    Must be defined last to avoid conflicts with /cashflow/{business_id} and /suppliers/{business_id}.
    """
    # Validate business exists first
    from src.api.services.business import get_business
    business = get_business(business_id)
    if not business:
        raise HTTPException(
            status_code=404,
            detail=f"Business '{business_id}' not found"
        )
    return get_business_risk(business_id)

