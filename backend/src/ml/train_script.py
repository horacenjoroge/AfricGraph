"""Script to train credit scoring models."""
import pandas as pd
import numpy as np
from pathlib import Path

from src.ml.training import (
    prepare_training_data,
    train_random_forest,
    train_xgboost,
)
from src.ml.evaluation import evaluate_model
from src.ml.versioning import save_model_version, get_latest_version
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)

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


def load_training_data(file_path: str) -> tuple[pd.DataFrame, pd.Series]:
    """
    Load training data from CSV.

    Expected format:
    - Columns: feature names + 'default' (0 or 1)
    """
    df = pd.read_csv(file_path)
    
    # Separate features and labels
    features = df[FEATURE_NAMES]
    labels = df["default"]
    
    return features, labels


def train_models(
    training_data_path: str,
    model_types: list[str] = ["xgboost", "random_forest"],
    test_size: float = 0.2,
) -> dict:
    """
    Train credit scoring models.

    Returns training results with metrics.
    """
    logger.info("Loading training data", path=training_data_path)
    features, labels = load_training_data(training_data_path)

    logger.info("Preparing training data", test_size=test_size)
    X_train, X_test, y_train, y_test = prepare_training_data(
        features, labels, test_size=test_size
    )

    results = {}

    for model_type in model_types:
        logger.info("Training model", type=model_type)

        # Train model
        if model_type == "xgboost":
            model = train_xgboost(X_train, y_train)
        elif model_type == "random_forest":
            model = train_random_forest(X_train, y_train)
        else:
            logger.warning("Unknown model type, skipping", type=model_type)
            continue

        # Evaluate
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None

        metrics = evaluate_model(y_test, y_pred, y_proba, model_version="1.0.0")

        # Get latest version number
        latest_version = get_latest_version(model_type)
        if latest_version:
            version_parts = latest_version.split(".")
            new_version = f"{version_parts[0]}.{version_parts[1]}.{int(version_parts[2]) + 1}"
        else:
            new_version = "1.0.0"

        # Save version metadata
        save_model_version(
            version=new_version,
            model_type=model_type,
            metrics=metrics.model_dump(),
            feature_names=FEATURE_NAMES,
            hyperparameters={
                "test_size": test_size,
                "n_estimators": 100,
                "max_depth": 6 if model_type == "xgboost" else None,
            },
        )

        results[model_type] = {
            "version": new_version,
            "metrics": metrics.model_dump(),
        }

        logger.info(
            "Model training completed",
            type=model_type,
            version=new_version,
            accuracy=metrics.accuracy,
        )

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python train_script.py <training_data.csv>")
        sys.exit(1)

    training_data_path = sys.argv[1]
    results = train_models(training_data_path)
    print("\nTraining Results:")
    print("=" * 50)
    for model_type, result in results.items():
        print(f"\n{model_type.upper()}:")
        print(f"  Version: {result['version']}")
        print(f"  Accuracy: {result['metrics']['accuracy']:.4f}")
        print(f"  Precision: {result['metrics']['precision']:.4f}")
        print(f"  Recall: {result['metrics']['recall']:.4f}")
        print(f"  F1 Score: {result['metrics']['f1_score']:.4f}")
        print(f"  ROC AUC: {result['metrics']['roc_auc']:.4f}")
