"""Feature extraction from graph data for credit scoring."""
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from src.infrastructure.database.neo4j_client import neo4j_client
from src.risk.scoring.engine import compute_business_risk
from src.risk.cashflow.calculator import compute_cash_health
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def extract_features(business_id: str) -> Dict[str, float]:
    """
    Extract all features for a business for credit scoring.

    Returns a dictionary of feature names to values.
    """
    features = {}

    # Payment history features
    payment_features = _extract_payment_history(business_id)
    features.update(payment_features)

    # Cash flow features
    cashflow_features = _extract_cashflow_features(business_id)
    features.update(cashflow_features)

    # Risk score
    risk_features = _extract_risk_features(business_id)
    features.update(risk_features)

    # Business age
    age_features = _extract_business_age(business_id)
    features.update(age_features)

    # Industry/sector
    industry_features = _extract_industry_features(business_id)
    features.update(industry_features)

    # Transaction volume
    transaction_features = _extract_transaction_features(business_id)
    features.update(transaction_features)

    return features


def _extract_payment_history(business_id: str) -> Dict[str, float]:
    """Extract payment history features."""
    query = """
    MATCH (b:Business {id: $business_id})<-[:INVOLVES]-(t:Transaction)
    WHERE t.transaction_type IN ['payment', 'invoice_payment']
    WITH t
    ORDER BY t.timestamp DESC
    LIMIT 100
    RETURN 
        count(t) as payment_count,
        avg(t.amount) as avg_payment_amount,
        stdDev(t.amount) as payment_amount_std,
        sum(CASE WHEN t.timestamp < datetime() - duration({days: 30}) THEN 1 ELSE 0 END) as late_payments_30d,
        sum(CASE WHEN t.timestamp < datetime() - duration({days: 60}) THEN 1 ELSE 0 END) as late_payments_60d,
        sum(CASE WHEN t.timestamp < datetime() - duration({days: 90}) THEN 1 ELSE 0 END) as late_payments_90d
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})

    if not rows or not rows[0].get("payment_count"):
        return {
            "payment_count": 0.0,
            "avg_payment_amount": 0.0,
            "payment_amount_std": 0.0,
            "late_payments_30d": 0.0,
            "late_payments_60d": 0.0,
            "late_payments_90d": 0.0,
            "on_time_payment_ratio": 0.0,
        }

    row = rows[0]
    payment_count = float(row.get("payment_count", 0))
    late_30d = float(row.get("late_payments_30d", 0))
    late_60d = float(row.get("late_payments_60d", 0))
    late_90d = float(row.get("late_payments_90d", 0))

    on_time_ratio = (
        (payment_count - late_30d) / payment_count if payment_count > 0 else 0.0
    )

    return {
        "payment_count": payment_count,
        "avg_payment_amount": float(row.get("avg_payment_amount", 0) or 0),
        "payment_amount_std": float(row.get("payment_amount_std", 0) or 0),
        "late_payments_30d": late_30d,
        "late_payments_60d": late_60d,
        "late_payments_90d": late_90d,
        "on_time_payment_ratio": on_time_ratio,
    }


def _extract_cashflow_features(business_id: str) -> Dict[str, float]:
    """Extract cash flow trend features."""
    try:
        cash_health = compute_cash_health(business_id)
        return {
            "cashflow_health_score": float(cash_health.health_score),
            "burn_rate": float(cash_health.burn_rate or 0),
            "runway_months": float(cash_health.runway_months or 0),
            "has_negative_trend": 1.0 if cash_health.has_negative_trend else 0.0,
            "avg_monthly_inflow": float(
                sum(m.inflow for m in cash_health.series) / len(cash_health.series)
                if cash_health.series
                else 0
            ),
            "avg_monthly_outflow": float(
                sum(m.outflow for m in cash_health.series) / len(cash_health.series)
                if cash_health.series
                else 0
            ),
        }
    except Exception as e:
        logger.warning(f"Failed to extract cashflow features: {e}")
        return {
            "cashflow_health_score": 0.0,
            "burn_rate": 0.0,
            "runway_months": 0.0,
            "has_negative_trend": 0.0,
            "avg_monthly_inflow": 0.0,
            "avg_monthly_outflow": 0.0,
        }


def _extract_risk_features(business_id: str) -> Dict[str, float]:
    """Extract risk score features."""
    try:
        risk_result = compute_business_risk(business_id)
        return {
            "risk_score": float(risk_result.score),
            "payment_risk": float(
                next(
                    (f.score for f in risk_result.factors if f.name == "payment_behavior"),
                    0.0,
                )
            ),
            "supplier_risk": float(
                next(
                    (
                        f.score
                        for f in risk_result.factors
                        if f.name == "supplier_concentration"
                    ),
                    0.0,
                )
            ),
            "ownership_risk": float(
                next(
                    (
                        f.score
                        for f in risk_result.factors
                        if f.name == "ownership_complexity"
                    ),
                    0.0,
                )
            ),
        }
    except Exception as e:
        logger.warning(f"Failed to extract risk features: {e}")
        return {
            "risk_score": 0.0,
            "payment_risk": 0.0,
            "supplier_risk": 0.0,
            "ownership_risk": 0.0,
        }


def _extract_business_age(business_id: str) -> Dict[str, float]:
    """Extract business age features."""
    query = """
    MATCH (b:Business {id: $business_id})
    RETURN b.created_at as created_at, b.registration_date as registration_date
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})

    if not rows:
        return {"business_age_days": 0.0, "business_age_years": 0.0}

    row = rows[0]
    created_at = row.get("created_at") or row.get("registration_date")

    if not created_at:
        return {"business_age_days": 0.0, "business_age_years": 0.0}

    # Parse date (simplified - adjust based on actual format)
    try:
        if isinstance(created_at, str):
            from dateutil import parser

            created_date = parser.parse(created_at)
        else:
            created_date = created_at

        age_delta = datetime.now() - created_date
        age_days = age_delta.days
        age_years = age_days / 365.25

        return {
            "business_age_days": float(age_days),
            "business_age_years": float(age_years),
        }
    except Exception:
        return {"business_age_days": 0.0, "business_age_years": 0.0}


