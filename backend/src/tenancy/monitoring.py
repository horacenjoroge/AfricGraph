"""Monitoring and observability for multi-tenancy."""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import text

from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.logging import get_logger
from src.tenancy.manager import TenantManager

logger = get_logger(__name__)


class TenantMonitoring:
    """Monitor tenant health, performance, and resource usage."""
    
    def __init__(self):
        """Initialize monitoring."""
        self.tenant_manager = TenantManager()
    
    def get_tenant_health(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get health metrics for a specific tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Health metrics dictionary
        """
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return {
                "tenant_id": tenant_id,
                "status": "not_found",
                "healthy": False,
            }
        
        # Get node count
        node_query = """
        MATCH (n)
        WHERE n.tenant_id = $tenant_id
        RETURN count(n) as node_count
        """
        try:
            node_result = neo4j_client.execute_cypher(
                node_query,
                {"tenant_id": tenant_id},
                skip_tenant_filter=True,
            )
            node_count = node_result[0]["node_count"] if node_result else 0
        except Exception as e:
            logger.exception("Failed to get node count", tenant_id=tenant_id, error=str(e))
            node_count = 0
        
        # Get relationship count
        rel_query = """
        MATCH ()-[r]->()
        WHERE r.tenant_id = $tenant_id
        RETURN count(r) as rel_count
        """
        try:
            rel_result = neo4j_client.execute_cypher(
                rel_query,
                {"tenant_id": tenant_id},
                skip_tenant_filter=True,
            )
            rel_count = rel_result[0]["rel_count"] if rel_result else 0
        except Exception as e:
            logger.exception("Failed to get relationship count", tenant_id=tenant_id, error=str(e))
            rel_count = 0
        
        # Determine health status
        is_healthy = (
            tenant.status == "active" and
            node_count >= 0 and  # Basic validation
            rel_count >= 0
        )
        
        return {
            "tenant_id": tenant_id,
            "status": tenant.status,
            "healthy": is_healthy,
            "node_count": node_count,
            "relationship_count": rel_count,
            "created_at": tenant.created_at.isoformat(),
            "last_updated": tenant.updated_at.isoformat(),
        }
    
    def get_tenant_resource_usage(
        self,
        tenant_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get resource usage metrics for a tenant.
        
        Args:
            tenant_id: Tenant ID
            days: Number of days to analyze
            
        Returns:
            Resource usage metrics
        """
        # Query audit logs for tenant activity
        query = """
        SELECT 
            COUNT(*) as operation_count,
            COUNT(DISTINCT DATE(created_at)) as active_days,
            MIN(created_at) as first_activity,
            MAX(created_at) as last_activity
        FROM audit_events
        WHERE resource_id = :tenant_id
        AND created_at >= NOW() - INTERVAL '%s days'
        """
        
        try:
            with postgres_client.get_session() as session:
                result = session.execute(
                    text(query % days),
                    {"tenant_id": tenant_id},
                )
                row = result.fetchone()
                if row:
                    row_dict = row._mapping if hasattr(row, '_mapping') else dict(row)
                    return {
                        "tenant_id": tenant_id,
                        "period_days": days,
                        "operation_count": row_dict.get("operation_count", 0),
                        "active_days": row_dict.get("active_days", 0),
                        "first_activity": row_dict.get("first_activity").isoformat() if row_dict.get("first_activity") else None,
                        "last_activity": row_dict.get("last_activity").isoformat() if row_dict.get("last_activity") else None,
                    }
        except Exception as e:
            logger.exception("Failed to get resource usage", tenant_id=tenant_id, error=str(e))
        
        return {
            "tenant_id": tenant_id,
            "period_days": days,
            "operation_count": 0,
            "active_days": 0,
            "first_activity": None,
            "last_activity": None,
            "error": "Unable to retrieve usage data",
        }
    
    def get_all_tenants_health(self) -> List[Dict[str, Any]]:
        """Get health status for all tenants."""
        tenants = self.tenant_manager.list_tenants(limit=1000)
        health_statuses = []
        
        for tenant in tenants:
            try:
                health = self.get_tenant_health(tenant.tenant_id)
                health_statuses.append(health)
            except Exception as e:
                logger.exception("Failed to get health for tenant", tenant_id=tenant.tenant_id, error=str(e))
                health_statuses.append({
                    "tenant_id": tenant.tenant_id,
                    "status": "error",
                    "healthy": False,
                    "error": str(e),
                })
        
        return health_statuses
    
    def get_performance_metrics(
        self,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get performance metrics for tenant(s).
        
        Args:
            tenant_id: Specific tenant ID, or None for all tenants
            
        Returns:
            Performance metrics
        """
        # This would integrate with query performance monitoring
        # For now, return basic structure
        return {
            "tenant_id": tenant_id,
            "average_query_time_ms": 0,
            "queries_per_minute": 0,
            "cache_hit_rate": 0,
            "index_usage_rate": 0,
        }
