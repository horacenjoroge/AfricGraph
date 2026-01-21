"""Model monitoring and performance tracking."""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from src.ml.prediction import predict_default
from src.ml.versioning import get_latest_version, load_metadata
from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def ensure_monitoring_table():
    """Create table for storing prediction monitoring data."""
    query = """
    CREATE TABLE IF NOT EXISTS ml_predictions (
        id SERIAL PRIMARY KEY,
        business_id VARCHAR(255) NOT NULL,
        model_version VARCHAR(100) NOT NULL,
        prediction_date TIMESTAMP NOT NULL,
        default_probability FLOAT NOT NULL,
        risk_category VARCHAR(20) NOT NULL,
        actual_default BOOLEAN,
        actual_default_date TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_ml_predictions_business ON ml_predictions(business_id);
    CREATE INDEX IF NOT EXISTS idx_ml_predictions_date ON ml_predictions(prediction_date);
    """
    postgres_client.execute_query(query)


def log_prediction(
    business_id: str,
    model_version: str,
    default_probability: float,
    risk_category: str,
):
    """Log a prediction for monitoring."""
    ensure_monitoring_table()

    query = """
    INSERT INTO ml_predictions 
    (business_id, model_version, prediction_date, default_probability, risk_category)
    VALUES ($1, $2, $3, $4, $5)
    """
    postgres_client.execute_query(
        query,
        (
            business_id,
            model_version,
            datetime.now(),
            default_probability,
            risk_category,
        ),
    )


def update_actual_default(business_id: str, default_date: Optional[datetime] = None):
    """Update predictions with actual default outcome."""
    ensure_monitoring_table()

    if default_date is None:
        default_date = datetime.now()

    query = """
    UPDATE ml_predictions
    SET actual_default = TRUE, actual_default_date = $1
    WHERE business_id = $2 AND actual_default IS NULL
    """
    postgres_client.execute_query(query, (default_date, business_id))


def get_model_performance(
    model_version: Optional[str] = None,
    days_back: int = 30,
) -> Dict:
    """Calculate model performance metrics from logged predictions."""
    ensure_monitoring_table()

    if model_version is None:
        model_version = get_latest_version()

    if model_version is None:
        return {"error": "No model version specified"}

    cutoff_date = datetime.now() - timedelta(days=days_back)

    query = """
    SELECT 
        COUNT(*) as total_predictions,
        COUNT(actual_default) as predictions_with_outcome,
        SUM(CASE WHEN actual_default = TRUE THEN 1 ELSE 0 END) as true_positives,
        SUM(CASE WHEN actual_default = FALSE THEN 1 ELSE 0 END) as true_negatives,
        AVG(default_probability) as avg_predicted_probability,
        AVG(CASE WHEN actual_default = TRUE THEN default_probability ELSE NULL END) as avg_probability_for_defaults
    FROM ml_predictions
    WHERE model_version = $1 AND prediction_date >= $2
    """
    rows = postgres_client.execute_query(query, (model_version, cutoff_date))

    if not rows:
        return {
            "model_version": model_version,
            "total_predictions": 0,
            "predictions_with_outcome": 0,
            "accuracy": None,
            "precision": None,
            "recall": None,
        }

    row = rows[0]
    total = row["total_predictions"] or 0
    with_outcome = row["predictions_with_outcome"] or 0
    tp = row["true_positives"] or 0
    tn = row["true_negatives"] or 0

    # Calculate metrics
    fp = with_outcome - tp - tn  # False positives
    fn = 0  # Would need to track false negatives separately

    accuracy = (tp + tn) / with_outcome if with_outcome > 0 else None
    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None

    return {
        "model_version": model_version,
        "total_predictions": total,
        "predictions_with_outcome": with_outcome,
        "true_positives": tp,
        "true_negatives": tn,
        "false_positives": fp,
        "avg_predicted_probability": float(row["avg_predicted_probability"] or 0),
        "avg_probability_for_defaults": float(
            row["avg_probability_for_defaults"] or 0
        ),
        "accuracy": float(accuracy) if accuracy else None,
        "precision": float(precision) if precision else None,
        "recall": float(recall) if recall else None,
    }


def get_prediction_drift(
    model_version: Optional[str] = None,
    days_back: int = 7,
) -> Dict:
    """Detect prediction drift (changes in prediction distribution)."""
    ensure_monitoring_table()

    if model_version is None:
        model_version = get_latest_version()

    cutoff_date = datetime.now() - timedelta(days=days_back)

    query = """
    SELECT 
        DATE(prediction_date) as prediction_day,
        AVG(default_probability) as avg_probability,
        COUNT(*) as prediction_count
    FROM ml_predictions
    WHERE model_version = $1 AND prediction_date >= $2
    GROUP BY DATE(prediction_date)
    ORDER BY prediction_day DESC
    """
    rows = postgres_client.execute_query(query, (model_version, cutoff_date))

    daily_stats = [
        {
            "date": str(row["prediction_day"]),
            "avg_probability": float(row["avg_probability"] or 0),
            "count": row["prediction_count"] or 0,
        }
        for row in rows
    ]

    # Calculate drift (coefficient of variation)
    probabilities = [s["avg_probability"] for s in daily_stats]
    if len(probabilities) > 1:
        mean_prob = sum(probabilities) / len(probabilities)
        variance = sum((p - mean_prob) ** 2 for p in probabilities) / len(probabilities)
        std_dev = variance ** 0.5
        cv = std_dev / mean_prob if mean_prob > 0 else 0
    else:
        cv = 0

    return {
        "model_version": model_version,
        "days_back": days_back,
        "daily_stats": daily_stats,
        "coefficient_of_variation": float(cv),
        "drift_detected": cv > 0.2,  # Threshold for drift detection
    }
