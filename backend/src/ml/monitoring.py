"""Model monitoring and drift detection."""
from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict

from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def ensure_monitoring_table():
    """Ensure monitoring table exists."""
    query = """
    CREATE TABLE IF NOT EXISTS ml_predictions (
        id SERIAL PRIMARY KEY,
        business_id VARCHAR(255) NOT NULL,
        prediction VARCHAR(50) NOT NULL,
        probability FLOAT NOT NULL,
        credit_score FLOAT NOT NULL,
        model_version VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        actual_outcome VARCHAR(50),
        feedback_date TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_ml_predictions_business ON ml_predictions(business_id);
    CREATE INDEX IF NOT EXISTS idx_ml_predictions_created ON ml_predictions(created_at);
    """
    postgres_client.execute_query(query)


def log_prediction(
    business_id: str,
    prediction: str,
    probability: float,
    credit_score: float,
    model_version: str,
) -> None:
    """Log prediction for monitoring."""
    ensure_monitoring_table()
    
    query = """
    INSERT INTO ml_predictions (business_id, prediction, probability, credit_score, model_version)
    VALUES (%s, %s, %s, %s, %s)
    """
    postgres_client.execute_query(
        query,
        (business_id, prediction, probability, credit_score, model_version),
    )


def update_prediction_outcome(
    business_id: str,
    actual_outcome: str,
    days_back: int = 90,
) -> None:
    """Update prediction with actual outcome for model evaluation."""
    ensure_monitoring_table()
    
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    query = """
    UPDATE ml_predictions
    SET actual_outcome = %s, feedback_date = CURRENT_TIMESTAMP
    WHERE business_id = %s
      AND created_at >= %s
      AND actual_outcome IS NULL
    ORDER BY created_at DESC
    LIMIT 1
    """
    postgres_client.execute_query(
        query,
        (actual_outcome, business_id, cutoff_date),
    )


def get_model_performance(
    model_version: str,
    days: int = 30,
) -> Dict:
    """Get model performance metrics from logged predictions."""
    ensure_monitoring_table()
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    query = """
    SELECT 
        COUNT(*) as total_predictions,
        COUNT(actual_outcome) as labeled_predictions,
        AVG(CASE WHEN prediction = actual_outcome THEN 1.0 ELSE 0.0 END) as accuracy,
        AVG(probability) as avg_probability,
        AVG(credit_score) as avg_credit_score
    FROM ml_predictions
    WHERE model_version = %s
      AND created_at >= %s
      AND actual_outcome IS NOT NULL
    """
    rows = postgres_client.execute_query(query, (model_version, cutoff_date))
    
    if rows and rows[0]:
        return {
            "total_predictions": rows[0][0] or 0,
            "labeled_predictions": rows[0][1] or 0,
            "accuracy": float(rows[0][2]) if rows[0][2] else 0.0,
            "avg_probability": float(rows[0][3]) if rows[0][3] else 0.0,
            "avg_credit_score": float(rows[0][4]) if rows[0][4] else 0.0,
        }
    
    return {
        "total_predictions": 0,
        "labeled_predictions": 0,
        "accuracy": 0.0,
        "avg_probability": 0.0,
        "avg_credit_score": 0.0,
    }


def detect_data_drift(
    model_version: str,
    reference_period_days: int = 30,
    current_period_days: int = 7,
) -> Dict:
    """Detect data drift by comparing feature distributions."""
    # This is a simplified implementation
    # In production, would use statistical tests (KS test, PSI, etc.)
    
    ensure_monitoring_table()
    
    reference_cutoff = datetime.now() - timedelta(days=reference_period_days + current_period_days)
    current_cutoff = datetime.now() - timedelta(days=current_period_days)
    
    # Compare average probabilities
    query = """
    SELECT 
        AVG(probability) as avg_prob,
        STDDEV(probability) as std_prob
    FROM ml_predictions
    WHERE model_version = %s
      AND created_at >= %s
      AND created_at < %s
    """
    
    reference_rows = postgres_client.execute_query(
        query,
        (model_version, reference_cutoff, current_cutoff),
    )
    current_rows = postgres_client.execute_query(
        query,
        (model_version, current_cutoff, datetime.now()),
    )
    
    if reference_rows and current_rows and reference_rows[0] and current_rows[0]:
        ref_avg = float(reference_rows[0][0]) if reference_rows[0][0] else 0.0
        curr_avg = float(current_rows[0][0]) if current_rows[0][0] else 0.0
        
        drift_score = abs(curr_avg - ref_avg) / max(ref_avg, 0.01)
        
        return {
            "drift_detected": drift_score > 0.1,  # 10% threshold
            "drift_score": drift_score,
            "reference_avg": ref_avg,
            "current_avg": curr_avg,
        }
    
    return {
        "drift_detected": False,
        "drift_score": 0.0,
        "reference_avg": 0.0,
        "current_avg": 0.0,
    }
