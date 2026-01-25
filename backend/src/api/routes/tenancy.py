"""Tenant management API endpoints."""
from fastapi import APIRouter, HTTPException, Query, Depends, Header
from typing import Optional, List, Any
from pydantic import BaseModel
from datetime import datetime

from src.tenancy.manager import TenantManager
from src.tenancy.models import Tenant, TenantConfig
from src.tenancy.analytics import CrossTenantAnalytics
from src.tenancy.export import TenantDataExporter
from src.tenancy.migration import TenantMigrationManager
from src.tenancy.context import get_current_tenant
from src.infrastructure.logging import get_logger
from src.auth.service import get_user_by_id
from src.auth.jwt_handler import validate_access_token

router = APIRouter(prefix="/tenants", tags=["tenants"])
logger = get_logger(__name__)

# Initialize managers lazily to avoid connection issues at import time
tenant_manager = None
analytics = None
exporter = None
migration_manager = None

def get_tenant_manager():
    global tenant_manager
    if tenant_manager is None:
        tenant_manager = TenantManager()
    return tenant_manager

def get_analytics():
    global analytics
    if analytics is None:
        analytics = CrossTenantAnalytics()
    return analytics

def get_exporter():
    global exporter
    if exporter is None:
        exporter = TenantDataExporter()
    return exporter

def get_migration_manager():
    global migration_manager
    if migration_manager is None:
        migration_manager = TenantMigrationManager()
    return migration_manager


