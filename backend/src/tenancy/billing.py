"""Tenant billing and usage tracking."""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal

from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.logging import get_logger
from src.tenancy.manager import TenantManager
from src.tenancy.quotas import TenantQuotaManager, QuotaType

logger = get_logger(__name__)


class BillingPeriod(str, Enum):
    """Billing period types."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class UsageMetric(str, Enum):
    """Usage metrics for billing."""
    NODES = "nodes"
    RELATIONSHIPS = "relationships"
    STORAGE_GB = "storage_gb"
    API_REQUESTS = "api_requests"
    EXPORTS = "exports"
    MIGRATIONS = "migrations"
    SUPPORT_TICKETS = "support_tickets"


@dataclass
class UsageRecord:
    """Usage record for billing."""
    metric: UsageMetric
    quantity: Decimal
    unit_price: Decimal
    total: Decimal
    period_start: datetime
    period_end: datetime


@dataclass
class BillingPlan:
    """Billing plan definition."""
    plan_id: str
    name: str
    description: str
    base_price: Decimal
    billing_period: BillingPeriod
    included_usage: Dict[UsageMetric, Decimal]
    overage_rates: Dict[UsageMetric, Decimal]
    features: List[str]


class TenantBillingManager:
    """Manage billing and usage tracking for tenants."""
    
    def __init__(self):
        """Initialize billing manager."""
        self.tenant_manager = TenantManager()
        self.quota_manager = TenantQuotaManager()
        
        # Default billing plans
        self.default_plans = {
            "free": BillingPlan(
                plan_id="free",
                name="Free Tier",
                description="Free tier with basic features",
                base_price=Decimal("0.00"),
                billing_period=BillingPeriod.MONTHLY,
                included_usage={
                    UsageMetric.NODES: Decimal("1000"),
                    UsageMetric.RELATIONSHIPS: Decimal("5000"),
                    UsageMetric.STORAGE_GB: Decimal("1"),
                    UsageMetric.API_REQUESTS: Decimal("10000"),
                },
                overage_rates={
                    UsageMetric.NODES: Decimal("0.01"),  # $0.01 per 1000 nodes
                    UsageMetric.RELATIONSHIPS: Decimal("0.005"),  # $0.005 per 1000 relationships
                    UsageMetric.STORAGE_GB: Decimal("0.10"),  # $0.10 per GB
                    UsageMetric.API_REQUESTS: Decimal("0.0001"),  # $0.0001 per request
                },
                features=["basic_graph", "api_access"],
            ),
            "pro": BillingPlan(
                plan_id="pro",
                name="Professional",
                description="Professional plan with advanced features",
                base_price=Decimal("99.00"),
                billing_period=BillingPeriod.MONTHLY,
                included_usage={
                    UsageMetric.NODES: Decimal("100000"),
                    UsageMetric.RELATIONSHIPS: Decimal("500000"),
                    UsageMetric.STORAGE_GB: Decimal("100"),
                    UsageMetric.API_REQUESTS: Decimal("1000000"),
                },
                overage_rates={
                    UsageMetric.NODES: Decimal("0.008"),
                    UsageMetric.RELATIONSHIPS: Decimal("0.004"),
                    UsageMetric.STORAGE_GB: Decimal("0.08"),
                    UsageMetric.API_REQUESTS: Decimal("0.00008"),
                },
                features=["advanced_graph", "api_access", "analytics", "exports"],
            ),
            "enterprise": BillingPlan(
                plan_id="enterprise",
                name="Enterprise",
                description="Enterprise plan with unlimited features",
                base_price=Decimal("999.00"),
                billing_period=BillingPeriod.MONTHLY,
                included_usage={
                    UsageMetric.NODES: Decimal("1000000"),
                    UsageMetric.RELATIONSHIPS: Decimal("5000000"),
                    UsageMetric.STORAGE_GB: Decimal("1000"),
                    UsageMetric.API_REQUESTS: Decimal("10000000"),
                },
                overage_rates={
                    UsageMetric.NODES: Decimal("0.005"),
                    UsageMetric.RELATIONSHIPS: Decimal("0.002"),
                    UsageMetric.STORAGE_GB: Decimal("0.05"),
                    UsageMetric.API_REQUESTS: Decimal("0.00005"),
                },
                features=["unlimited_graph", "api_access", "analytics", "exports", "migrations", "support"],
            ),
        }
    
    def get_tenant_plan(self, tenant_id: str) -> Optional[BillingPlan]:
        """
        Get billing plan for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Billing plan or None
        """
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return None
        
        # Get plan from tenant config
        configs = self.tenant_manager.get_all_tenant_configs(tenant_id)
        plan_id = "free"  # Default
        
        for config in configs:
            if config.key == "billing_plan":
                plan_id = config.value
                break
        
        return self.default_plans.get(plan_id)
    
    def set_tenant_plan(self, tenant_id: str, plan_id: str) -> None:
        """
        Set billing plan for a tenant.
        
        Args:
            tenant_id: Tenant ID
            plan_id: Plan ID
        """
        if plan_id not in self.default_plans:
            raise ValueError(f"Invalid plan ID: {plan_id}")
        
        self.tenant_manager.set_tenant_config(
            tenant_id=tenant_id,
            key="billing_plan",
            value=plan_id,
            description=f"Billing plan: {self.default_plans[plan_id].name}",
        )
        logger.info(f"Billing plan set", tenant_id=tenant_id, plan_id=plan_id)
    
    def calculate_usage(
        self,
        tenant_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> Dict[UsageMetric, UsageRecord]:
        """
        Calculate usage for a billing period.
        
        Args:
            tenant_id: Tenant ID
            period_start: Period start
            period_end: Period end
            
        Returns:
            Dictionary of usage records by metric
        """
        plan = self.get_tenant_plan(tenant_id)
        if not plan:
            return {}
        
        usage_records = {}
        
        # Calculate usage for each metric
        for metric in UsageMetric:
            quantity = self._get_usage_quantity(tenant_id, metric, period_start, period_end)
            included = plan.included_usage.get(metric, Decimal("0"))
            overage = max(Decimal("0"), quantity - included)
            
            unit_price = plan.overage_rates.get(metric, Decimal("0"))
            total = overage * unit_price
            
            usage_records[metric] = UsageRecord(
                metric=metric,
                quantity=quantity,
                unit_price=unit_price,
                total=total,
                period_start=period_start,
                period_end=period_end,
            )
        
        return usage_records
    
    def calculate_bill(
        self,
        tenant_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Calculate total bill for a tenant.
        
        Args:
            tenant_id: Tenant ID
            period_start: Period start (defaults to current billing period)
            period_end: Period end (defaults to current billing period)
            
        Returns:
            Bill summary
        """
        plan = self.get_tenant_plan(tenant_id)
        if not plan:
            return {
                "tenant_id": tenant_id,
                "plan": None,
                "base_price": Decimal("0"),
                "usage": {},
                "overage": Decimal("0"),
                "total": Decimal("0"),
            }
        
        # Determine billing period
        if not period_start or not period_end:
            period_start, period_end = self._get_current_billing_period(tenant_id, plan)
        
        # Calculate usage
        usage_records = self.calculate_usage(tenant_id, period_start, period_end)
        
        # Calculate totals
        base_price = plan.base_price
        overage_total = sum(record.total for record in usage_records.values())
        total = base_price + overage_total
        
        return {
            "tenant_id": tenant_id,
            "plan": {
                "plan_id": plan.plan_id,
                "name": plan.name,
                "base_price": float(base_price),
            },
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat(),
            },
            "base_price": float(base_price),
            "usage": {
                metric.value: {
                    "quantity": float(record.quantity),
                    "included": float(plan.included_usage.get(metric, Decimal("0"))),
                    "overage": float(record.quantity - plan.included_usage.get(metric, Decimal("0"))),
                    "unit_price": float(record.unit_price),
                    "total": float(record.total),
                }
                for metric, record in usage_records.items()
            },
            "overage_total": float(overage_total),
            "total": float(total),
        }
    
    def get_usage_summary(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get current usage summary for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Usage summary
        """
        plan = self.get_tenant_plan(tenant_id)
        if not plan:
            return {
                "tenant_id": tenant_id,
                "plan": None,
                "current_usage": {},
            }
        
        # Get current quotas
        quotas = self.quota_manager.get_all_quotas(tenant_id)
        
        # Map quotas to usage metrics
        usage = {}
        quota_mapping = {
            QuotaType.NODES: UsageMetric.NODES,
            QuotaType.RELATIONSHIPS: UsageMetric.RELATIONSHIPS,
            QuotaType.STORAGE_MB: UsageMetric.STORAGE_GB,  # Convert MB to GB
            QuotaType.API_REQUESTS_PER_DAY: UsageMetric.API_REQUESTS,
        }
        
        for quota_type, metric in quota_mapping.items():
            quota = quotas.get(quota_type)
            if quota:
                included = plan.included_usage.get(metric, Decimal("0"))
                if metric == UsageMetric.STORAGE_GB:
                    # Convert MB to GB
                    current = Decimal(str(quota.current_usage)) / Decimal("1024")
                else:
                    current = Decimal(str(quota.current_usage))
                
                usage[metric.value] = {
                    "current": float(current),
                    "included": float(included),
                    "overage": float(max(Decimal("0"), current - included)),
                    "limit": float(Decimal(str(quota.limit))),
                    "usage_percentage": quota.usage_percentage,
                }
        
        return {
            "tenant_id": tenant_id,
            "plan": {
                "plan_id": plan.plan_id,
                "name": plan.name,
            },
            "current_usage": usage,
        }
    
    def _get_usage_quantity(
        self,
        tenant_id: str,
        metric: UsageMetric,
        period_start: datetime,
        period_end: datetime,
    ) -> Decimal:
        """Get usage quantity for a metric in a period."""
        if metric == UsageMetric.NODES:
            quota = self.quota_manager.get_tenant_quota(tenant_id, QuotaType.NODES)
            return Decimal(str(quota.current_usage))
        elif metric == UsageMetric.RELATIONSHIPS:
            quota = self.quota_manager.get_tenant_quota(tenant_id, QuotaType.RELATIONSHIPS)
            return Decimal(str(quota.current_usage))
        elif metric == UsageMetric.STORAGE_GB:
            quota = self.quota_manager.get_tenant_quota(tenant_id, QuotaType.STORAGE_MB)
            return Decimal(str(quota.current_usage)) / Decimal("1024")  # Convert MB to GB
        elif metric == UsageMetric.API_REQUESTS:
            # Count API requests in period
            return Decimal(str(self._count_api_requests_in_period(tenant_id, period_start, period_end)))
        else:
            return Decimal("0")
    
    def _count_api_requests_in_period(
        self,
        tenant_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> int:
        """Count API requests in a period."""
        from sqlalchemy import text
        
        query = """
        SELECT COUNT(*) as count
        FROM audit_events
        WHERE resource_id = :tenant_id
        AND event_type = 'api_request'
        AND created_at >= :period_start
        AND created_at < :period_end
        """
        
        try:
            with postgres_client.get_session() as session:
                result = session.execute(
                    text(query),
                    {
                        "tenant_id": tenant_id,
                        "period_start": period_start,
                        "period_end": period_end,
                    },
                )
                row = result.fetchone()
                return row[0] if row else 0
        except Exception as e:
            logger.exception("Failed to count API requests", tenant_id=tenant_id, error=str(e))
            return 0
    
    def _get_current_billing_period(
        self,
        tenant_id: str,
        plan: BillingPlan,
    ) -> tuple[datetime, datetime]:
        """Get current billing period dates."""
        now = datetime.utcnow()
        
        if plan.billing_period == BillingPeriod.MONTHLY:
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)
        elif plan.billing_period == BillingPeriod.QUARTERLY:
            quarter = (now.month - 1) // 3
            period_start = now.replace(month=quarter * 3 + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            if period_start.month == 10:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 3)
        elif plan.billing_period == BillingPeriod.YEARLY:
            period_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start.replace(year=period_start.year + 1)
        else:
            # Default to monthly
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)
        
        return period_start, period_end
