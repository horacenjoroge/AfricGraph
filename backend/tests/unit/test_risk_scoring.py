"""Unit tests for risk scoring."""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from src.risk.scoring.models import FactorScore, RiskScoreResult
from src.risk.scoring.payment_analyzer import analyze_payment_behavior
from src.risk.scoring.supplier_analyzer import analyze_supplier_concentration
from src.risk.scoring.ownership_analyzer import analyze_ownership_complexity
from src.risk.scoring.cashflow_analyzer import analyze_cashflow_health
from src.risk.scoring.network_analyzer import analyze_network_exposure


@pytest.mark.unit
class TestFactorScore:
    """Test FactorScore model."""

    def test_factor_score_creation(self):
        """Test creating a FactorScore."""
        score = FactorScore(
            name="test_factor",
            score=75.5,
            details={"key": "value"},
        )
        assert score.name == "test_factor"
        assert score.score == 75.5
        assert score.details == {"key": "value"}


@pytest.mark.unit
class TestRiskScoreResult:
    """Test RiskScoreResult model."""

    def test_risk_score_result_creation(self):
        """Test creating a RiskScoreResult."""
        factors = {
            "factor1": FactorScore(name="factor1", score=50.0, details={}),
        }
        result = RiskScoreResult(
            business_id="business-123",
            timestamp=datetime.now(timezone.utc),
            composite_score=50.0,
            factor_scores=list(factors.values()),
            explanation="Test explanation",
        )
        assert result.business_id == "business-123"
        assert result.composite_score == 50.0
        assert len(result.factor_scores) == 1


@pytest.mark.unit
class TestPaymentAnalyzer:
    """Test payment behavior analyzer."""

    @patch("src.risk.scoring.payment_analyzer.neo4j_client")
    def test_analyze_payment_behavior_good(self, mock_client):
        """Test payment analysis with good payment history."""
        mock_client.execute_cypher.return_value = [
            {
                "on_time_count": 90,
                "late_count": 10,
                "default_count": 0,
                "total_payments": 100,
            }
        ]
        
        result = analyze_payment_behavior("business-123")
        assert result.name == "payment_behavior"
        assert result.score < 50  # Good payment history = low risk
        assert "on_time_ratio" in result.details

    @patch("src.risk.scoring.payment_analyzer.neo4j_client")
    def test_analyze_payment_behavior_poor(self, mock_client):
        """Test payment analysis with poor payment history."""
        mock_client.execute_cypher.return_value = [
            {
                "on_time_count": 30,
                "late_count": 50,
                "default_count": 20,
                "total_payments": 100,
            }
        ]
        
        result = analyze_payment_behavior("business-123")
        assert result.name == "payment_behavior"
        assert result.score > 70  # Poor payment history = high risk


@pytest.mark.unit
class TestSupplierAnalyzer:
    """Test supplier concentration analyzer."""

    @patch("src.risk.scoring.supplier_analyzer.neo4j_client")
    def test_analyze_supplier_concentration_low(self, mock_client):
        """Test supplier analysis with low concentration."""
        mock_client.execute_cypher.return_value = [
            {"supplier_id": "supplier-1", "total_amount": 1000},
            {"supplier_id": "supplier-2", "total_amount": 1000},
            {"supplier_id": "supplier-3", "total_amount": 1000},
        ]
        
        result = analyze_supplier_concentration("business-123")
        assert result.name == "supplier_concentration"
        assert result.score < 50  # Low concentration = low risk

    @patch("src.risk.scoring.supplier_analyzer.neo4j_client")
    def test_analyze_supplier_concentration_high(self, mock_client):
        """Test supplier analysis with high concentration."""
        mock_client.execute_cypher.return_value = [
            {"supplier_id": "supplier-1", "total_amount": 9000},
            {"supplier_id": "supplier-2", "total_amount": 500},
            {"supplier_id": "supplier-3", "total_amount": 500},
        ]
        
        result = analyze_supplier_concentration("business-123")
        assert result.name == "supplier_concentration"
        assert result.score > 70  # High concentration = high risk


@pytest.mark.unit
class TestOwnershipAnalyzer:
    """Test ownership complexity analyzer."""

    @patch("src.risk.scoring.ownership_analyzer.neo4j_client")
    def test_analyze_ownership_simple(self, mock_client):
        """Test ownership analysis with simple structure."""
        mock_client.execute_cypher.return_value = [
            {"owner_count": 1, "max_depth": 1, "has_circular": False},
        ]
        
        result = analyze_ownership_complexity("business-123")
        assert result.name == "ownership_complexity"
        assert result.score < 30  # Simple ownership = low risk

    @patch("src.risk.scoring.ownership_analyzer.neo4j_client")
    def test_analyze_ownership_complex(self, mock_client):
        """Test ownership analysis with complex structure."""
        mock_client.execute_cypher.return_value = [
            {"owner_count": 10, "max_depth": 5, "has_circular": True},
        ]
        
        result = analyze_ownership_complexity("business-123")
        assert result.name == "ownership_complexity"
        assert result.score > 70  # Complex ownership = high risk
