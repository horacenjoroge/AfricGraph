"""Locust load testing for AfricGraph API."""
from locust import HttpUser, task, between
import random


class AfricGraphUser(HttpUser):
    """Simulated user for load testing."""
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Setup before user starts."""
        # Login or get auth token
        self.business_ids = []
        self.auth_token = None
        
        # Try to authenticate
        response = self.client.post(
            "/api/auth/login",
            json={
                "username": "test_user",
                "password": "test_password",
            },
        )
        if response.status_code == 200:
            self.auth_token = response.json().get("access_token")
            self.client.headers.update({
                "Authorization": f"Bearer {self.auth_token}"
            })

    @task(3)
    def get_businesses(self):
        """Search businesses (high frequency)."""
        self.client.get("/api/v1/businesses/search?query=test")

    @task(2)
    def get_business_detail(self):
        """Get business details."""
        if self.business_ids:
            business_id = random.choice(self.business_ids)
            self.client.get(f"/api/v1/businesses/{business_id}")

    @task(2)
    def get_risk_assessment(self):
        """Get risk assessment."""
        if self.business_ids:
            business_id = random.choice(self.business_ids)
            self.client.get(f"/api/v1/risk/{business_id}")

    @task(1)
    def get_graph(self):
        """Get business graph."""
        if self.business_ids:
            business_id = random.choice(self.business_ids)
            self.client.get(f"/api/v1/businesses/{business_id}/graph?max_hops=2")

    @task(1)
    def search_relationships(self):
        """Search relationships."""
        if len(self.business_ids) >= 2:
            entity_a = random.choice(self.business_ids)
            entity_b = random.choice(self.business_ids)
            if entity_a != entity_b:
                self.client.get(
                    f"/api/v1/relationships/connect/{entity_a}/{entity_b}"
                )

    @task(1)
    def get_fraud_alerts(self):
        """Get fraud alerts."""
        self.client.get("/api/v1/fraud/alerts")

    @task(1)
    def health_check(self):
        """Health check endpoint."""
        self.client.get("/health")


class HighLoadUser(HttpUser):
    """User for high-load testing."""
    wait_time = between(0.1, 0.5)  # Very short wait time
    
    @task(10)
    def rapid_requests(self):
        """Rapid fire requests."""
        self.client.get("/api/v1/businesses/search?query=load")
        self.client.get("/health")
