"""Unit tests for fraud detection."""
import pytest
from unittest.mock import Mock, patch

from src.fraud.models import FraudPatternHit, FraudAlert, AlertSeverity
from src.fraud.patterns.circular_payments import detect_circular_payments
from src.fraud.patterns.shell_companies import detect_shell_company_signals
from src.fraud.patterns.duplicate_invoices import detect_duplicate_invoices


@pytest.mark.unit
class TestFraudPatternHit:
    """Test FraudPatternHit model."""

    def test_fraud_pattern_hit_creation(self):
        """Test creating a FraudPatternHit."""
        hit = FraudPatternHit(
            pattern="circular_payments",
            description="Circular payment detected",
            score_contribution=50.0,
            context={"cycle": ["A", "B", "C", "A"]},
        )
        assert hit.pattern == "circular_payments"
        assert hit.score_contribution == 50.0


@pytest.mark.unit
class TestFraudAlert:
    """Test FraudAlert model."""

    def test_fraud_alert_creation(self):
        """Test creating a FraudAlert."""
        alert = FraudAlert(
            business_id="business-123",
            severity=AlertSeverity.HIGH,
            score=85.0,
            description="Multiple fraud patterns detected",
            pattern_hits=[],
        )
        assert alert.business_id == "business-123"
        assert alert.severity == AlertSeverity.HIGH
        assert alert.score == 85.0


@pytest.mark.unit
class TestCircularPayments:
    """Test circular payment detection."""

    @patch("src.fraud.patterns.circular_payments.neo4j_client")
    def test_detect_circular_payments_found(self, mock_client):
        """Test detecting circular payments."""
        mock_client.execute_cypher.return_value = [
            {
                "path": [
                    {"id": "business-1"},
                    {"id": "business-2"},
                    {"id": "business-3"},
                    {"id": "business-1"},
                ],
            }
        ]
        
        hits = detect_circular_payments("business-1")
        assert len(hits) > 0
        assert hits[0].pattern == "circular_payments"

    @patch("src.fraud.patterns.circular_payments.neo4j_client")
    def test_detect_circular_payments_none(self, mock_client):
        """Test when no circular payments found."""
        mock_client.execute_cypher.return_value = []
        
        hits = detect_circular_payments("business-1")
        assert len(hits) == 0


@pytest.mark.unit
class TestShellCompanies:
    """Test shell company detection."""

    @patch("src.fraud.patterns.shell_companies.neo4j_client")
    def test_detect_shell_company_signals(self, mock_client):
        """Test detecting shell company signals."""
        mock_client.execute_cypher.return_value = [
            {
                "employee_count": 0,
                "transaction_count": 1000,
                "shared_directors": 5,
            }
        ]
        
        hits = detect_shell_company_signals("business-123")
        assert len(hits) > 0
        assert any(hit.pattern == "shell_company" for hit in hits)


@pytest.mark.unit
class TestDuplicateInvoices:
    """Test duplicate invoice detection."""

    @patch("src.fraud.patterns.duplicate_invoices.neo4j_client")
    def test_detect_duplicate_invoices(self, mock_client):
        """Test detecting duplicate invoices."""
        mock_client.execute_cypher.return_value = [
            {
                "invoice_number": "INV-001",
                "count": 3,
                "total_amount": 3000.0,
            }
        ]
        
        hits = detect_duplicate_invoices("business-123")
        assert len(hits) > 0
        assert any(hit.pattern == "duplicate_invoice" for hit in hits)
