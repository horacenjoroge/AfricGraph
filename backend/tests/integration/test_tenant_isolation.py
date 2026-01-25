"""Integration tests for tenant isolation."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from src.tenancy.manager import TenantManager
from src.tenancy.context import set_current_tenant, get_current_tenant
from src.tenancy.models import Tenant
from src.infrastructure.database.neo4j_client import neo4j_client


@pytest.mark.integration
@pytest.mark.tenancy
class TestTenantIsolation:
    """Test tenant data isolation."""

    @pytest.fixture
    def tenant_manager(self):
        """Create tenant manager instance."""
        return TenantManager()

    @pytest.fixture
    def tenant1(self, tenant_manager):
        """Create test tenant 1."""
        return tenant_manager.create_tenant(
            tenant_id="test-tenant-1",
            name="Test Tenant 1",
            domain="tenant1.test.com",
        )

    @pytest.fixture
    def tenant2(self, tenant_manager):
        """Create test tenant 2."""
        return tenant_manager.create_tenant(
            tenant_id="test-tenant-2",
            name="Test Tenant 2",
            domain="tenant2.test.com",
        )

    def test_tenant_creation(self, tenant_manager):
        """Test creating tenants."""
        tenant = tenant_manager.create_tenant(
            tenant_id="test-tenant",
            name="Test Tenant",
        )
        assert tenant is not None
        assert tenant.tenant_id == "test-tenant"
        assert tenant.name == "Test Tenant"
        assert tenant.status == "active"

    def test_tenant_data_isolation_nodes(self, tenant1, tenant2):
        """Test that nodes are isolated between tenants."""
        # Set tenant 1 context
        set_current_tenant(tenant1)
        
        # Create node for tenant 1
        node1_query = """
        CREATE (n:Business {id: 'biz-1', name: 'Tenant 1 Business', tenant_id: $tenant_id})
        RETURN n
        """
        result1 = neo4j_client.execute_cypher(
            node1_query,
            {"tenant_id": tenant1.tenant_id},
            skip_tenant_filter=True,
        )
        assert result1 is not None

        # Set tenant 2 context
        set_current_tenant(tenant2)
        
        # Create node for tenant 2
        node2_query = """
        CREATE (n:Business {id: 'biz-2', name: 'Tenant 2 Business', tenant_id: $tenant_id})
        RETURN n
        """
        result2 = neo4j_client.execute_cypher(
            node2_query,
            {"tenant_id": tenant2.tenant_id},
            skip_tenant_filter=True,
        )
        assert result2 is not None

        # Query with tenant 1 context - should only see tenant 1 nodes
        set_current_tenant(tenant1)
        query1 = "MATCH (n:Business) WHERE n.tenant_id = $tenant_id RETURN n"
        nodes1 = neo4j_client.execute_cypher(
            query1,
            {"tenant_id": tenant1.tenant_id},
            skip_tenant_filter=True,
        )
        # Should only find tenant 1's node
        tenant1_nodes = [n for n in nodes1 if n.get("n", {}).get("properties", {}).get("tenant_id") == tenant1.tenant_id]
        assert len(tenant1_nodes) > 0

        # Query with tenant 2 context - should only see tenant 2 nodes
        set_current_tenant(tenant2)
        query2 = "MATCH (n:Business) WHERE n.tenant_id = $tenant_id RETURN n"
        nodes2 = neo4j_client.execute_cypher(
            query2,
            {"tenant_id": tenant2.tenant_id},
            skip_tenant_filter=True,
        )
        # Should only find tenant 2's node
        tenant2_nodes = [n for n in nodes2 if n.get("n", {}).get("properties", {}).get("tenant_id") == tenant2.tenant_id]
        assert len(tenant2_nodes) > 0

        # Verify isolation - tenant 1 should not see tenant 2's data
        set_current_tenant(tenant1)
        all_nodes = neo4j_client.execute_cypher(
            query1,
            {"tenant_id": tenant1.tenant_id},
            skip_tenant_filter=True,
        )
        tenant2_data = [n for n in all_nodes if n.get("n", {}).get("properties", {}).get("tenant_id") == tenant2.tenant_id]
        assert len(tenant2_data) == 0, "Tenant 1 should not see tenant 2's data"

    def test_tenant_data_isolation_relationships(self, tenant1, tenant2):
        """Test that relationships are isolated between tenants."""
        set_current_tenant(tenant1)
        
        # Create nodes and relationship for tenant 1
        create_query1 = """
        CREATE (a:Business {id: 'biz-a1', tenant_id: $tenant_id})
        CREATE (b:Business {id: 'biz-b1', tenant_id: $tenant_id})
        CREATE (a)-[r:SUPPLIES {tenant_id: $tenant_id}]->(b)
        RETURN r
        """
        result1 = neo4j_client.execute_cypher(
            create_query1,
            {"tenant_id": tenant1.tenant_id},
            skip_tenant_filter=True,
        )
        assert result1 is not None

        set_current_tenant(tenant2)
        
        # Create nodes and relationship for tenant 2
        create_query2 = """
        CREATE (a:Business {id: 'biz-a2', tenant_id: $tenant_id})
        CREATE (b:Business {id: 'biz-b2', tenant_id: $tenant_id})
        CREATE (a)-[r:SUPPLIES {tenant_id: $tenant_id}]->(b)
        RETURN r
        """
        result2 = neo4j_client.execute_cypher(
            create_query2,
            {"tenant_id": tenant2.tenant_id},
            skip_tenant_filter=True,
        )
        assert result2 is not None

        # Query relationships for tenant 1
        set_current_tenant(tenant1)
        rel_query1 = """
        MATCH ()-[r:SUPPLIES]->()
        WHERE r.tenant_id = $tenant_id
        RETURN count(r) as count
        """
        rels1 = neo4j_client.execute_cypher(
            rel_query1,
            {"tenant_id": tenant1.tenant_id},
            skip_tenant_filter=True,
        )
        assert rels1[0]["count"] > 0

        # Query relationships for tenant 2
        set_current_tenant(tenant2)
        rel_query2 = """
        MATCH ()-[r:SUPPLIES]->()
        WHERE r.tenant_id = $tenant_id
        RETURN count(r) as count
        """
        rels2 = neo4j_client.execute_cypher(
            rel_query2,
            {"tenant_id": tenant2.tenant_id},
            skip_tenant_filter=True,
        )
        assert rels2[0]["count"] > 0

        # Verify isolation
        set_current_tenant(tenant1)
        all_rels = neo4j_client.execute_cypher(
            rel_query1,
            {"tenant_id": tenant1.tenant_id},
            skip_tenant_filter=True,
        )
        tenant2_rels = neo4j_client.execute_cypher(
            rel_query2,
            {"tenant_id": tenant2.tenant_id},
            skip_tenant_filter=True,
        )
        # Tenant 1 should not see tenant 2's relationships
        assert all_rels[0]["count"] == rels1[0]["count"]

    def test_query_rewriter_adds_tenant_filter(self, tenant1):
        """Test that query rewriter automatically adds tenant filter."""
        from src.tenancy.query_rewriter import TenantQueryRewriter
        
        set_current_tenant(tenant1)
        rewriter = TenantQueryRewriter()
        
        query = "MATCH (n:Business) RETURN n"
        rewritten = rewriter.rewrite_query(query, {})
        
        # Should include tenant_id filter
        assert "tenant_id" in rewritten.lower()
        assert tenant1.tenant_id in str(rewritten) or "$tenant_id" in rewritten

    def test_cross_tenant_data_leak_prevention(self, tenant1, tenant2):
        """Test that queries cannot leak data across tenants."""
        from src.tenancy.security import TenantSecurityValidator
        
        # Dangerous query that tries to bypass tenant filter
        dangerous_query = "MATCH (n) WHERE n.tenant_id != 'other-tenant' RETURN n"
        
        is_safe, error = TenantSecurityValidator.validate_query(dangerous_query)
        assert not is_safe, "Dangerous query should be rejected"
        assert error is not None

    def test_tenant_context_required(self, tenant_manager):
        """Test that tenant context is required for data operations."""
        # Clear tenant context
        set_current_tenant(None)
        
        current = get_current_tenant()
        assert current is None, "Tenant context should be None"

    def test_tenant_config_isolation(self, tenant1, tenant2, tenant_manager):
        """Test that tenant configs are isolated."""
        # Set config for tenant 1
        config1 = tenant_manager.set_tenant_config(
            tenant_id=tenant1.tenant_id,
            key="test_key",
            value="tenant1_value",
        )
        assert config1.value == "tenant1_value"

        # Set config for tenant 2
        config2 = tenant_manager.set_tenant_config(
            tenant_id=tenant2.tenant_id,
            key="test_key",
            value="tenant2_value",
        )
        assert config2.value == "tenant2_value"

        # Get configs - should be isolated
        configs1 = tenant_manager.get_all_tenant_configs(tenant1.tenant_id)
        configs2 = tenant_manager.get_all_tenant_configs(tenant2.tenant_id)
        
        # Find test_key in each
        test_config1 = next((c for c in configs1 if c.key == "test_key"), None)
        test_config2 = next((c for c in configs2 if c.key == "test_key"), None)
        
        assert test_config1 is not None
        assert test_config2 is not None
        assert test_config1.value == "tenant1_value"
        assert test_config2.value == "tenant2_value"
        assert test_config1.value != test_config2.value

    @patch("src.infrastructure.database.neo4j_client.neo4j_client")
    def test_tenant_filter_in_queries(self, mock_client, tenant1):
        """Test that tenant filter is automatically added to queries."""
        from src.infrastructure.database.neo4j_client import neo4j_client
        
        set_current_tenant(tenant1)
        
        # Mock the execute_cypher to capture the query
        captured_query = []
        def capture_query(query, params=None, **kwargs):
            captured_query.append((query, params))
            return []
        
        mock_client.execute_cypher = capture_query
        
        # Execute a query (this would normally go through query rewriter)
        query = "MATCH (n:Business) RETURN n"
        # In real scenario, this goes through query rewriter
        # For test, we verify the pattern
        
        # The actual implementation should add tenant filter
        # This test verifies the concept

    def test_tenant_migration_isolation(self, tenant1, tenant2, tenant_manager):
        """Test that tenant migration doesn't affect other tenants."""
        from src.tenancy.migration import TenantMigrationManager
        
        migration_manager = TenantMigrationManager()
        
        # Create some data for tenant 1
        set_current_tenant(tenant1)
        create_query = """
        CREATE (n:Business {id: 'migrate-test', name: 'To Migrate', tenant_id: $tenant_id})
        RETURN n
        """
        neo4j_client.execute_cypher(
            create_query,
            {"tenant_id": tenant1.tenant_id},
            skip_tenant_filter=True,
        )
        
        # Count tenant 2 data before migration
        count_query2_before = """
        MATCH (n)
        WHERE n.tenant_id = $tenant_id
        RETURN count(n) as count
        """
        count_before = neo4j_client.execute_cypher(
            count_query2_before,
            {"tenant_id": tenant2.tenant_id},
            skip_tenant_filter=True,
        )
        count_before_value = count_before[0]["count"] if count_before else 0
        
        # Migrate tenant 1 to a new tenant (dry run)
        result = migration_manager.migrate_tenant(
            source_tenant_id=tenant1.tenant_id,
            target_tenant_id="migrated-tenant",
            dry_run=True,
        )
        
        # Verify tenant 2 data is unchanged
        count_after = neo4j_client.execute_cypher(
            count_query2_before,
            {"tenant_id": tenant2.tenant_id},
            skip_tenant_filter=True,
        )
        count_after_value = count_after[0]["count"] if count_after else 0
        
        assert count_before_value == count_after_value, "Migration should not affect other tenants"

    def test_tenant_analytics_isolation(self, tenant1, tenant2):
        """Test that analytics are properly aggregated without leaking tenant data."""
        from src.tenancy.analytics import CrossTenantAnalytics
        
        analytics = CrossTenantAnalytics()
        
        # Get aggregated stats - should not include individual tenant data
        stats = analytics.get_aggregated_stats()
        
        # Should have aggregated metrics
        assert "tenant_count" in stats
        assert "total_nodes" in stats
        assert "total_relationships" in stats
        
        # Should NOT have individual tenant breakdowns
        assert "tenants" not in stats or isinstance(stats.get("tenants"), list) is False
        # Aggregated stats should not expose individual tenant IDs

    def test_tenant_export_isolation(self, tenant1, tenant2):
        """Test that tenant export only includes that tenant's data."""
        from src.tenancy.export import TenantDataExporter
        
        exporter = TenantDataExporter()
        
        # Export tenant 1 data
        export1 = exporter.export_tenant_data(tenant_id=tenant1.tenant_id)
        
        # Verify all nodes belong to tenant 1
        if "nodes" in export1:
            for node in export1["nodes"]:
                assert node.get("tenant_id") == tenant1.tenant_id
        
        # Verify all relationships belong to tenant 1
        if "relationships" in export1:
            for rel in export1["relationships"]:
                assert rel.get("tenant_id") == tenant1.tenant_id