def _extract_industry_features(business_id: str) -> Dict[str, float]:
    """Extract industry/sector features (one-hot encoded)."""
    query = """
    MATCH (b:Business {id: $business_id})
    RETURN b.sector as sector
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})

    sector = rows[0].get("sector") if rows else None

    # Common sectors (one-hot encoding)
    sectors = [
        "Technology",
        "Finance",
        "Retail",
        "Manufacturing",
        "Healthcare",
        "Agriculture",
        "Services",
    ]

    features = {f"industry_{s.lower()}": 0.0 for s in sectors}
    features["industry_other"] = 1.0  # Default

    if sector:
        sector_lower = sector.lower()
        for s in sectors:
            if s.lower() in sector_lower or sector_lower in s.lower():
                features[f"industry_{s.lower()}"] = 1.0
                features["industry_other"] = 0.0
                break

    return features


def _extract_transaction_features(business_id: str) -> Dict[str, float]:
    """Extract transaction volume features."""
    query = """
    MATCH (b:Business {id: $business_id})<-[:INVOLVES]-(t:Transaction)
    WITH t
    RETURN 
        count(t) as total_transactions,
        sum(t.amount) as total_volume,
        avg(t.amount) as avg_transaction_amount,
        stdDev(t.amount) as transaction_amount_std,
        count(DISTINCT date(t.timestamp)) as active_days
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})

    if not rows:
        return {
            "total_transactions": 0.0,
            "total_volume": 0.0,
            "avg_transaction_amount": 0.0,
            "transaction_amount_std": 0.0,
            "active_days": 0.0,
            "transactions_per_day": 0.0,
        }

    row = rows[0]
    total_transactions = float(row.get("total_transactions", 0))
    active_days = float(row.get("active_days", 1))

    return {
        "total_transactions": total_transactions,
        "total_volume": float(row.get("total_volume", 0) or 0),
        "avg_transaction_amount": float(row.get("avg_transaction_amount", 0) or 0),
        "transaction_amount_std": float(row.get("transaction_amount_std", 0) or 0),
        "active_days": active_days,
        "transactions_per_day": total_transactions / active_days if active_days > 0 else 0.0,
    }
