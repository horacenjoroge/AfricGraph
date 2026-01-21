"""Model prediction with SHAP explainability."""
from typing import Dict, Optional
import numpy as np
import pandas as pd
from datetime import datetime

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    shap = None

from src.ml.features import extract_features
from src.ml.versioning import load_model, load_feature_names, get_latest_version
from src.ml.models import PredictionResult
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def predict_default(
    business_id: str,
    model_version: Optional[str] = None,
    include_shap: bool = True,
) -> PredictionResult:
    """
    Predict payment default probability for a business.

    Args:
        business_id: Business ID to predict for
        model_version: Model version to use (defaults to latest)
        include_shap: Whether to include SHAP feature contributions

    Returns:
        PredictionResult with probability and explanations
    """
    # Load model
    if model_version is None:
        model_version = get_latest_version()
        if model_version is None:
            raise ValueError("No trained model available")

    model = load_model(model_version)
    feature_names = load_feature_names(model_version)

    # Extract features
    features = extract_features(business_id)

    # Convert to DataFrame with correct feature order
    feature_vector = pd.DataFrame([features])[feature_names]

    # Predict probability
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(feature_vector)[0]
        default_probability = float(probabilities[1])  # Probability of class 1 (default)
    else:
        # Fallback for models without predict_proba
        prediction = model.predict(feature_vector)[0]
        default_probability = float(prediction)

    # Determine risk category
    if default_probability >= 0.7:
        risk_category = "high"
    elif default_probability >= 0.4:
        risk_category = "medium"
    else:
        risk_category = "low"

    # Calculate SHAP values if requested and available
    feature_contributions = None
    if include_shap and SHAP_AVAILABLE:
        try:
            feature_contributions = _calculate_shap_values(
                model, feature_vector, feature_names
            )
        except Exception as e:
            logger.warning(f"Failed to calculate SHAP values: {e}")

    return PredictionResult(
        business_id=business_id,
        default_probability=default_probability,
        risk_category=risk_category,
        model_version=model_version,
        prediction_date=datetime.now(),
        feature_contributions=feature_contributions,
    )


def _calculate_shap_values(
    model, feature_vector: pd.DataFrame, feature_names: list
) -> Dict[str, float]:
    """Calculate SHAP values for feature contributions."""
    if not SHAP_AVAILABLE:
        return {}

    try:
        # Use TreeExplainer for tree-based models (Random Forest, XGBoost)
        if hasattr(model, "estimators_") or hasattr(model, "get_booster"):
            explainer = shap.TreeExplainer(model)
        else:
            # Fallback to KernelExplainer (slower but more general)
            explainer = shap.KernelExplainer(model.predict_proba, feature_vector)

        shap_values = explainer.shap_values(feature_vector)

        # Handle different SHAP output formats
        if isinstance(shap_values, list):
            # Binary classification: use values for positive class
            shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]

        # Convert to dictionary
        contributions = {}
        for i, feature_name in enumerate(feature_names):
            if i < len(shap_values[0]):
                contributions[feature_name] = float(shap_values[0][i])

        return contributions
    except Exception as e:
        logger.error(f"SHAP calculation error: {e}")
        return {}
