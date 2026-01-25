"""Tenant resource quotas and limits."""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.logging import get_logger
from src.tenancy.manager import TenantManager
from src.tenancy.context import get_current_tenant

logger = get_logger(__name__)


class QuotaType(str, Enum):
    """Types of resource quotas."""
    NODES = "nodes"
    RELATIONSHIPS = "relationships"
    STORAGE_MB = "storage_mb"
    API_REQUESTS_PER_DAY = "api_requests_per_day"
    API_REQUESTS_PER_HOUR = "api_requests_per_hour"
    EXPORTS_PER_MONTH = "exports_per_month"
    MIGRATIONS_PER_MONTH = "migrations_per_month"


@dataclass
class Quota:
    """Resource quota definition."""
    quota_type: QuotaType
    limit: int
    current_usage: int = 0
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    
    @property
    def remaining(self) -> int:
        """Calculate remaining quota."""
        return max(0, self.limit - self.current_usage)
    
    @property
    def usage_percentage(self) -> float:
        """Calculate usage percentage."""
        if self.limit == 0:
            return 0.0
        return (self.current_usage / self.limit) * 100
    
    @property
    def is_exceeded(self) -> bool:
        """Check if quota is exceeded."""
        return self.current_usage >= self.limit


class TenantQuotaManager:
    """Manage resource quotas for tenants."""
    
    def __init__(self):
        """Initialize quota manager."""
        self.tenant_manager = TenantManager()
        # Default quotas (can be overridden per tenant)
        self.default_quotas = {
            QuotaType.NODES: 100000,
            QuotaType.RELATIONSHIPS: 500000,
            QuotaType.STORAGE_MB: 10240,  # 10GB
            QuotaType.API_REQUESTS_PER_DAY: 100000,
            QuotaType.API_REQUESTS_PER_HOUR: 10000,
            QuotaType.EXPORTS_PER_MONTH: 10,
            QuotaType.MIGRATIONS_PER_MONTH: 2,
        }
    
    def get_tenant_quota(
        self,
        tenant_id: str,
        quota_type: QuotaType,
    ) -> Quota:
        """
        Get quota for a tenant.
        
        Args:
            tenant_id: Tenant ID
            quota_type: Type of quota
            
        Returns:
            Quota object with current usage
        """
        # Get tenant-specific quota limit from config
        tenant_configs = self.tenant_manager.get_all_tenant_configs(tenant_id)
        quota_key = f"quota_{quota_type.value}"
        
        limit = self.default_quotas.get(quota_type, 0)
        for config in tenant_configs:
            if config.key == quota_key:
                try:
                    limit = int(config.value)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid quota value for {quota_key}", tenant_id=tenant_id)
        
        # Get current usage
        current_usage = self._get_current_usage(tenant_id, quota_type)
        
        # Calculate period for time-based quotas
        period_start, period_end = self._get_period(quota_type)
        
        return Quota(
            quota_type=quota_type,
            limit=limit,
            current_usage=current_usage,
            period_start=period_start,
            period_end=period_end,
        )
    
    def get_all_quotas(self, tenant_id: str) -> Dict[QuotaType, Quota]:
        """Get all quotas for a tenant."""
        quotas = {}
        for quota_type in QuotaType:
            quotas[quota_type] = self.get_tenant_quota(tenant_id, quota_type)
        return quotas
    
    def check_quota(
        self,
        tenant_id: str,
        quota_type: QuotaType,
        requested_amount: int = 1,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if tenant has quota available.
        
        Args:
            tenant_id: Tenant ID
            quota_type: Type of quota
            requested_amount: Amount requested
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        quota = self.get_tenant_quota(tenant_id, quota_type)
        
        if quota.current_usage + requested_amount > quota.limit:
            return False, f"Quota exceeded for {quota_type.value}. Limit: {quota.limit}, Current: {quota.current_usage}, Requested: {requested_amount}"
        
        return True, None
    
    def record_usage(
        self,
        tenant_id: str,
        quota_type: QuotaType,
        amount: int = 1,
    ) -> None:
        """
        Record quota usage.
        
        Args:
            tenant_id: Tenant ID
            quota_type: Type of quota
            amount: Amount used
        """
        # For time-based quotas, track in database
        if quota_type in [QuotaType.API_REQUESTS_PER_DAY, QuotaType.API_REQUESTS_PER_HOUR]:
            self._record_time_based_usage(tenant_id, quota_type, amount)
        else:
            # For persistent quotas (nodes, relationships), usage is calculated on-demand
            logger.debug(f"Usage recorded for {quota_type.value}", tenant_id=tenant_id, amount=amount)
    
    def set_quota_limit(
        self,
        tenant_id: str,
        quota_type: QuotaType,
        limit: int,
    ) -> None:
        """
        Set quota limit for a tenant.
        
        Args:
            tenant_id: Tenant ID
            quota_type: Type of quota
            limit: New limit
        """
        self.tenant_manager.set_tenant_config(
            tenant_id=tenant_id,
            key=f"quota_{quota_type.value}",
            value=str(limit),
            description=f"Quota limit for {quota_type.value}",
        )
        logger.info(f"Quota limit set", tenant_id=tenant_id, quota_type=quota_type.value, limit=limit)
    
    def _get_current_usage(self, tenant_id: str, quota_type: QuotaType) -> int:
        """Get current usage for a quota type."""
        if quota_type == QuotaType.NODES:
            return self._count_nodes(tenant_id)
        elif quota_type == QuotaType.RELATIONSHIPS:
            return self._count_relationships(tenant_id)
        elif quota_type == QuotaType.STORAGE_MB:
            return self._estimate_storage_mb(tenant_id)
        elif quota_type in [QuotaType.API_REQUESTS_PER_DAY, QuotaType.API_REQUESTS_PER_HOUR]:
            return self._count_api_requests(tenant_id, quota_type)
        elif quota_type == QuotaType.EXPORTS_PER_MONTH:
            return self._count_exports(tenant_id)
        elif quota_type == QuotaType.MIGRATIONS_PER_MONTH:
            return self._count_migrations(tenant_id)
        else:
            return 0
    
    def _count_nodes(self, tenant_id: str) -> int:
        """Count nodes for a tenant."""
        query = """
        MATCH (n)
        WHERE n.tenant_id = $tenant_id
        RETURN count(n) as count
        """
        try:
            result = neo4j_client.execute_cypher(
                query,
                {"tenant_id": tenant_id},
                skip_tenant_filter=True,
            )
            return result[0]["count"] if result else 0
        except Exception as e:
            logger.exception("Failed to count nodes", tenant_id=tenant_id, error=str(e))
            return 0
    
    def _count_relationships(self, tenant_id: str) -> int:
        """Count relationships for a tenant."""
        query = """
        MATCH ()-[r]->()
        WHERE r.tenant_id = $tenant_id
        RETURN count(r) as count
        """
        try:
            result = neo4j_client.execute_cypher(
                query,
                {"tenant_id": tenant_id},
                skip_tenant_filter=True,
            )
            return result[0]["count"] if result else 0
        except Exception as e:
            logger.exception("Failed to count relationships", tenant_id=tenant_id, error=str(e))
            return 0
    
    def _estimate_storage_mb(self, tenant_id: str) -> int:
        """Estimate storage usage in MB (rough estimate)."""
        # Rough estimate: average node size ~1KB, relationship ~0.5KB
        nodes = self._count_nodes(tenant_id)
        relationships = self._count_relationships(tenant_id)
        estimated_bytes = (nodes * 1024) + (relationships * 512)
        return int(estimated_bytes / (1024 * 1024))  # Convert to MB
    
    def _count_api_requests(self, tenant_id: str, quota_type: QuotaType) -> int:
        """Count API requests for time period."""
        from sqlalchemy import text
        
        if quota_type == QuotaType.API_REQUESTS_PER_DAY:
            period_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        elif quota_type == QuotaType.API_REQUESTS_PER_HOUR:
            period_start = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        else:
            return 0
        
        query = """
        SELECT COUNT(*) as count
        FROM audit_events
        WHERE resource_id = :tenant_id
        AND event_type = 'api_request'
        AND created_at >= :period_start
        """
        
        try:
            with postgres_client.get_session() as session:
                result = session.execute(
                    text(query),
                    {
                        "tenant_id": tenant_id,
                        "period_start": period_start,
                    },
                )
                row = result.fetchone()
                return row[0] if row else 0
        except Exception as e:
            logger.exception("Failed to count API requests", tenant_id=tenant_id, error=str(e))
            return 0
    
    def _count_exports(self, tenant_id: str) -> int:
        """Count exports this month."""
        from sqlalchemy import text
        
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        query = """
        SELECT COUNT(*) as count
        FROM audit_events
        WHERE resource_id = :tenant_id
        AND event_type = 'tenant_export'
        AND created_at >= :month_start
        """
        
        try:
            with postgres_client.get_session() as session:
                result = session.execute(
                    text(query),
                    {
                        "tenant_id": tenant_id,
                        "month_start": month_start,
                    },
                )
                row = result.fetchone()
                return row[0] if row else 0
        except Exception as e:
            logger.exception("Failed to count exports", tenant_id=tenant_id, error=str(e))
            return 0
    
    def _count_migrations(self, tenant_id: str) -> int:
        """Count migrations this month."""
        from sqlalchemy import text
        
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        query = """
        SELECT COUNT(*) as count
        FROM audit_events
        WHERE resource_id = :tenant_id
        AND event_type = 'tenant_migration'
        AND created_at >= :month_start
        """
        
        try:
            with postgres_client.get_session() as session:
                result = session.execute(
                    text(query),
                    {
                        "tenant_id": tenant_id,
                        "month_start": month_start,
                    },
                )
                row = result.fetchone()
                return row[0] if row else 0
        except Exception as e:
            logger.exception("Failed to count migrations", tenant_id=tenant_id, error=str(e))
            return 0
    
    def _record_time_based_usage(self, tenant_id: str, quota_type: QuotaType, amount: int) -> None:
        """Record time-based quota usage in database."""
        # This would typically be done via audit logging
        # For now, we calculate on-demand from audit_events
        logger.debug(f"Time-based usage recorded", tenant_id=tenant_id, quota_type=quota_type.value, amount=amount)
    
    def _get_period(self, quota_type: QuotaType) -> tuple[Optional[datetime], Optional[datetime]]:
        """Get period start and end for time-based quotas."""
        now = datetime.utcnow()
        
        if quota_type == QuotaType.API_REQUESTS_PER_DAY:
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)
            return period_start, period_end
        elif quota_type == QuotaType.API_REQUESTS_PER_HOUR:
            period_start = now.replace(minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(hours=1)
            return period_start, period_end
        elif quota_type == QuotaType.EXPORTS_PER_MONTH:
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)
            return period_start, period_end
        elif quota_type == QuotaType.MIGRATIONS_PER_MONTH:
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)
            return period_start, period_end
        else:
            return None, None
