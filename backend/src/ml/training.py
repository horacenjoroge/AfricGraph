"""Model training with Random Forest and XGBoost."""
import pickle
from pathlib import Path
from typing import Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import joblib

from src.infrastructure.logging import get_logger

logger = get_logger(__name__)

MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)


def prepare_training_data(
    features_df: pd.DataFrame,
    labels: pd.Series,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Prepare training data with train/test split."""
    X = features_df.values
    y = labels.values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Save scaler
    joblib.dump(scaler, MODELS_DIR / "scaler.pkl")

    return X_train_scaled, X_test_scaled, y_train, y_test


def train_random_forest(
    X_train: np.ndarray,
    y_train: np.ndarray,
    n_estimators: int = 100,
    max_depth: Optional[int] = None,
    random_state: int = 42,
) -> RandomForestClassifier:
    """Train Random Forest classifier."""
    logger.info("Training Random Forest model", n_estimators=n_estimators, max_depth=max_depth)

    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1,
        class_weight="balanced",
    )

    model.fit(X_train, y_train)

    # Save model
    model_path = MODELS_DIR / "random_forest.pkl"
    joblib.dump(model, model_path)
    logger.info("Random Forest model saved", path=str(model_path))

    return model


def train_xgboost(
    X_train: np.ndarray,
    y_train: np.ndarray,
    n_estimators: int = 100,
    max_depth: int = 6,
    learning_rate: float = 0.1,
    random_state: int = 42,
) -> xgb.XGBClassifier:
    """Train XGBoost classifier."""
    logger.info("Training XGBoost model", n_estimators=n_estimators, max_depth=max_depth)

    model = xgb.XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        random_state=random_state,
        eval_metric="logloss",
        use_label_encoder=False,
    )

    model.fit(X_train, y_train)

    # Save model
    model_path = MODELS_DIR / "xgboost.pkl"
    joblib.dump(model, model_path)
    logger.info("XGBoost model saved", path=str(model_path))

    return model


def load_model(model_type: str = "xgboost") -> Optional[object]:
    """Load trained model."""
    model_path = MODELS_DIR / f"{model_type}.pkl"
    if model_path.exists():
        return joblib.load(model_path)
    return None


def load_scaler() -> Optional[object]:
    """Load feature scaler."""
    scaler_path = MODELS_DIR / "scaler.pkl"
    if scaler_path.exists():
        return joblib.load(scaler_path)
    return None
