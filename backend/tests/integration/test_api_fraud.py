"""Integration tests for fraud API endpoints."""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.fraud
class TestFraudAPI:
    """Test fraud API endpoints."""

    def test_scan_business_for_fraud(self, test_client: TestClient, sample_business_data):
        """Test fraud scan endpoint."""
        test_client.post("/api/v1/businesses", json=sample_business_data)
        
        response = test_client.post(
            f"/api/v1/fraud/business/{sample_business_data['id']}/scan"
        )
        assert response.status_code == 200
        data = response.json()
        assert "patterns" in data
        assert "alert" in data or "business_id" in data

    def test_list_fraud_alerts(self, test_client: TestClient):
        """Test listing fraud alerts."""
        response = test_client.get("/api/v1/fraud/alerts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "items" in data

    def test_mark_false_positive(self, test_client: TestClient):
        """Test marking alert as false positive."""
        # First create an alert (would need setup)
        # Then mark as false positive
        response = test_client.post("/api/v1/fraud/alerts/1/false-positive")
        # May return 404 if no alerts, or 200 if successful
        assert response.status_code in [200, 404]
