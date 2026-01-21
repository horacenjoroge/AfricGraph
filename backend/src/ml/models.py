"""ML model definitions and schemas."""
from typing import List, Optional
from pydantic import BaseModel


class FeatureVector(BaseModel):
    """Feature vector for credit scoring."""

    payment_history_score: float
    cashflow_trend: float
    risk_score: float
    business_age_months: float
    industry_risk: float
    transaction_volume: float
    avg_transaction_amount: float
    supplier_concentration: float
    late_payment_ratio: float
    default_history: int


class PredictionRequest(BaseModel):
    """Request for credit score prediction."""

    business_id: str
    features: Optional[FeatureVector] = None  # If None, will be extracted


class PredictionResponse(BaseModel):
    """Response from credit score prediction."""

    business_id: str
    default_probability: float
    credit_score: float
    prediction: str  # "default" or "no_default"
    confidence: float
    model_version: str


class ModelMetrics(BaseModel):
    """Model evaluation metrics."""

    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    model_version: str
