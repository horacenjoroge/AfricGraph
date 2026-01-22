"""Anomaly detection API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from src.anomaly.scoring import (
    compute_anomaly_score,
    detect_all_anomalies,
    create_anomaly_alert,
)
from src.anomaly.alerts import list_alerts, acknowledge_alert, save_alert, ensure_alerts_table
from src.anomaly.isolation_forest import detect_transaction_anomalies
from src.anomaly.clustering import detect_business_anomalies
from src.anomaly.timeseries import detect_timeseries_anomalies
from src.anomaly.graph_embedding import detect_graph_anomalies
from src.anomaly.models import AnomalyScore, AnomalyAlert

router = APIRouter(prefix="/anomaly", tags=["anomaly-detection"])


@router.post("/detect/all", response_model=List[AnomalyScore])
def detect_all():
    """Run all anomaly detection methods."""
    anomalies = detect_all_anomalies()
    
    # Create and save alerts for high-severity anomalies
    for anomaly in anomalies:
        if anomaly.score >= 0.7:
            alert = create_anomaly_alert(anomaly)
            save_alert(alert)
    
    return anomalies


@router.post("/detect/transaction", response_model=List[AnomalyScore])
def detect_transaction_anomalies_endpoint(
    business_id: Optional[str] = Query(None),
    contamination: float = Query(0.1, ge=0.01, le=0.5),
):
    """Detect transaction anomalies using Isolation Forest."""
    anomalies = detect_transaction_anomalies(
        business_id=business_id,
        contamination=contamination,
    )
    return anomalies


@router.post("/detect/business", response_model=List[AnomalyScore])
def detect_business_anomalies_endpoint(
    method: str = Query("kmeans", pattern="^(kmeans|dbscan)$"),
    n_clusters: int = Query(5, ge=2, le=20),
):
    """Detect business anomalies using clustering."""
    anomalies = detect_business_anomalies(
        method=method,
        n_clusters=n_clusters,
    )
    return anomalies


@router.post("/detect/timeseries/{business_id}", response_model=List[AnomalyScore])
def detect_timeseries_anomalies_endpoint(
    business_id: str,
    metric: str = Query("transaction_volume", pattern="^(transaction_volume|payment_amount|cashflow)$"),
    threshold_std: float = Query(3.0, ge=1.0, le=5.0),
):
    """Detect time series anomalies for a business."""
    anomalies = detect_timeseries_anomalies(
        business_id=business_id,
        metric=metric,
        threshold_std=threshold_std,
    )
    return anomalies


@router.post("/detect/graph", response_model=List[AnomalyScore])
def detect_graph_anomalies_endpoint(
    node_type: str = Query("Business"),
    contamination: float = Query(0.1, ge=0.01, le=0.5),
):
    """Detect anomalies using graph embeddings."""
    anomalies = detect_graph_anomalies(
        node_type=node_type,
        contamination=contamination,
    )
    return anomalies


@router.get("/score/{entity_type}/{entity_id}", response_model=AnomalyScore)
def get_anomaly_score(
    entity_type: str,
    entity_id: str,
    method: str = Query("combined"),
):
    """Get anomaly score for a specific entity."""
    try:
        score = compute_anomaly_score(
            entity_id=entity_id,
            entity_type=entity_type,
            method=method,
        )
        return score
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute score: {str(e)}")


@router.get("/alerts", response_model=List[AnomalyAlert])
def get_alerts(
    entity_id: Optional[str] = None,
    severity: Optional[str] = Query(None, pattern="^(low|medium|high|critical)$"),
    acknowledged: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=1000),
):
    """List anomaly alerts."""
    ensure_alerts_table()
    alerts = list_alerts(
        entity_id=entity_id,
        severity=severity,
        acknowledged=acknowledged,
        limit=limit,
    )
    return alerts


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_anomaly_alert(alert_id: str):
    """Acknowledge an anomaly alert."""
    ensure_alerts_table()
    success = acknowledge_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "acknowledged", "alert_id": alert_id}
