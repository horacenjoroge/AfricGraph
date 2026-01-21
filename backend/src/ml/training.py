"""Training data preparation and model training."""
from typing import List, Tuple, Dict, Optional
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import xgboost as xgb
import joblib
from datetime import datetime

from src.ml.features import extract_features
from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def prepare_training_data(
    business_ids: Optional[List[str]] = None,
    default_threshold_days: int = 90,
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepare training data from businesses and their default status.

    Args:
        business_ids: Optional list of business IDs to include. If None, uses all businesses.
        default_threshold_days: Number of days overdue to consider as default.

    Returns:
        Tuple of (features DataFrame, labels Series)
    """
    if business_ids is None:
        # Get all businesses
        query = "MATCH (b:Business) RETURN b.id as business_id"
        rows = neo4j_client.execute_cypher(query, {})
        business_ids = [row["business_id"] for row in rows]

    features_list = []
    labels = []

    for business_id in business_ids:
        try:
            # Extract features
            features = extract_features(business_id)
            features_list.append(features)

            # Determine label (1 = default, 0 = no default)
            label = _determine_default_label(business_id, default_threshold_days)
            labels.append(label)
        except Exception as e:
            logger.warning(f"Failed to process business {business_id}: {e}")
            continue

    if not features_list:
        raise ValueError("No training data could be extracted")

    # Convert to DataFrame
    df = pd.DataFrame(features_list)
    labels_series = pd.Series(labels, name="default")

    # Handle missing values
    df = df.fillna(0)

    return df, labels_series


def _determine_default_label(business_id: str, threshold_days: int) -> int:
    """Determine if a business has defaulted (1) or not (0)."""
    query = """
    MATCH (b:Business {id: $business_id})<-[:INVOLVES]-(t:Transaction)
    WHERE t.transaction_type = 'payment' 
      AND t.due_date IS NOT NULL
      AND t.timestamp < t.due_date
    WITH t, duration.between(t.due_date, t.timestamp).days as days_overdue
    WHERE days_overdue >= $threshold_days
    RETURN count(t) as default_count
    """
    rows = neo4j_client.execute_cypher(
        query, {"business_id": business_id, "threshold_days": threshold_days}
    )

    default_count = rows[0].get("default_count", 0) if rows else 0
    return 1 if default_count > 0 else 0


def train_random_forest(
    X: pd.DataFrame, y: pd.Series, n_estimators: int = 100, max_depth: int = 10
) -> Tuple[RandomForestClassifier, Dict[str, float]]:
    """Train a Random Forest classifier."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=n_estimators, max_depth=max_depth, random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
    }

    return model, metrics


def train_xgboost(
    X: pd.DataFrame, y: pd.Series, n_estimators: int = 100, max_depth: int = 6
) -> Tuple[xgb.XGBClassifier, Dict[str, float]]:
    """Train an XGBoost classifier."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = xgb.XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=42,
        eval_metric="logloss",
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
    }

    return model, metrics


def get_feature_importance(model, feature_names: List[str]) -> Dict[str, float]:
    """Extract feature importance from trained model."""
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "coef_"):
        importances = np.abs(model.coef_[0])
    else:
        return {}

    # Normalize to sum to 1
    total = sum(importances)
    if total > 0:
        importances = importances / total

    return dict(zip(feature_names, importances.tolist()))
