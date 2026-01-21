"""Clustering for business segmentation and anomaly detection."""
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from datetime import datetime

from src.infrastructure.database.neo4j_client import neo4j_client
from src.ml.features import extract_features
from src.anomaly.models import AnomalyScore
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def detect_business_anomalies(
    n_clusters: int = 5,
    min_cluster_size: int = 3,
    method: str = "kmeans",
) -> List[AnomalyScore]:
    """
    Detect anomalous businesses using clustering.

    Businesses in small clusters or far from cluster centers are considered anomalies.

    Args:
        n_clusters: Number of clusters for KMeans
        min_cluster_size: Minimum cluster size (for DBSCAN)
        method: 'kmeans' or 'dbscan'

    Returns:
        List of AnomalyScore objects for detected anomalies
    """
    # Get all businesses
    query = "MATCH (b:Business) RETURN b.id as business_id LIMIT 1000"
    rows = neo4j_client.execute_cypher(query, {})
    business_ids = [row["business_id"] for row in rows]

    if len(business_ids) < 10:
        return []

    # Extract features for all businesses
    features_list = []
    valid_business_ids = []
    
    for business_id in business_ids:
        try:
            features = extract_features(business_id)
            features_list.append(features)
            valid_business_ids.append(business_id)
        except Exception as e:
            logger.warning(f"Failed to extract features for {business_id}: {e}")
            continue

    if not features_list:
        return []

    # Convert to DataFrame
    df = pd.DataFrame(features_list)
    df = df.fillna(0)

    # Select numeric features
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    X = df[numeric_cols].values

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Cluster
    if method == "kmeans":
        clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = clusterer.fit_predict(X_scaled)
        centers = clusterer.cluster_centers_
    else:  # DBSCAN
        clusterer = DBSCAN(min_samples=min_cluster_size, eps=0.5)
        labels = clusterer.fit_predict(X_scaled)
        centers = None

    # Calculate distances to cluster centers (for KMeans)
    if method == "kmeans" and centers is not None:
        distances = []
        for i, point in enumerate(X_scaled):
            cluster_id = labels[i]
            if cluster_id >= 0:
                center = centers[cluster_id]
                distance = np.linalg.norm(point - center)
                distances.append(distance)
            else:
                distances.append(np.inf)  # Noise points in DBSCAN
        distances = np.array(distances)
        
        # Normalize distances to 0-1
        if distances.max() > distances.min():
            normalized_distances = (distances - distances.min()) / (distances.max() - distances.min())
        else:
            normalized_distances = np.zeros_like(distances)
    else:
        # For DBSCAN, noise points are anomalies
        normalized_distances = np.array([1.0 if label == -1 else 0.0 for label in labels])

    # Count cluster sizes
    cluster_sizes = {}
    for label in labels:
        cluster_sizes[label] = cluster_sizes.get(label, 0) + 1

    # Identify anomalies
    results = []
    for i, business_id in enumerate(valid_business_ids):
        label = labels[i]
        score = float(normalized_distances[i])
        cluster_size = cluster_sizes.get(label, 0)

        # Anomaly if: small cluster, noise point, or far from center
        is_anomaly = (
            label == -1  # Noise point in DBSCAN
            or cluster_size < min_cluster_size  # Small cluster
            or score > 0.7  # Far from cluster center
        )

        if is_anomaly:
            explanation = _explain_business_anomaly(label, cluster_size, score, method)
            results.append(
                AnomalyScore(
                    entity_id=business_id,
                    entity_type="business",
                    score=score,
                    is_anomaly=True,
                    detection_method=f"clustering_{method}",
                    features={col: float(df.iloc[i][col]) for col in numeric_cols[:5]},  # Top 5 features
                    explanation=explanation,
                    detected_at=datetime.now(),
                )
            )

    return results


def _explain_business_anomaly(
    cluster_label: int, cluster_size: int, score: float, method: str
) -> str:
    """Generate explanation for business anomaly."""
    if method == "dbscan" and cluster_label == -1:
        return f"Business identified as noise point (score: {score:.2f})"
    elif cluster_size < 3:
        return f"Business in small cluster (size: {cluster_size}, score: {score:.2f})"
    else:
        return f"Business far from cluster center (score: {score:.2f})"
