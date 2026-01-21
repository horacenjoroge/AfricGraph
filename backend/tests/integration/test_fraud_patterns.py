"""Integration tests for fraud pattern detection."""
import pytest
from unittest.mock import Mock, patch


@pytest.mark.integration
@pytest.mark.fraud
class TestFraudPatternDetection:
    """Test fraud pattern detection integration."""

    @patch("src.fraud.detector.neo4j_client")
    def test_circular_payment_detection(self, mock_client):
        """Test circular payment pattern detection."""
        from src.fraud.detector import run_fraud_checks_for_business
        
        # Mock circular payment cycle
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
        
        result = run_fraud_checks_for_business("business-1")
        assert "patterns" in result
        assert len(result["patterns"]) > 0

    @patch("src.fraud.detector.neo4j_client")
    def test_shell_company_detection(self, mock_client):
        """Test shell company pattern detection."""
        from src.fraud.detector import run_fraud_checks_for_business
        
        # Mock shell company characteristics
        mock_client.execute_cypher.return_value = [
            {
                "employee_count": 0,
                "transaction_count": 1000,
                "shared_directors": 5,
            }
        ]
        
        result = run_fraud_checks_for_business("business-123")
        assert "patterns" in result

    @patch("src.fraud.detector.neo4j_client")
    def test_duplicate_invoice_detection(self, mock_client):
        """Test duplicate invoice pattern detection."""
        from src.fraud.detector import run_fraud_checks_for_business
        
        # Mock duplicate invoices
        mock_client.execute_cypher.return_value = [
            {
                "invoice_number": "INV-001",
                "count": 3,
                "total_amount": 3000.0,
            }
        ]
        
        result = run_fraud_checks_for_business("business-123")
        assert "patterns" in result
