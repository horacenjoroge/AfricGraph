"""Integration tests for risk API endpoints."""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.api
class TestRiskAPI:
    """Test risk API endpoints."""

    def test_get_risk_assessment(self, test_client: TestClient, sample_business_data):
        """Test getting risk assessment."""
        # Create business first
        test_client.post("/api/v1/businesses", json=sample_business_data)
        
        # Get risk
        response = test_client.get(f"/api/v1/risk/{sample_business_data['id']}")
        assert response.status_code == 200
        data = response.json()
        assert "composite_score" in data or "total_score" in data
        assert "factors" in data or "factor_scores" in data

    def test_get_cashflow_health(self, test_client: TestClient, sample_business_data):
        """Test getting cash flow health."""
        test_client.post("/api/v1/businesses", json=sample_business_data)
        
        response = test_client.get(f"/api/v1/risk/cashflow/{sample_business_data['id']}")
        assert response.status_code == 200
        data = response.json()
        assert "health_score" in data
        assert "burn_rate" in data
        assert "runway_months" in data

    def test_get_supplier_risk(self, test_client: TestClient, sample_business_data):
        """Test getting supplier risk analysis."""
        test_client.post("/api/v1/businesses", json=sample_business_data)
        
        response = test_client.get(f"/api/v1/risk/suppliers/{sample_business_data['id']}")
        assert response.status_code == 200
        data = response.json()
        assert "concentration" in data
        assert "supplier_health" in data
