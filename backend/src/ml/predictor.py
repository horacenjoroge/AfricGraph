"""Credit scoring prediction service."""
from typing import Optional
import numpy as np
import joblib

from src.ml.feature_extraction import extract_features
from src.ml.training import load_model, load_scaler
from src.ml.versioning import get_latest_version
from src.ml.models import PredictionResponse, FeatureVector
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def predict_default(
    business_id: str,
    features: Optional[FeatureVector] = None,
    model_type: str = "xgboost",
    model_version: Optional[str] = None,
) -> PredictionResponse:
    """
    Predict payment default probability for a business.

    Returns prediction with probability and confidence.
    """
    # Load model
    if model_version:
        model_path = f"models/{model_type}_v{model_version}.pkl"
        try:
            model = joblib.load(model_path)
        except Exception:
            logger.warning("Could not load specific version, using latest", version=model_version)
            model = load_model(model_type)
    else:
        model = load_model(model_type)

    if not model:
        raise ValueError(f"Model {model_type} not found. Train a model first.")

    scaler = load_scaler()
    if not scaler:
        raise ValueError("Scaler not found. Train a model first.")

    # Extract or use provided features
    if features is None:
        features = extract_features(business_id)

    # Prepare feature array
    feature_array = np.array([[
        features.payment_history_score,
        features.cashflow_trend,
        features.risk_score,
        features.business_age_months,
        features.industry_risk,
        features.transaction_volume,
        features.avg_transaction_amount,
        features.supplier_concentration,
        features.late_payment_ratio,
        features.default_history,
    ]])

    # Scale features
    feature_array_scaled = scaler.transform(feature_array)

    # Predict
    probability = model.predict_proba(feature_array_scaled)[0]
    default_probability = probability[1] if len(probability) > 1 else probability[0]
    
    prediction_class = model.predict(feature_array_scaled)[0]
    prediction = "default" if prediction_class == 1 else "no_default"

    # Calculate confidence (distance from decision boundary)
    confidence = abs(default_probability - 0.5) * 2  # Normalize to 0-1

    # Calculate credit score (0-1000, higher = better)
    credit_score = (1 - default_probability) * 1000

    # Get model version
    version = model_version or get_latest_version(model_type) or "1.0.0"

    logger.info(
        "Prediction made",
        business_id=business_id,
        default_probability=default_probability,
        prediction=prediction,
        confidence=confidence,
    )

    return PredictionResponse(
        business_id=business_id,
        default_probability=float(default_probability),
        credit_score=float(credit_score),
        prediction=prediction,
        confidence=float(confidence),
        model_version=version,
    )
