"""Cross-tenant analytics (aggregated, no individual tenant data)."""
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import text

from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.logging import get_logger
from src.tenancy.context import get_current_tenant

logger = get_logger(__name__)


class CrossTenantAnalytics:
    """Aggregated analytics across all tenants (no individual tenant data)."""

    def get_aggregated_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get aggregated statistics across all tenants.

        Returns aggregated data only - no individual tenant information.
        """
        # Get tenant count
        query = "SELECT COUNT(*) as count FROM tenants WHERE status = 'active'"
        with postgres_client.get_session() as session:
            result = session.execute(text(query))
            tenant_count = result.fetchone()["count"]

        # Get aggregated node count (from Neo4j)
        # This is a simplified approach - in production, you'd maintain aggregated stats
        node_query = """
        MATCH (n)
        WHERE n.tenant_id IS NOT NULL
        RETURN count(n) as total_nodes
        """
        node_result = neo4j_client.execute_cypher(node_query)
        total_nodes = node_result[0]["total_nodes"] if node_result else 0

        # Get aggregated relationship count
        rel_query = """
        MATCH ()-[r]->()
        WHERE r.tenant_id IS NOT NULL
        RETURN count(r) as total_relationships
        """
        rel_result = neo4j_client.execute_cypher(rel_query)
        total_relationships = rel_result[0]["total_relationships"] if rel_result else 0

        # Get node distribution by label
        label_query = """
        MATCH (n)
        WHERE n.tenant_id IS NOT NULL
        UNWIND labels(n) as label
        WITH label, count(n) as count
        ORDER BY count DESC
        RETURN collect({label: label, count: count}) as distribution
        """
        try:
            label_result = neo4j_client.execute_cypher(label_query, skip_tenant_filter=True)
            label_distribution = label_result[0]["distribution"] if label_result else []
        except Exception as e:
            logger.exception("Failed to get label distribution", error=str(e))
            label_distribution = []

        return {
            "tenant_count": tenant_count,
            "total_nodes": total_nodes,
            "total_relationships": total_relationships,
            "average_nodes_per_tenant": total_nodes / tenant_count if tenant_count > 0 else 0,
            "average_relationships_per_tenant": total_relationships / tenant_count if tenant_count > 0 else 0,
            "node_distribution_by_label": label_distribution,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
        }

    def get_tenant_distribution(
        self,
        metric: str = "nodes",
    ) -> Dict[str, Any]:
        """
        Get distribution of tenants by metric.

        Returns aggregated buckets, not individual tenant data.
        """
        if metric == "nodes":
            query = """
            MATCH (n)
            WHERE n.tenant_id IS NOT NULL
            WITH n.tenant_id as tenant_id, count(n) as node_count
            RETURN 
                CASE 
                    WHEN node_count <= 100 THEN '0-100'
                    WHEN node_count <= 500 THEN '101-500'
                    WHEN node_count <= 1000 THEN '501-1000'
                    ELSE '1000+'
                END as bucket,
                count(tenant_id) as tenant_count
            ORDER BY 
                CASE bucket
                    WHEN '0-100' THEN 1
                    WHEN '101-500' THEN 2
                    WHEN '501-1000' THEN 3
                    ELSE 4
                END
            """
        elif metric == "relationships":
            query = """
            MATCH ()-[r]->()
            WHERE r.tenant_id IS NOT NULL
            WITH r.tenant_id as tenant_id, count(r) as rel_count
            RETURN 
                CASE 
                    WHEN rel_count <= 100 THEN '0-100'
                    WHEN rel_count <= 500 THEN '101-500'
                    WHEN rel_count <= 1000 THEN '501-1000'
                    ELSE '1000+'
                END as bucket,
                count(tenant_id) as tenant_count
            ORDER BY 
                CASE bucket
                    WHEN '0-100' THEN 1
                    WHEN '101-500' THEN 2
                    WHEN '501-1000' THEN 3
                    ELSE 4
                END
            """
        else:
            # Default to nodes
            query = """
            MATCH (n)
            WHERE n.tenant_id IS NOT NULL
            WITH n.tenant_id as tenant_id, count(n) as node_count
            RETURN 
                CASE 
                    WHEN node_count <= 100 THEN '0-100'
                    WHEN node_count <= 500 THEN '101-500'
                    WHEN node_count <= 1000 THEN '501-1000'
                    ELSE '1000+'
                END as bucket,
                count(tenant_id) as tenant_count
            ORDER BY 
                CASE bucket
                    WHEN '0-100' THEN 1
                    WHEN '101-500' THEN 2
                    WHEN '501-1000' THEN 3
                    ELSE 4
                END
            """
        
        try:
            result = neo4j_client.execute_cypher(query, skip_tenant_filter=True)
            buckets = [
                {
                    "range": row.get("bucket", "unknown"),
                    "count": row.get("tenant_count", 0),
                }
                for row in result
            ]
            
            # Ensure all buckets are present
            bucket_ranges = ["0-100", "101-500", "501-1000", "1000+"]
            existing_ranges = {b["range"] for b in buckets}
            for range_val in bucket_ranges:
                if range_val not in existing_ranges:
                    buckets.append({"range": range_val, "count": 0})
            
            buckets.sort(key=lambda x: bucket_ranges.index(x["range"]))
            
            return {
                "metric": metric,
                "buckets": buckets,
            }
        except Exception as e:
            logger.exception("Failed to get tenant distribution", error=str(e))
            return {
                "metric": metric,
                "buckets": [
                    {"range": "0-100", "count": 0},
                    {"range": "101-500", "count": 0},
                    {"range": "501-1000", "count": 0},
                    {"range": "1000+", "count": 0},
                ],
                "error": str(e),
            }

    def get_activity_summary(
        self,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get aggregated activity summary across all tenants."""
        try:
            # Query audit logs for aggregated activity
            query = """
            SELECT 
                event_type,
                COUNT(*) as count,
                DATE(created_at) as activity_date
            FROM audit_events
            WHERE created_at >= NOW() - INTERVAL '%s days'
            GROUP BY event_type, DATE(created_at)
            ORDER BY activity_date DESC, count DESC
            """
            
            with postgres_client.get_session() as session:
                result = session.execute(text(query % days))
                rows = [dict(row._mapping if hasattr(row, '_mapping') else row) for row in result]
            
            # Aggregate operations by type
            operations_by_type = {}
            daily_activity = {}
            total_operations = 0
            
            for row in rows:
                event_type = row.get("event_type", "unknown")
                count = row.get("count", 0)
                activity_date = row.get("activity_date")
                
                operations_by_type[event_type] = operations_by_type.get(event_type, 0) + count
                daily_activity[activity_date] = daily_activity.get(activity_date, 0) + count
                total_operations += count
            
            # Find peak activity day
            peak_activity_day = None
            peak_count = 0
            for date, count in daily_activity.items():
                if count > peak_count:
                    peak_count = count
                    peak_activity_day = date.isoformat() if hasattr(date, 'isoformat') else str(date)
            
            return {
                "period_days": days,
                "total_operations": total_operations,
                "operations_by_type": operations_by_type,
                "peak_activity_day": peak_activity_day,
                "peak_activity_count": peak_count,
                "average_operations_per_day": total_operations / days if days > 0 else 0,
            }
        except Exception as e:
            logger.exception("Failed to get activity summary", error=str(e))
            # Fallback if audit table doesn't exist or query fails
            return {
                "period_days": days,
                "total_operations": 0,
                "operations_by_type": {},
                "peak_activity_day": None,
                "error": str(e),
            }
