"""Feature extraction from graph and business data."""
from typing import Dict, Optional
from datetime import datetime

from src.infrastructure.database.neo4j_client import neo4j_client
from src.risk.scoring.engine import compute_business_risk
from src.risk.cashflow.calculator import compute_cash_health
from src.risk.supplier.analyzer import analyze_supplier_risk
from src.ml.models import FeatureVector


def extract_features(business_id: str) -> FeatureVector:
    """
    Extract features for credit scoring from graph and business data.

    Features:
    - Payment history score
    - Cash flow trend
    - Risk score
    - Business age (months)
    - Industry risk
    - Transaction volume
    - Average transaction amount
    - Supplier concentration
    - Late payment ratio
    - Default history
    """
    # Get business node
    business = neo4j_client.find_node("Business", {"id": business_id})
    if not business:
        raise ValueError(f"Business {business_id} not found")

    # Extract payment history
    payment_history_score = _extract_payment_history(business_id)

    # Extract cash flow trend
    cashflow_trend = _extract_cashflow_trend(business_id)

    # Get risk score
    risk_result = compute_business_risk(business_id)
    risk_score = risk_result.composite_score if risk_result else 50.0

    # Business age
    business_age_months = _extract_business_age(business)

    # Industry risk (simplified - would use industry risk database)
    industry_risk = _extract_industry_risk(business)

    # Transaction volume and average
    transaction_stats = _extract_transaction_stats(business_id)
    transaction_volume = transaction_stats.get("volume", 0.0)
    avg_transaction_amount = transaction_stats.get("avg_amount", 0.0)

    # Supplier concentration
    supplier_risk = analyze_supplier_risk(business_id)
    supplier_concentration = supplier_risk.get("concentration", {}).get("hhi_index", 0.0) / 10000.0

    # Late payment ratio
    late_payment_ratio = _extract_late_payment_ratio(business_id)

    # Default history
    default_history = _extract_default_history(business_id)

    return FeatureVector(
        payment_history_score=payment_history_score,
        cashflow_trend=cashflow_trend,
        risk_score=risk_score,
        business_age_months=business_age_months,
        industry_risk=industry_risk,
        transaction_volume=transaction_volume,
        avg_transaction_amount=avg_transaction_amount,
        supplier_concentration=supplier_concentration,
        late_payment_ratio=late_payment_ratio,
        default_history=default_history,
    )


def _extract_payment_history(business_id: str) -> float:
    """Extract payment history score (0-100, higher = better)."""
    query = """
    MATCH (b:Business {id: $business_id})<-[:INVOLVES]-(t:Transaction)
    WHERE t.due_date IS NOT NULL AND t.paid_date IS NOT NULL
    WITH t, duration.between(date(t.due_date), date(t.paid_date)).days as days_late
    WITH 
        count(t) as total,
        sum(CASE WHEN days_late <= 0 THEN 1 ELSE 0 END) as on_time,
        sum(CASE WHEN days_late > 60 THEN 1 ELSE 0 END) as defaults
    RETURN 
        CASE WHEN total > 0 
        THEN (on_time * 1.0 / total * 100 - defaults * 1.0 / total * 50)
        ELSE 50.0 END as score
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    if rows and rows[0].get("score") is not None:
        return float(rows[0]["score"])
    return 50.0  # Default neutral score


def _extract_cashflow_trend(business_id: str) -> float:
    """Extract cash flow trend (-1 to 1, positive = improving)."""
    try:
        cash_health = compute_cash_health(business_id)
        if cash_health.has_negative_trend:
            return -0.5
        # Calculate trend from series
        if len(cash_health.series) >= 3:
            recent = cash_health.series[-3:]
            net_trend = (recent[-1].net - recent[0].net) / max(abs(recent[0].net), 1)
            return max(-1.0, min(1.0, net_trend / 1000.0))  # Normalize
        return 0.0
    except Exception:
        return 0.0


def _extract_business_age(business: Dict) -> float:
    """Extract business age in months."""
    if "registration_date" in business:
        try:
            reg_date = datetime.fromisoformat(business["registration_date"].replace("Z", "+00:00"))
            age_days = (datetime.now(reg_date.tzinfo) - reg_date).days
            return age_days / 30.0  # Convert to months
        except Exception:
            pass
    return 12.0  # Default 1 year


def _extract_industry_risk(business: Dict) -> float:
    """Extract industry risk score (0-1, higher = riskier)."""
    # Simplified - would use industry risk database
    sector = business.get("sector", "").lower()
    high_risk_sectors = ["construction", "retail", "hospitality"]
    medium_risk_sectors = ["manufacturing", "services"]
    
    if any(hr in sector for hr in high_risk_sectors):
        return 0.7
    if any(mr in sector for mr in medium_risk_sectors):
        return 0.4
    return 0.2  # Low risk default


def _extract_transaction_stats(business_id: str) -> Dict[str, float]:
    """Extract transaction volume and average amount."""
    query = """
    MATCH (b:Business {id: $business_id})<-[:INVOLVES]-(t:Transaction)
    WHERE t.amount IS NOT NULL
    WITH count(t) as volume, avg(t.amount) as avg_amount
    RETURN volume, COALESCE(avg_amount, 0.0) as avg_amount
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    if rows:
        return {
            "volume": float(rows[0].get("volume", 0)),
            "avg_amount": float(rows[0].get("avg_amount", 0.0)),
        }
    return {"volume": 0.0, "avg_amount": 0.0}


def _extract_late_payment_ratio(business_id: str) -> float:
    """Extract ratio of late payments (0-1)."""
    query = """
    MATCH (b:Business {id: $business_id})<-[:INVOLVES]-(t:Transaction)
    WHERE t.due_date IS NOT NULL AND t.paid_date IS NOT NULL
    WITH t, duration.between(date(t.due_date), date(t.paid_date)).days as days_late
    WITH 
        count(t) as total,
        sum(CASE WHEN days_late > 0 THEN 1 ELSE 0 END) as late
    RETURN CASE WHEN total > 0 THEN late * 1.0 / total ELSE 0.0 END as ratio
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    if rows and rows[0].get("ratio") is not None:
        return float(rows[0]["ratio"])
    return 0.0


def _extract_default_history(business_id: str) -> int:
    """Extract number of historical defaults (60+ days overdue)."""
    query = """
    MATCH (b:Business {id: $business_id})<-[:INVOLVES]-(t:Transaction)
    WHERE t.due_date IS NOT NULL AND t.paid_date IS NOT NULL
    WITH t, duration.between(date(t.due_date), date(t.paid_date)).days as days_late
    RETURN sum(CASE WHEN days_late > 60 THEN 1 ELSE 0 END) as defaults
    """
    rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    if rows and rows[0].get("defaults") is not None:
        return int(rows[0]["defaults"])
    return 0
