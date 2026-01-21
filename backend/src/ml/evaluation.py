"""Model evaluation metrics."""
from typing import Dict, Optional
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)

from src.ml.models import ModelMetrics
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def evaluate_model(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray] = None,
    model_version: str = "1.0.0",
) -> ModelMetrics:
    """
    Evaluate model performance.

    Returns accuracy, precision, recall, F1, and ROC AUC.
    """
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    roc_auc = 0.0
    if y_proba is not None and len(np.unique(y_true)) > 1:
        try:
            roc_auc = roc_auc_score(y_true, y_proba)
        except Exception as e:
            logger.warning("Could not calculate ROC AUC", error=str(e))

    # Log confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    logger.info(
        "Model evaluation",
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1=f1,
        roc_auc=roc_auc,
        confusion_matrix=cm.tolist(),
    )

    return ModelMetrics(
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1_score=f1,
        roc_auc=roc_auc,
        model_version=model_version,
    )


def get_feature_importance(model, feature_names: list) -> Dict[str, float]:
    """Get feature importance from trained model."""
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
        return dict(zip(feature_names, importances))
    return {}
