"""Model versioning and metadata management."""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import joblib

from src.infrastructure.logging import get_logger

logger = get_logger(__name__)

MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

METADATA_FILE = MODELS_DIR / "model_metadata.json"


class ModelVersion:
    """Model version metadata."""

    def __init__(
        self,
        version: str,
        model_type: str,
        metrics: Dict,
        training_date: str,
        feature_names: list,
        hyperparameters: Dict,
    ):
        self.version = version
        self.model_type = model_type
        self.metrics = metrics
        self.training_date = training_date
        self.feature_names = feature_names
        self.hyperparameters = hyperparameters

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "model_type": self.model_type,
            "metrics": self.metrics,
            "training_date": self.training_date,
            "feature_names": self.feature_names,
            "hyperparameters": self.hyperparameters,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ModelVersion":
        """Create from dictionary."""
        return cls(
            version=data["version"],
            model_type=data["model_type"],
            metrics=data["metrics"],
            training_date=data["training_date"],
            feature_names=data["feature_names"],
            hyperparameters=data["hyperparameters"],
        )


def save_model_version(
    version: str,
    model_type: str,
    metrics: Dict,
    feature_names: list,
    hyperparameters: Dict,
) -> None:
    """Save model version metadata."""
    metadata = load_all_metadata()

    model_version = ModelVersion(
        version=version,
        model_type=model_type,
        metrics=metrics,
        training_date=datetime.now().isoformat(),
        feature_names=feature_names,
        hyperparameters=hyperparameters,
    )

    metadata[version] = model_version.to_dict()

    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Model version saved", version=version, model_type=model_type)


def load_all_metadata() -> Dict:
    """Load all model metadata."""
    if METADATA_FILE.exists():
        with open(METADATA_FILE, "r") as f:
            return json.load(f)
    return {}


def get_latest_version(model_type: str = "xgboost") -> Optional[str]:
    """Get latest model version."""
    metadata = load_all_metadata()
    
    versions = [
        (v, data["training_date"])
        for v, data in metadata.items()
        if data["model_type"] == model_type
    ]
    
    if not versions:
        return None
    
    # Sort by training date (newest first)
    versions.sort(key=lambda x: x[1], reverse=True)
    return versions[0][0]


def get_model_version(version: str) -> Optional[ModelVersion]:
    """Get specific model version metadata."""
    metadata = load_all_metadata()
    if version in metadata:
        return ModelVersion.from_dict(metadata[version])
    return None


def list_model_versions(model_type: Optional[str] = None) -> list[ModelVersion]:
    """List all model versions, optionally filtered by type."""
    metadata = load_all_metadata()
    
    versions = []
    for version_data in metadata.values():
        if model_type is None or version_data["model_type"] == model_type:
            versions.append(ModelVersion.from_dict(version_data))
    
    # Sort by training date (newest first)
    versions.sort(key=lambda x: x.training_date, reverse=True)
    return versions
