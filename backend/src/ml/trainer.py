"""CLI script for training credit scoring models."""
import argparse
from typing import Optional

from src.ml.training import (
    prepare_training_data,
    train_random_forest,
    train_xgboost,
    get_feature_importance,
)
from src.ml.versioning import save_model
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def train_model(
    algorithm: str = "random_forest",
    n_estimators: int = 100,
    max_depth: int = 10,
    business_ids: Optional[list] = None,
) -> str:
    """
    Train a credit scoring model.

    Args:
        algorithm: 'random_forest' or 'xgboost'
        n_estimators: Number of estimators
        max_depth: Maximum tree depth
        business_ids: Optional list of business IDs to train on

    Returns:
        Model version string
    """
    logger.info("Preparing training data...")
    X, y = prepare_training_data(business_ids=business_ids)

    logger.info(f"Training data: {len(X)} samples, {len(X.columns)} features")
    logger.info(f"Class distribution: {y.value_counts().to_dict()}")

    # Train model
    logger.info(f"Training {algorithm} model...")
    if algorithm == "random_forest":
        model, metrics = train_random_forest(
            X, y, n_estimators=n_estimators, max_depth=max_depth
        )
    elif algorithm == "xgboost":
        model, metrics = train_xgboost(
            X, y, n_estimators=n_estimators, max_depth=max_depth
        )
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    logger.info(f"Model metrics: {metrics}")

    # Get feature importance
    feature_importance = get_feature_importance(model, list(X.columns))

    # Save model
    version = save_model(
        model=model,
        algorithm=algorithm,
        metrics=metrics,
        feature_names=list(X.columns),
        feature_importance=feature_importance,
        training_samples=len(X),
    )

    logger.info(f"Model trained and saved: {version}")
    return version


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train credit scoring model")
    parser.add_argument(
        "--algorithm",
        choices=["random_forest", "xgboost"],
        default="random_forest",
        help="ML algorithm to use",
    )
    parser.add_argument(
        "--n-estimators", type=int, default=100, help="Number of estimators"
    )
    parser.add_argument("--max-depth", type=int, default=10, help="Max tree depth")
    parser.add_argument(
        "--business-ids",
        nargs="+",
        help="Optional list of business IDs to train on",
    )

    args = parser.parse_args()

    train_model(
        algorithm=args.algorithm,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        business_ids=args.business_ids,
    )
