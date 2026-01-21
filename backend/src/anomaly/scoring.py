"""Anomaly scoring and aggregation."""
from typing import List, Dict
from datetime import datetime

from src.anomaly.models import AnomalyScore, AnomalyAlert
from src.anomaly.isolation_forest import detect_transaction_anomalies
from src.anomaly.clustering import detect_business_anomalies
from src.anomaly.timeseries import detect_timeseries_anomalies
from src.anomaly.graph_embedding import detect_graph_anomalies
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def compute_anomaly_score(
    entity_id: str,
    entity_type: str,
    method: str = "combined",
) -> AnomalyScore:
    """
    Compute comprehensive anomaly score for an entity.

    Args:
        entity_id: Entity ID
        entity_type: Type of entity ('transaction', 'business', etc.)
        method: Detection method ('isolation_forest', 'clustering', 'combined')

    Returns:
        AnomalyScore with aggregated score
    """
    scores = []

    if entity_type == "transaction":
        # Use Isolation Forest
        anomalies = detect_transaction_anomalies()
        entity_anomalies = [a for a in anomalies if a.entity_id == entity_id]
        if entity_anomalies:
            scores.append(entity_anomalies[0].score)
    elif entity_type == "business":
        # Use clustering
        anomalies = detect_business_anomalies()
        entity_anomalies = [a for a in anomalies if a.entity_id == entity_id]
        if entity_anomalies:
            scores.append(entity_anomalies[0].score)
        
        # Also check time series
        try:
            ts_anomalies = detect_timeseries_anomalies(entity_id)
            if ts_anomalies:
                scores.append(max(a.score for a in ts_anomalies))
        except Exception:
            pass

    # Aggregate scores (max or average)
    if scores:
        final_score = max(scores)  # Use max for conservative approach
    else:
        final_score = 0.0

    return AnomalyScore(
        entity_id=entity_id,
        entity_type=entity_type,
        score=final_score,
        is_anomaly=final_score > 0.7,
        detection_method=method,
        detected_at=datetime.now(),
    )


def detect_all_anomalies() -> List[AnomalyScore]:
    """Run all anomaly detection methods and return combined results."""
    all_anomalies = []

    try:
        # Transaction anomalies
        transaction_anomalies = detect_transaction_anomalies()
        all_anomalies.extend(transaction_anomalies)
        logger.info(f"Detected {len(transaction_anomalies)} transaction anomalies")
    except Exception as e:
        logger.error(f"Transaction anomaly detection failed: {e}")

    try:
        # Business anomalies
        business_anomalies = detect_business_anomalies()
        all_anomalies.extend(business_anomalies)
        logger.info(f"Detected {len(business_anomalies)} business anomalies")
    except Exception as e:
        logger.error(f"Business anomaly detection failed: {e}")

    try:
        # Graph embedding anomalies
        graph_anomalies = detect_graph_anomalies()
        all_anomalies.extend(graph_anomalies)
        logger.info(f"Detected {len(graph_anomalies)} graph anomalies")
    except Exception as e:
        logger.error(f"Graph embedding detection failed: {e}")

    return all_anomalies


def create_anomaly_alert(anomaly: AnomalyScore) -> AnomalyAlert:
    """Create an alert from an anomaly score."""
    # Determine severity
    if anomaly.score >= 0.9:
        severity = "critical"
    elif anomaly.score >= 0.7:
        severity = "high"
    elif anomaly.score >= 0.5:
        severity = "medium"
    else:
        severity = "low"

    alert_id = f"{anomaly.entity_type}_{anomaly.entity_id}_{anomaly.detected_at.timestamp()}"

    description = (
        f"Anomaly detected in {anomaly.entity_type} {anomaly.entity_id}. "
        f"Score: {anomaly.score:.2f}. "
        f"Method: {anomaly.detection_method}. "
        f"{anomaly.explanation or ''}"
    )

    return AnomalyAlert(
        id=alert_id,
        entity_id=anomaly.entity_id,
        entity_type=anomaly.entity_type,
        anomaly_score=anomaly.score,
        severity=severity,
        description=description,
        detected_at=anomaly.detected_at,
        acknowledged=False,
    )
