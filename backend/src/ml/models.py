"""ML model definitions and interfaces."""
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel


class ModelMetadata(BaseModel):
    """Model version metadata."""

    version: str
    created_at: datetime
    algorithm: str  # 'random_forest', 'xgboost'
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    feature_importance: Dict[str, float]
    training_samples: int


class PredictionResult(BaseModel):
    """Credit scoring prediction result."""

    business_id: str
    default_probability: float
    risk_category: str  # 'low', 'medium', 'high'
    model_version: str
    prediction_date: datetime
    feature_contributions: Optional[Dict[str, float]] = None  # SHAP values
