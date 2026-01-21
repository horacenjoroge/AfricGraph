"""Integration tests for business API endpoints."""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.api
class TestBusinessAPI:
    """Test business API endpoints."""

    def test_create_business(self, test_client: TestClient, sample_business_data):
        """Test creating a business."""
        response = test_client.post(
            "/api/v1/businesses",
            json=sample_business_data,
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["id"] == sample_business_data["id"]
        assert data["name"] == sample_business_data["name"]

    def test_get_business(self, test_client: TestClient, sample_business_data):
        """Test getting a business by ID."""
        # First create
        test_client.post("/api/v1/businesses", json=sample_business_data)
        
        # Then get
        response = test_client.get(f"/api/v1/businesses/{sample_business_data['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_business_data["id"]

    def test_get_business_not_found(self, test_client: TestClient):
        """Test getting non-existent business."""
        response = test_client.get("/api/v1/businesses/non-existent")
        assert response.status_code == 404

    def test_search_businesses(self, test_client: TestClient, sample_business_data):
        """Test searching businesses."""
        # Create a business
        test_client.post("/api/v1/businesses", json=sample_business_data)
        
        # Search
        response = test_client.get("/api/v1/businesses/search?query=Test")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)

    def test_update_business(self, test_client: TestClient, sample_business_data):
        """Test updating a business."""
        # Create
        test_client.post("/api/v1/businesses", json=sample_business_data)
        
        # Update
        update_data = {"name": "Updated Business Name"}
        response = test_client.put(
            f"/api/v1/businesses/{sample_business_data['id']}",
            json=update_data,
        )
        assert response.status_code in [200, 204]
        
        # Verify
        get_response = test_client.get(f"/api/v1/businesses/{sample_business_data['id']}")
        assert get_response.status_code == 200
        updated = get_response.json()
        assert updated["name"] == "Updated Business Name"


@pytest.mark.integration
@pytest.mark.api
class TestBusinessGraphAPI:
    """Test business graph API endpoints."""

    def test_get_business_graph(self, test_client: TestClient, sample_business_data):
        """Test getting business subgraph."""
        # Create business
        test_client.post("/api/v1/businesses", json=sample_business_data)
        
        # Get graph
        response = test_client.get(
            f"/api/v1/businesses/{sample_business_data['id']}/graph?max_hops=2"
        )
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "relationships" in data
