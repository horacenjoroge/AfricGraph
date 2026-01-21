"""Isolation Forest for transaction anomaly detection."""
from typing import List, Dict
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime

from src.infrastructure.database.neo4j_client import neo4j_client
from src.anomaly.models import AnomalyScore
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def detect_transaction_anomalies(
    business_id: Optional[str] = None,
    contamination: float = 0.1,
) -> List[AnomalyScore]:
    """
    Detect anomalous transactions using Isolation Forest.

    Args:
        business_id: Optional business ID to filter transactions
        contamination: Expected proportion of anomalies (0-0.5)

    Returns:
        List of AnomalyScore objects for detected anomalies
    """
    # Fetch transactions
    if business_id:
        query = """
        MATCH (b:Business {id: $business_id})<-[:INVOLVES]-(t:Transaction)
        RETURN t.id as id, t.amount as amount, t.timestamp as timestamp,
               t.transaction_type as type, id(t) as node_id
        ORDER BY t.timestamp DESC
        LIMIT 1000
        """
        rows = neo4j_client.execute_cypher(query, {"business_id": business_id})
    else:
        query = """
        MATCH (t:Transaction)
        RETURN t.id as id, t.amount as amount, t.timestamp as timestamp,
               t.transaction_type as type, id(t) as node_id
        ORDER BY t.timestamp DESC
        LIMIT 10000
        """
        rows = neo4j_client.execute_cypher(query, {})

    if not rows or len(rows) < 10:
        return []

    # Prepare features
    transactions = []
    for row in rows:
        amount = float(row.get("amount", 0) or 0)
        timestamp = row.get("timestamp")
        
        # Convert timestamp to numeric features
        if timestamp:
            if isinstance(timestamp, str):
                from dateutil import parser
                ts = parser.parse(timestamp)
            else:
                ts = timestamp
            hour = ts.hour
            day_of_week = ts.weekday()
            day_of_month = ts.day
        else:
            hour = 0
            day_of_week = 0
            day_of_month = 0

        transactions.append({
            "id": row["id"],
            "node_id": row["node_id"],
            "amount": amount,
            "hour": hour,
            "day_of_week": day_of_week,
            "day_of_month": day_of_month,
            "log_amount": np.log1p(abs(amount)),
        })

    df = pd.DataFrame(transactions)
    
    # Feature matrix
    feature_cols = ["amount", "hour", "day_of_week", "day_of_month", "log_amount"]
    X = df[feature_cols].values

    # Train Isolation Forest
    iso_forest = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=100,
    )
    predictions = iso_forest.fit_predict(X)
    anomaly_scores = -iso_forest.score_samples(X)  # Negative scores (higher = more anomalous)
    
    # Normalize scores to 0-1
    min_score = anomaly_scores.min()
    max_score = anomaly_scores.max()
    if max_score > min_score:
        normalized_scores = (anomaly_scores - min_score) / (max_score - min_score)
    else:
        normalized_scores = np.zeros_like(anomaly_scores)

    # Create results
    results = []
    for idx, row in df.iterrows():
        is_anomaly = predictions[idx] == -1
        score = float(normalized_scores[idx])
        
        if is_anomaly or score > 0.7:  # Threshold for anomalies
            results.append(
                AnomalyScore(
                    entity_id=str(row["id"]),
                    entity_type="transaction",
                    score=score,
                    is_anomaly=True,
                    detection_method="isolation_forest",
                    features={
                        "amount": float(row["amount"]),
                        "hour": int(row["hour"]),
                        "day_of_week": int(row["day_of_week"]),
                    },
                    explanation=_explain_transaction_anomaly(row, score),
                    detected_at=datetime.now(),
                )
            )

    return results


def _explain_transaction_anomaly(transaction: pd.Series, score: float) -> str:
    """Generate explanation for transaction anomaly."""
    reasons = []
    
    if abs(transaction["amount"]) > transaction["amount"] * 2:  # Simplified check
        reasons.append("unusual amount")
    
    if transaction["hour"] not in range(9, 17):  # Outside business hours
        reasons.append("unusual time")
    
    if not reasons:
        reasons.append("statistical outlier")
    
    return f"Anomaly detected (score: {score:.2f}): {', '.join(reasons)}"
