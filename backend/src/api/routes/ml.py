"""Machine Learning API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from src.ml.prediction import predict_default
from src.ml.versioning import get_latest_version, list_versions, load_metadata
from src.ml.monitoring import (
    get_model_performance,
    get_prediction_drift,
    log_prediction,
)
from src.ml.models import PredictionResult

router = APIRouter(prefix="/ml", tags=["machine-learning"])


@router.post("/predict/{business_id}", response_model=PredictionResult)
def predict_business_default(
    business_id: str,
    model_version: Optional[str] = Query(None, description="Model version (defaults to latest)"),
    include_shap: bool = Query(True, description="Include SHAP feature contributions"),
) -> PredictionResult:
    """Predict payment default probability for a business."""
    try:
        result = predict_default(
            business_id=business_id,
            model_version=model_version,
            include_shap=include_shap,
        )

        # Log prediction for monitoring
        log_prediction(
            business_id=business_id,
            model_version=result.model_version,
            default_probability=result.default_probability,
            risk_category=result.risk_category,
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/models")
def list_models():
    """List all available model versions."""
    versions = list_versions()
    models = []
    for version in versions:
        try:
            metadata = load_metadata(version)
            models.append(metadata.model_dump())
        except Exception:
            # Skip if metadata can't be loaded
            continue
    return {"models": models, "count": len(models)}


@router.get("/models/latest")
def get_latest_model():
    """Get the latest model version and metadata."""
    version = get_latest_version()
    if version is None:
        raise HTTPException(status_code=404, detail="No trained models available")

    metadata = load_metadata(version)
    return metadata.model_dump()


@router.get("/models/{version}")
def get_model_info(version: str):
    """Get metadata for a specific model version."""
    try:
        metadata = load_metadata(version)
        return metadata.model_dump()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Model version {version} not found")


@router.get("/monitoring/performance")
def get_performance_metrics(
    model_version: Optional[str] = None,
    days_back: int = Query(30, ge=1, le=365),
):
    """Get model performance metrics from monitoring data."""
    return get_model_performance(model_version=model_version, days_back=days_back)


@router.get("/monitoring/drift")
def get_drift_analysis(
    model_version: Optional[str] = None,
    days_back: int = Query(7, ge=1, le=90),
):
    """Get prediction drift analysis."""
    return get_prediction_drift(model_version=model_version, days_back=days_back)
