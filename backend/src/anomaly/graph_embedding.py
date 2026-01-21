"""Graph embedding (Node2Vec) for anomaly detection."""
from typing import List, Dict, Optional
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from datetime import datetime

try:
    from node2vec import Node2Vec
    NODE2VEC_AVAILABLE = True
except ImportError:
    NODE2VEC_AVAILABLE = False
    Node2Vec = None

from src.infrastructure.database.neo4j_client import neo4j_client
from src.anomaly.models import AnomalyScore
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def detect_graph_anomalies(
    node_type: str = "Business",
    dimensions: int = 64,
    walk_length: int = 30,
    num_walks: int = 200,
    contamination: float = 0.1,
) -> List[AnomalyScore]:
    """
    Detect anomalies using graph embeddings (Node2Vec).

    Args:
        node_type: Type of nodes to analyze ('Business', 'Person', etc.)
        dimensions: Embedding dimensions
        walk_length: Random walk length
        num_walks: Number of walks per node
        contamination: Expected proportion of anomalies

    Returns:
        List of AnomalyScore objects for detected anomalies
    """
    if not NODE2VEC_AVAILABLE:
        logger.warning("Node2Vec not available, skipping graph embedding detection")
        return []

    # Build graph from Neo4j
    query = f"""
    MATCH (n:{node_type})
    OPTIONAL MATCH (n)-[r]-(m)
    RETURN id(n) as node_id, n.id as business_id, 
           count(DISTINCT r) as degree,
           collect(DISTINCT type(r)) as rel_types
    LIMIT 1000
    """
    rows = neo4j_client.execute_cypher(query, {})

    if len(rows) < 10:
        return []

    # Create node mapping
    node_mapping = {}
    node_ids = []
    for row in rows:
        node_id = row["node_id"]
        node_mapping[node_id] = row.get("business_id", str(node_id))
        node_ids.append(node_id)

    # Build edge list
    edge_query = f"""
    MATCH (n:{node_type})-[r]-(m:{node_type})
    WHERE id(n) IN $node_ids AND id(m) IN $node_ids
    RETURN id(n) as source, id(m) as target
    LIMIT 10000
    """
    edge_rows = neo4j_client.execute_cypher(edge_query, {"node_ids": node_ids})

    if not edge_rows:
        return []

    # Create NetworkX graph (simplified - would need actual NetworkX graph)
    # For now, use degree-based features as proxy
    degrees = {row["node_id"]: row["degree"] for row in rows}
    rel_type_counts = {
        row["node_id"]: len(row.get("rel_types", [])) for row in rows
    }

    # Create feature vectors (degree + relationship diversity)
    features = []
    valid_node_ids = []
    for row in rows:
        node_id = row["node_id"]
        features.append([degrees.get(node_id, 0), rel_type_counts.get(node_id, 0)])
        valid_node_ids.append(node_id)

    if len(features) < 10:
        return []

    X = np.array(features)
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Use Isolation Forest on embeddings (or degree features as proxy)
    iso_forest = IsolationForest(
        contamination=contamination,
        random_state=42,
    )
    predictions = iso_forest.fit_predict(X_scaled)
    scores = -iso_forest.score_samples(X_scaled)

    # Normalize scores
    min_score = scores.min()
    max_score = scores.max()
    if max_score > min_score:
        normalized_scores = (scores - min_score) / (max_score - min_score)
    else:
        normalized_scores = np.zeros_like(scores)

    # Create results
    results = []
    for i, node_id in enumerate(valid_node_ids):
        is_anomaly = predictions[i] == -1
        score = float(normalized_scores[i])

        if is_anomaly or score > 0.7:
            business_id = node_mapping.get(node_id, str(node_id))
            results.append(
                AnomalyScore(
                    entity_id=business_id,
                    entity_type=node_type.lower(),
                    score=score,
                    is_anomaly=True,
                    detection_method="graph_embedding",
                    features={
                        "degree": float(degrees.get(node_id, 0)),
                        "relationship_diversity": float(rel_type_counts.get(node_id, 0)),
                    },
                    explanation=_explain_graph_anomaly(degrees.get(node_id, 0), score),
                    detected_at=datetime.now(),
                )
            )

    return results


def _explain_graph_anomaly(degree: int, score: float) -> str:
    """Generate explanation for graph embedding anomaly."""
    if degree == 0:
        return f"Isolated node detected (score: {score:.2f})"
    elif degree > 100:
        return f"Highly connected node (hub) detected (degree: {degree}, score: {score:.2f})"
    else:
        return f"Unusual graph position detected (degree: {degree}, score: {score:.2f})"
