"""SHAP values for model explainability."""
from typing import Dict, List, Optional
import numpy as np
import shap
import joblib

from src.ml.training import load_model, load_scaler
from src.ml.feature_extraction import extract_features
from src.ml.models import FeatureVector

FEATURE_NAMES = [
    "payment_history_score",
    "cashflow_trend",
    "risk_score",
    "business_age_months",
    "industry_risk",
    "transaction_volume",
    "avg_transaction_amount",
    "supplier_concentration",
    "late_payment_ratio",
    "default_history",
]


def get_shap_values(
    business_id: str,
    model_type: str = "xgboost",
    sample_size: int = 100,
) -> Dict[str, float]:
    """
    Get SHAP values for a business prediction.

    Returns feature importance scores explaining the prediction.
    """
    model = load_model(model_type)
    if not model:
        raise ValueError(f"Model {model_type} not found. Train a model first.")

    scaler = load_scaler()
    if not scaler:
        raise ValueError("Scaler not found. Train a model first.")

    # Extract features for the business
    features = extract_features(business_id)
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

    # Create SHAP explainer
    try:
        # For tree models, use TreeExplainer
        if hasattr(model, "tree_"):
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(feature_array_scaled)
        else:
            # For other models, use KernelExplainer (slower but more general)
            # Use a sample of training data as background
            explainer = shap.KernelExplainer(
                model.predict_proba,
                feature_array_scaled[:sample_size] if len(feature_array_scaled) > sample_size else feature_array_scaled,
            )
            shap_values = explainer.shap_values(feature_array_scaled)

        # Extract SHAP values (handle binary classification)
        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # Use positive class

        # Create feature importance dictionary
        importance = {}
        for i, feature_name in enumerate(FEATURE_NAMES):
            importance[feature_name] = float(shap_values[0][i])

        return importance
    except Exception as e:
        # Fallback: use feature importance from model
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
            return dict(zip(FEATURE_NAMES, importances.tolist()))
        raise ValueError(f"Could not compute SHAP values: {str(e)}")


def get_prediction_explanation(
    business_id: str,
    prediction: float,
    model_type: str = "xgboost",
) -> Dict:
    """
    Get human-readable explanation of prediction.

    Returns top contributing factors.
    """
    shap_values = get_shap_values(business_id, model_type)

    # Sort by absolute value
    sorted_features = sorted(
        shap_values.items(),
        key=lambda x: abs(x[1]),
        reverse=True,
    )

    # Get top 5 contributing factors
    top_factors = sorted_features[:5]

    explanation = {
        "prediction": "default" if prediction > 0.5 else "no_default",
        "probability": float(prediction),
        "top_factors": [
            {
                "feature": factor[0],
                "contribution": float(factor[1]),
                "impact": "increases_risk" if factor[1] > 0 else "decreases_risk",
            }
            for factor in top_factors
        ],
    }

    return explanation
