"""Time series anomaly detection."""
from typing import List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler

from src.infrastructure.database.neo4j_client import neo4j_client
from src.anomaly.models import AnomalyScore
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def detect_timeseries_anomalies(
    business_id: str,
    metric: str = "transaction_volume",
    window_size: int = 30,
    threshold_std: float = 3.0,
) -> List[AnomalyScore]:
    """
    Detect anomalies in time series data using statistical methods.

    Args:
        business_id: Business ID to analyze
        metric: Metric to analyze ('transaction_volume', 'payment_amount', 'cashflow')
        window_size: Rolling window size in days
        threshold_std: Number of standard deviations for anomaly threshold

    Returns:
        List of AnomalyScore objects for detected anomalies
    """
    # Fetch time series data
    if metric == "transaction_volume":
        query = """
        MATCH (b:Business {id: $business_id})<-[:INVOLVES]-(t:Transaction)
        WITH date(t.timestamp) as day, count(t) as volume
        ORDER BY day DESC
        LIMIT 365
        RETURN day, volume
        """
        rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
        data = [(row["day"], float(row.get("volume", 0))) for row in rows]
    elif metric == "payment_amount":
        query = """
        MATCH (b:Business {id: $business_id})<-[:INVOLVES]-(t:Transaction)
        WHERE t.transaction_type = 'payment'
        WITH date(t.timestamp) as day, sum(t.amount) as total_amount
        ORDER BY day DESC
        LIMIT 365
        RETURN day, total_amount as value
        """
        rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
        data = [(row["day"], float(row.get("value", 0))) for row in rows]
    else:
        # Cash flow metric
        try:
            from src.risk.cashflow.calculator import compute_cash_health
            cash_health = compute_cash_health(business_id)
            data = [
                (m.month, m.net) for m in cash_health.series if hasattr(m, "month")
            ]
        except Exception:
            return []

    if len(data) < window_size:
        return []

    # Convert to DataFrame
    df = pd.DataFrame(data, columns=["date", "value"])
    df = df.sort_values("date")
    df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0)

    # Calculate rolling statistics
    df["rolling_mean"] = df["value"].rolling(window=window_size, min_periods=1).mean()
    df["rolling_std"] = df["value"].rolling(window=window_size, min_periods=1).std()

    # Identify anomalies (values beyond threshold_std from rolling mean)
    df["z_score"] = (df["value"] - df["rolling_mean"]) / (df["rolling_std"] + 1e-6)
    df["is_anomaly"] = np.abs(df["z_score"]) > threshold_std

    # Calculate anomaly scores (normalized z-score)
    df["anomaly_score"] = np.clip(
        np.abs(df["z_score"]) / threshold_std, 0, 1
    )

    # Create results
    results = []
    for _, row in df[df["is_anomaly"]].iterrows():
        results.append(
            AnomalyScore(
                entity_id=f"{business_id}_{row['date']}",
                entity_type="time_series_point",
                score=float(row["anomaly_score"]),
                is_anomaly=True,
                detection_method="time_series",
                features={
                    "value": float(row["value"]),
                    "rolling_mean": float(row["rolling_mean"]),
                    "z_score": float(row["z_score"]),
                },
                explanation=_explain_timeseries_anomaly(row, metric),
                detected_at=datetime.now(),
            )
        )

    return results


def _explain_timeseries_anomaly(row: pd.Series, metric: str) -> str:
    """Generate explanation for time series anomaly."""
    direction = "above" if row["z_score"] > 0 else "below"
    deviation = abs(row["z_score"])
    return (
        f"Anomaly in {metric}: value {direction} normal range "
        f"(z-score: {deviation:.2f}, score: {row['anomaly_score']:.2f})"
    )
