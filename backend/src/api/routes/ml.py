"""Machine Learning API endpoints."""
from fastapi import APIRouter, HTTPException
from typing import Optional

from src.ml.models import PredictionRequest, PredictionResponse
from src.ml.predictor import predict_default
from src.ml.explainability import get_shap_values, get_prediction_explanation
from src.ml.monitoring import log_prediction, update_prediction_outcome, get_model_performance, detect_data_drift
from src.ml.versioning import list_model_versions, get_model_version

router = APIRouter(prefix="/ml", tags=["machine-learning"])


@router.post("/predict", response_model=PredictionResponse)
def predict_credit_score(request: PredictionRequest) -> PredictionResponse:
    """Predict payment default probability for a business."""
    try:
        prediction = predict_default(
            business_id=request.business_id,
            features=request.features,
        )
        
        # Log prediction for monitoring
        log_prediction(
            business_id=prediction.business_id,
            prediction=prediction.prediction,
            probability=prediction.default_probability,
            credit_score=prediction.credit_score,
            model_version=prediction.model_version,
        )
        
        return prediction
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/predict/{business_id}/explain")
def explain_prediction(
    business_id: str,
    model_type: str = "xgboost",
) -> dict:
    """Get SHAP explanation for a prediction."""
    try:
        prediction = predict_default(business_id, model_type=model_type)
        explanation = get_prediction_explanation(business_id, prediction.default_probability, model_type)
        
        return {
            "business_id": business_id,
            "prediction": explanation,
            "shap_values": get_shap_values(business_id, model_type),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")


@router.post("/predictions/{business_id}/feedback")
def submit_prediction_feedback(
    business_id: str,
    actual_outcome: str,  # "default" or "no_default"
) -> dict:
    """Submit feedback on prediction accuracy."""
    if actual_outcome not in ["default", "no_default"]:
        raise HTTPException(status_code=400, detail="actual_outcome must be 'default' or 'no_default'")
    
    update_prediction_outcome(business_id, actual_outcome)
    return {"status": "feedback recorded", "business_id": business_id}


@router.get("/models")
def list_models(model_type: Optional[str] = None) -> dict:
    """List all model versions."""
    versions = list_model_versions(model_type)
    return {
        "models": [v.to_dict() for v in versions],
        "count": len(versions),
    }


@router.get("/models/{version}")
def get_model_info(version: str) -> dict:
    """Get model version information."""
    model_version = get_model_version(version)
    if not model_version:
        raise HTTPException(status_code=404, detail="Model version not found")
    return model_version.to_dict()


@router.get("/models/{version}/performance")
def get_performance(version: str, days: int = 30) -> dict:
    """Get model performance metrics."""
    performance = get_model_performance(version, days)
    return {
        "model_version": version,
        "period_days": days,
        **performance,
    }


@router.get("/models/{version}/drift")
def check_drift(version: str) -> dict:
    """Check for data drift."""
    drift = detect_data_drift(version)
    return {
        "model_version": version,
        **drift,
    }
