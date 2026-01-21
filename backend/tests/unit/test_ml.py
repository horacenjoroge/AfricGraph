"""Unit tests for ML models."""
import pytest
import numpy as np
from unittest.mock import Mock, patch

from src.ml.features import extract_features
from src.ml.models import ModelMetadata, PredictionResult


@pytest.mark.unit
class TestFeatureExtraction:
    """Test feature extraction for ML."""

    @patch("src.ml.features.neo4j_client")
    @patch("src.ml.features.get_business")
    def test_extract_features(self, mock_business, mock_client):
        """Test feature extraction."""
        mock_business.return_value = Mock(
            id="business-123",
            sector="Technology",
            founded_date="2020-01-01",
        )
        mock_client.execute_cypher.return_value = [
            {"payment_count": 100, "on_time_ratio": 0.9},
            {"transaction_volume": 100000},
            {"risk_score": 50.0},
        ]
        
        features = extract_features("business-123")
        assert "payment_history" in features
        assert "transaction_volume" in features
        assert "risk_score" in features


@pytest.mark.unit
class TestMLModels:
    """Test ML model classes."""

    def test_model_metadata(self):
        """Test ModelMetadata."""
        metadata = ModelMetadata(
            model_id="model-1",
            model_type="random_forest",
            version="1.0.0",
            accuracy=0.85,
        )
        assert metadata.model_id == "model-1"
        assert metadata.accuracy == 0.85

    def test_prediction_result(self):
        """Test PredictionResult."""
        result = PredictionResult(
            business_id="business-123",
            prediction=0.75,
            probability=0.85,
            features={},
        )
        assert result.business_id == "business-123"
        assert result.prediction == 0.75
