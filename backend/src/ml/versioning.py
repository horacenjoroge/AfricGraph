"""Model versioning and persistence."""
import os
import json
import joblib
from typing import Optional, Dict
from datetime import datetime
from pathlib import Path

from src.ml.models import ModelMetadata
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)

MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)


def save_model(
    model,
    algorithm: str,
    metrics: Dict[str, float],
    feature_names: list,
    feature_importance: Dict[str, float],
    training_samples: int,
    version: Optional[str] = None,
) -> str:
    """
    Save a trained model with metadata.

    Returns the model version string.
    """
    if version is None:
        version = datetime.now().strftime("%Y%m%d_%H%M%S")

    model_dir = MODELS_DIR / version
    model_dir.mkdir(exist_ok=True)

    # Save model
    model_path = model_dir / "model.pkl"
    joblib.dump(model, model_path)

    # Save metadata
    metadata = ModelMetadata(
        version=version,
        created_at=datetime.now(),
        algorithm=algorithm,
        accuracy=metrics.get("accuracy", 0.0),
        precision=metrics.get("precision", 0.0),
        recall=metrics.get("recall", 0.0),
        f1_score=metrics.get("f1_score", 0.0),
        feature_importance=feature_importance,
        training_samples=training_samples,
    )

    metadata_path = model_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata.model_dump(), f, indent=2, default=str)

    # Save feature names
    features_path = model_dir / "features.json"
    with open(features_path, "w") as f:
        json.dump(feature_names, f, indent=2)

    logger.info(f"Model saved: {version}")
    return version


def load_model(version: str):
    """Load a model by version."""
    model_dir = MODELS_DIR / version
    model_path = model_dir / "model.pkl"

    if not model_path.exists():
        raise FileNotFoundError(f"Model version {version} not found")

    model = joblib.load(model_path)
    return model


def load_metadata(version: str) -> ModelMetadata:
    """Load model metadata by version."""
    model_dir = MODELS_DIR / version
    metadata_path = model_dir / "metadata.json"

    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata for version {version} not found")

    with open(metadata_path, "r") as f:
        data = json.load(f)
        return ModelMetadata(**data)


def load_feature_names(version: str) -> list:
    """Load feature names for a model version."""
    model_dir = MODELS_DIR / version
    features_path = model_dir / "features.json"

    if not features_path.exists():
        raise FileNotFoundError(f"Features for version {version} not found")

    with open(features_path, "r") as f:
        return json.load(f)


def get_latest_version() -> Optional[str]:
    """Get the latest model version."""
    if not MODELS_DIR.exists():
        return None

    versions = [d.name for d in MODELS_DIR.iterdir() if d.is_dir()]
    if not versions:
        return None

    # Sort by version string (timestamp format)
    versions.sort(reverse=True)
    return versions[0]


def list_versions() -> list[str]:
    """List all available model versions."""
    if not MODELS_DIR.exists():
        return []

    return sorted([d.name for d in MODELS_DIR.iterdir() if d.is_dir()], reverse=True)
