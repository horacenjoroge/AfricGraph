"""E2E tests for critical user journeys."""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.e2e
@pytest.mark.slow
class TestBusinessOnboardingJourney:
    """Test complete business onboarding journey."""

    def test_business_onboarding_flow(self, test_client: TestClient):
        """Test full business onboarding flow."""
        # 1. Create business
        business_data = {
            "id": "e2e-business-1",
            "name": "E2E Test Business",
            "registration_number": "E2E-123",
            "sector": "Technology",
        }
        create_response = test_client.post(
            "/api/v1/businesses",
            json=business_data,
        )
        assert create_response.status_code in [200, 201]
        business_id = business_data["id"]

        # 2. Get risk assessment
        risk_response = test_client.get(f"/api/v1/risk/{business_id}")
        assert risk_response.status_code == 200

        # 3. Run fraud scan
        fraud_response = test_client.post(f"/api/v1/fraud/business/{business_id}/scan")
        assert fraud_response.status_code == 200

        # 4. Get business graph
        graph_response = test_client.get(f"/api/v1/businesses/{business_id}/graph")
        assert graph_response.status_code == 200

        # 5. Search for business
        search_response = test_client.get("/api/v1/businesses/search?query=E2E")
        assert search_response.status_code == 200


@pytest.mark.e2e
@pytest.mark.slow
class TestRiskAnalysisJourney:
    """Test risk analysis journey."""

    def test_complete_risk_analysis(self, test_client: TestClient):
        """Test complete risk analysis workflow."""
        # Create business
        business_data = {
            "id": "e2e-risk-1",
            "name": "Risk Analysis Business",
            "registration_number": "RISK-123",
        }
        test_client.post("/api/v1/businesses", json=business_data)
        business_id = business_data["id"]

        # Get risk score
        risk_response = test_client.get(f"/api/v1/risk/{business_id}")
        assert risk_response.status_code == 200
        risk_data = risk_response.json()
        assert "composite_score" in risk_data or "total_score" in risk_data

        # Get cash flow health
        cashflow_response = test_client.get(f"/api/v1/risk/cashflow/{business_id}")
        assert cashflow_response.status_code == 200

        # Get supplier risk
        supplier_response = test_client.get(f"/api/v1/risk/suppliers/{business_id}")
        assert supplier_response.status_code == 200


@pytest.mark.e2e
@pytest.mark.slow
class TestFraudDetectionJourney:
    """Test fraud detection journey."""

    def test_fraud_detection_workflow(self, test_client: TestClient):
        """Test complete fraud detection workflow."""
        # Create business
        business_data = {
            "id": "e2e-fraud-1",
            "name": "Fraud Test Business",
            "registration_number": "FRAUD-123",
        }
        test_client.post("/api/v1/businesses", json=business_data)
        business_id = business_data["id"]

        # Run fraud scan
        scan_response = test_client.post(f"/api/v1/fraud/business/{business_id}/scan")
        assert scan_response.status_code == 200
        scan_data = scan_response.json()
        assert "patterns" in scan_data

        # List fraud alerts
        alerts_response = test_client.get("/api/v1/fraud/alerts")
        assert alerts_response.status_code == 200


@pytest.mark.e2e
@pytest.mark.slow
class TestGraphExplorationJourney:
    """Test graph exploration journey."""

    def test_graph_exploration_workflow(self, test_client: TestClient):
        """Test graph exploration workflow."""
        # Create multiple businesses
        business1 = {"id": "e2e-graph-1", "name": "Graph Business 1"}
        business2 = {"id": "e2e-graph-2", "name": "Graph Business 2"}
        
        test_client.post("/api/v1/businesses", json=business1)
        test_client.post("/api/v1/businesses", json=business2)

        # Get subgraph
        graph_response = test_client.get(f"/api/v1/businesses/{business1['id']}/graph")
        assert graph_response.status_code == 200

        # Find relationships
        rel_response = test_client.get(
            f"/api/v1/relationships/connect/{business1['id']}/{business2['id']}"
        )
        assert rel_response.status_code in [200, 404]  # 404 if no connection
