"""Anomaly detection models and results."""
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel


class AnomalyScore(BaseModel):
    """Anomaly score result."""

    entity_id: str
    entity_type: str  # 'transaction', 'business', 'time_series_point'
    score: float  # 0-1, higher = more anomalous
    is_anomaly: bool
    detection_method: str  # 'isolation_forest', 'clustering', 'time_series', 'graph_embedding'
    features: Optional[Dict[str, float]] = None
    explanation: Optional[str] = None
    detected_at: datetime


class AnomalyAlert(BaseModel):
    """Anomaly alert."""

    id: str
    entity_id: str
    entity_type: str
    anomaly_score: float
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    detected_at: datetime
    acknowledged: bool = False
