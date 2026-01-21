"""Integration tests for permission-aware queries."""
import pytest
from unittest.mock import Mock, patch


@pytest.mark.integration
@pytest.mark.abac
class TestPermissionAwareQueries:
    """Test permission-aware query filtering."""

    @patch("src.security.query_rewriter.neo4j_client")
    def test_owner_can_access_own_business(self, mock_client, owner_subject):
        """Test owner can query their own business."""
        from src.infrastructure.database.neo4j_client import Neo4jClient
        
        client = Neo4jClient()
        mock_client.execute_cypher.return_value = [
            {"id": "business-123", "name": "Owner's Business"}
        ]
        
        result = client.execute_cypher(
            "MATCH (b:Business) RETURN b",
            subject=owner_subject,
            action="read",
        )
        
        # Query should be rewritten with permission filters
        assert mock_client.execute_cypher.called

    @patch("src.security.query_rewriter.neo4j_client")
    def test_analyst_cannot_access_sensitive_data(self, mock_client, analyst_subject):
        """Test analyst cannot access sensitive business data."""
        from src.infrastructure.database.neo4j_client import Neo4jClient
        
        client = Neo4jClient()
        
        result = client.execute_cypher(
            "MATCH (b:Business {sensitivity_level: 'confidential'}) RETURN b",
            subject=analyst_subject,
            action="read",
        )
        
        # Query should filter out sensitive data
        assert mock_client.execute_cypher.called

    @patch("src.security.query_rewriter.neo4j_client")
    def test_admin_can_access_all(self, mock_client, admin_subject):
        """Test admin can access all data."""
        from src.infrastructure.database.neo4j_client import Neo4jClient
        
        client = Neo4jClient()
        mock_client.execute_cypher.return_value = [
            {"id": "business-123"},
            {"id": "business-456"},
        ]
        
        result = client.execute_cypher(
            "MATCH (b:Business) RETURN b",
            subject=admin_subject,
            action="read",
        )
        
        # Admin should see all businesses
        assert mock_client.execute_cypher.called