def get_current_user_id(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract user ID from JWT token in Authorization header."""
    if not authorization:
        return None
    try:
        token = authorization.replace("Bearer ", "").strip()
        payload = validate_access_token(token)
        if payload:
            return payload.get("sub")
    except Exception:
        pass
    return None


def require_admin(user_id: Optional[str] = Depends(get_current_user_id)) -> dict:
    """Require admin role for tenant management operations."""
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin role required for tenant management operations"
        )
    
    return {"user_id": user_id, "role": user.role}


class TenantCreateRequest(BaseModel):
    """Tenant creation request."""
    tenant_id: str
    name: str
    domain: Optional[str] = None
    config: Optional[dict] = None


class TenantUpdateRequest(BaseModel):
    """Tenant update request."""
    name: Optional[str] = None
    domain: Optional[str] = None
    status: Optional[str] = None
    config: Optional[dict] = None


class TenantConfigRequest(BaseModel):
    """Tenant configuration request."""
    key: str
    value: Any
    description: Optional[str] = None


class MigrationRequest(BaseModel):
    """Tenant migration request."""
    source_tenant_id: str
    target_tenant_id: str
    dry_run: bool = False


@router.post("", response_model=dict)
def create_tenant(
    request: TenantCreateRequest,
    admin: dict = Depends(require_admin)
) -> dict:
    """Create a new tenant. Requires admin role."""
    try:
        manager = get_tenant_manager()
        tenant = manager.create_tenant(
            tenant_id=request.tenant_id,
            name=request.name,
            domain=request.domain,
            config=request.config,
        )
        logger.info(f"Tenant created by admin {admin['user_id']}", tenant_id=request.tenant_id)
        return tenant.model_dump(mode="json")
    except Exception as e:
        logger.exception("Failed to create tenant", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create tenant: {str(e)}")


@router.get("/available", response_model=dict)
def list_available_tenants(
    user_id: Optional[str] = Depends(get_current_user_id),
    status: Optional[str] = Query("active", description="Filter by status"),
) -> dict:
    """
    List tenants available to the current user.
    - Admins see all tenants (filtered by status if provided)
    - Regular users see all active tenants (for selection)
    - If not authenticated, returns all active tenants (for development)
    """
    try:
        manager = get_tenant_manager()
        
        # Default to active if no status specified
        filter_status = status if status else "active"
        
        # If user is admin, return all tenants (or filtered by status)
        if user_id:
            user = get_user_by_id(user_id)
            if user and user.role == "admin":
                tenants = manager.list_tenants(status=filter_status, limit=1000)
                return {
                    "tenants": [tenant.model_dump(mode="json") for tenant in tenants],
                    "total": len(tenants),
                }
        
        # For regular users or unauthenticated, return active tenants only
        tenants = manager.list_tenants(status="active", limit=1000)
        logger.info(f"Returning {len(tenants)} active tenants for user", user_id=user_id)
        return {
            "tenants": [tenant.model_dump(mode="json") for tenant in tenants],
            "total": len(tenants),
        }
    except Exception as e:
        logger.exception("Failed to list available tenants", error=str(e))
        # Return empty list on error rather than failing
        return {"tenants": [], "total": 0}


@router.get("/{tenant_id}", response_model=dict)
def get_tenant(
    tenant_id: str,
    user_id: Optional[str] = Depends(get_current_user_id),
) -> dict:
    """Get tenant by ID. Users can only view their current tenant, admins can view any tenant."""
    manager = get_tenant_manager()
    tenant = manager.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Check if user is admin or viewing their own tenant
    if user_id:
        user = get_user_by_id(user_id)
        if user and user.role == "admin":
            # Admins can view any tenant
            return tenant.model_dump(mode="json")
        
        # Regular users can only view their current tenant
        current_tenant = get_current_tenant()
        if current_tenant and current_tenant.tenant_id == tenant_id:
            return tenant.model_dump(mode="json")
        else:
            raise HTTPException(
                status_code=403,
                detail="You can only view your current tenant. Admin role required to view other tenants."
            )
    
    # If not authenticated, allow viewing (for development)
    return tenant.model_dump(mode="json")


@router.get("", response_model=dict)
def list_tenants(
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    admin: dict = Depends(require_admin),
) -> dict:
    """List all tenants. Requires admin role."""
    try:
        manager = get_tenant_manager()
        tenants = manager.list_tenants(status=status, limit=limit)
        return {
            "tenants": [tenant.model_dump(mode="json") for tenant in tenants],
            "total": len(tenants),
        }
    except Exception as e:
        logger.exception("Failed to list tenants", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list tenants: {str(e)}")


@router.put("/{tenant_id}", response_model=dict)
def update_tenant(
    tenant_id: str,
    request: TenantUpdateRequest,
    admin: dict = Depends(require_admin),
) -> dict:
    """Update tenant. Requires admin role."""
    manager = get_tenant_manager()
    tenant = manager.update_tenant(
        tenant_id=tenant_id,
        name=request.name,
        domain=request.domain,
        status=request.status,
        config=request.config,
    )
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    logger.info(f"Tenant updated by admin {admin['user_id']}", tenant_id=tenant_id)
    return tenant.model_dump(mode="json")


@router.post("/{tenant_id}/config", response_model=dict)
def set_tenant_config(
    tenant_id: str,
    request: TenantConfigRequest,
    admin: dict = Depends(require_admin),
) -> dict:
    """Set tenant-specific configuration. Requires admin role."""
    try:
        manager = get_tenant_manager()
        config = manager.set_tenant_config(
            tenant_id=tenant_id,
            key=request.key,
            value=request.value,
            description=request.description,
        )
        logger.info(f"Tenant config set by admin {admin['user_id']}", tenant_id=tenant_id, key=request.key)
        return config.model_dump(mode="json")
    except Exception as e:
        logger.exception("Failed to set tenant config", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to set config: {str(e)}")


@router.get("/{tenant_id}/config", response_model=dict)
def get_tenant_configs(
    tenant_id: str,
    user_id: Optional[str] = Depends(get_current_user_id),
) -> dict:
    """Get all tenant configurations. Users can only view their current tenant's config, admins can view any tenant."""
    # Check if user is admin or viewing their own tenant
    if user_id:
        user = get_user_by_id(user_id)
        if user and user.role == "admin":
            # Admins can view any tenant's config
            manager = get_tenant_manager()
            configs = manager.get_all_tenant_configs(tenant_id)
            return {"tenant_id": tenant_id, "configs": configs}
        
        # Regular users can only view their current tenant's config
        current_tenant = get_current_tenant()
        if current_tenant and current_tenant.tenant_id == tenant_id:
            manager = get_tenant_manager()
            configs = manager.get_all_tenant_configs(tenant_id)
            return {"tenant_id": tenant_id, "configs": configs}
        else:
            raise HTTPException(
                status_code=403,
                detail="You can only view your current tenant's configuration. Admin role required to view other tenants."
            )
    
    # If not authenticated, allow viewing (for development)
    manager = get_tenant_manager()
    configs = manager.get_all_tenant_configs(tenant_id)
    return {"tenant_id": tenant_id, "configs": configs}


@router.get("/{tenant_id}/export")
def export_tenant_data(
    tenant_id: str,
    include_nodes: bool = Query(True),
    include_relationships: bool = Query(True),
    include_metadata: bool = Query(True),
    admin: dict = Depends(require_admin),
) -> dict:
    """Export tenant data. Requires admin role."""
    try:
        exp = get_exporter()
        data = exp.export_tenant_data(
            tenant_id=tenant_id,
            include_nodes=include_nodes,
            include_relationships=include_relationships,
            include_metadata=include_metadata,
        )
        logger.info(f"Tenant data exported by admin {admin['user_id']}", tenant_id=tenant_id)
        return data
    except Exception as e:
        logger.exception("Failed to export tenant data", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")


@router.post("/migrate", response_model=dict)
def migrate_tenant(
    request: MigrationRequest,
    admin: dict = Depends(require_admin),
) -> dict:
    """Migrate tenant data. Requires admin role."""
    try:
        mgr = get_migration_manager()
        result = mgr.migrate_tenant(
            source_tenant_id=request.source_tenant_id,
            target_tenant_id=request.target_tenant_id,
            dry_run=request.dry_run,
        )
        logger.info(
            f"Tenant migration initiated by admin {admin['user_id']}",
            source=request.source_tenant_id,
            target=request.target_tenant_id,
        )
        return result
    except Exception as e:
        logger.exception("Failed to migrate tenant", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to migrate: {str(e)}")


@router.get("/analytics/aggregated")
def get_aggregated_analytics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    admin: dict = Depends(require_admin),
) -> dict:
    """Get aggregated analytics across all tenants. Requires admin role."""
    try:
        anl = get_analytics()
        stats = anl.get_aggregated_stats(
            start_date=start_date,
            end_date=end_date,
        )
        return stats
    except Exception as e:
        logger.exception("Failed to get aggregated analytics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/current", response_model=dict)
def get_current_tenant_info() -> dict:
    """Get current tenant information from context. Accessible to all authenticated users."""
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant context")
    return tenant.model_dump(mode="json")


@router.get("/me", response_model=dict)
def get_my_tenant_info() -> dict:
    """Get current tenant information (alias for /current). Accessible to all authenticated users."""
    return get_current_tenant_info()


@router.get("/debug/context", response_model=dict)
def debug_tenant_context() -> dict:
    """Debug endpoint to check tenant context."""
    from src.tenancy.context import get_current_tenant
    tenant = get_current_tenant()
    return {
        "has_tenant": tenant is not None,
        "tenant_id": tenant.tenant_id if tenant else None,
        "tenant_name": tenant.name if tenant else None,
        "tenant_status": tenant.status if tenant else None,
    }


@router.post("/indexes/ensure", response_model=dict)
def ensure_tenant_indexes(
    admin: dict = Depends(require_admin),
) -> dict:
    """Ensure all tenant isolation indexes exist. Requires admin role."""
    try:
        from src.tenancy.indexes import ensure_tenant_indexes
        results = ensure_tenant_indexes()
        logger.info("Tenant indexes ensured", results=results)
        return results
    except Exception as e:
        logger.exception("Failed to ensure indexes", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to ensure indexes: {str(e)}")


@router.get("/indexes/status", response_model=dict)
def get_index_status(
    admin: dict = Depends(require_admin),
) -> dict:
    """Get status of tenant-related indexes. Requires admin role."""
    try:
        from src.tenancy.indexes import get_index_status
        return get_index_status()
    except Exception as e:
        logger.exception("Failed to get index status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get index status: {str(e)}")


@router.get("/analytics/distribution", response_model=dict)
def get_tenant_distribution(
    metric: str = Query("nodes", description="Metric: nodes or relationships"),
    admin: dict = Depends(require_admin),
) -> dict:
    """Get tenant distribution by metric. Requires admin role."""
    try:
        anl = get_analytics()
        return anl.get_tenant_distribution(metric=metric)
    except Exception as e:
        logger.exception("Failed to get tenant distribution", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get distribution: {str(e)}")


@router.get("/analytics/activity", response_model=dict)
def get_activity_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    admin: dict = Depends(require_admin),
) -> dict:
    """Get aggregated activity summary. Requires admin role."""
    try:
        anl = get_analytics()
        return anl.get_activity_summary(days=days)
    except Exception as e:
        logger.exception("Failed to get activity summary", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get activity: {str(e)}")


@router.get("/{tenant_id}/health", response_model=dict)
def get_tenant_health(
    tenant_id: str,
    admin: dict = Depends(require_admin),
) -> dict:
    """Get health metrics for a tenant. Requires admin role."""
    try:
        from src.tenancy.monitoring import TenantMonitoring
        monitoring = TenantMonitoring()
        return monitoring.get_tenant_health(tenant_id)
    except Exception as e:
        logger.exception("Failed to get tenant health", tenant_id=tenant_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get health: {str(e)}")


@router.get("/{tenant_id}/usage", response_model=dict)
def get_tenant_usage(
    tenant_id: str,
    days: int = Query(30, ge=1, le=365),
    admin: dict = Depends(require_admin),
) -> dict:
    """Get resource usage for a tenant. Requires admin role."""
    try:
        from src.tenancy.monitoring import TenantMonitoring
        monitoring = TenantMonitoring()
        return monitoring.get_tenant_resource_usage(tenant_id, days=days)
    except Exception as e:
        logger.exception("Failed to get tenant usage", tenant_id=tenant_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get usage: {str(e)}")


@router.get("/health/all", response_model=dict)
def get_all_tenants_health(
    admin: dict = Depends(require_admin),
) -> dict:
    """Get health status for all tenants. Requires admin role."""
    try:
        from src.tenancy.monitoring import TenantMonitoring
        monitoring = TenantMonitoring()
        health_statuses = monitoring.get_all_tenants_health()
        return {
            "total_tenants": len(health_statuses),
            "healthy_tenants": sum(1 for h in health_statuses if h.get("healthy", False)),
            "unhealthy_tenants": sum(1 for h in health_statuses if not h.get("healthy", False)),
            "tenants": health_statuses,
        }
    except Exception as e:
        logger.exception("Failed to get all tenants health", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get health: {str(e)}")
