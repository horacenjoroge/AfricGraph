"""Tenant statistics tracking."""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import text

from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.logging import get_logger
from src.tenancy.models import TenantStats

logger = get_logger(__name__)


class TenantStatsCollector:
    """Collects and tracks tenant statistics."""

    def get_tenant_stats(self, tenant_id: str) -> TenantStats:
        """
        Get statistics for a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            TenantStats instance
        """
        # Count nodes
        node_query = """
        MATCH (n)
        WHERE n.tenant_id = $tenant_id
        RETURN count(n) as count
        """
        node_result = neo4j_client.execute_cypher(node_query, {"tenant_id": tenant_id})
        node_count = node_result[0]["count"] if node_result else 0

        # Count relationships
        rel_query = """
        MATCH ()-[r]->()
        WHERE r.tenant_id = $tenant_id
        RETURN count(r) as count
        """
        rel_result = neo4j_client.execute_cypher(rel_query, {"tenant_id": tenant_id})
        rel_count = rel_result[0]["count"] if rel_result else 0

        # Count users (from PostgreSQL)
        user_query = "SELECT COUNT(*) as count FROM users WHERE tenant_id = %(tenant_id)s"
        with postgres_client.get_session() as session:
            result = session.execute(text(user_query), {"tenant_id": tenant_id})
            user_count = result.fetchone()["count"] if result.fetchone() else 0

        # Estimate storage (simplified)
        storage_bytes = (node_count * 1024) + (rel_count * 512)  # Rough estimate

        # Get last activity (from audit logs)
        activity_query = """
        SELECT MAX(timestamp) as last_activity
        FROM audit_logs
        WHERE tenant_id = %(tenant_id)s
        """
        with postgres_client.get_session() as session:
            result = session.execute(text(activity_query), {"tenant_id": tenant_id})
            row = result.fetchone()
            last_activity = row["last_activity"] if row and row["last_activity"] else None

        return TenantStats(
            tenant_id=tenant_id,
            node_count=node_count,
            relationship_count=rel_count,
            user_count=user_count,
            storage_bytes=storage_bytes,
            last_activity=last_activity,
        )

    def update_tenant_stats(self, tenant_id: str) -> TenantStats:
        """Update and return tenant statistics."""
        stats = self.get_tenant_stats(tenant_id)
        # Could store in cache or database for quick access
        return stats
