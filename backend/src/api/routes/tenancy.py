"""Tenant management API endpoints."""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from src.tenancy.manager import TenantManager
from src.tenancy.models import Tenant, TenantConfig
from src.tenancy.analytics import CrossTenantAnalytics
from src.tenancy.export import TenantDataExporter
from src.tenancy.migration import TenantMigrationManager
from src.tenancy.context import get_current_tenant
from src.infrastructure.logging import get_logger

router = APIRouter(prefix="/tenants", tags=["tenants"])
logger = get_logger(__name__)

tenant_manager = TenantManager()
analytics = CrossTenantAnalytics()
exporter = TenantDataExporter()
migration_manager = TenantMigrationManager()


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
def create_tenant(request: TenantCreateRequest) -> dict:
    """Create a new tenant."""
    try:
        tenant = tenant_manager.create_tenant(
            tenant_id=request.tenant_id,
            name=request.name,
            domain=request.domain,
            config=request.config,
        )
        return tenant.model_dump(mode="json")
    except Exception as e:
        logger.exception("Failed to create tenant", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create tenant: {str(e)}")


@router.get("/{tenant_id}", response_model=dict)
def get_tenant(tenant_id: str) -> dict:
    """Get tenant by ID."""
    tenant = tenant_manager.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant.model_dump(mode="json")


@router.get("", response_model=dict)
def list_tenants(
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
) -> dict:
    """List tenants."""
    try:
        tenants = tenant_manager.list_tenants(status=status, limit=limit)
        return {
            "tenants": [tenant.model_dump(mode="json") for tenant in tenants],
            "total": len(tenants),
        }
    except Exception as e:
        logger.exception("Failed to list tenants", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list tenants: {str(e)}")


@router.put("/{tenant_id}", response_model=dict)
def update_tenant(tenant_id: str, request: TenantUpdateRequest) -> dict:
    """Update tenant."""
    tenant = tenant_manager.update_tenant(
        tenant_id=tenant_id,
        name=request.name,
        domain=request.domain,
        status=request.status,
        config=request.config,
    )
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant.model_dump(mode="json")


@router.post("/{tenant_id}/config", response_model=dict)
def set_tenant_config(tenant_id: str, request: TenantConfigRequest) -> dict:
    """Set tenant-specific configuration."""
    try:
        config = tenant_manager.set_tenant_config(
            tenant_id=tenant_id,
            key=request.key,
            value=request.value,
            description=request.description,
        )
        return config.model_dump(mode="json")
    except Exception as e:
        logger.exception("Failed to set tenant config", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to set config: {str(e)}")


@router.get("/{tenant_id}/config", response_model=dict)
def get_tenant_configs(tenant_id: str) -> dict:
    """Get all tenant configurations."""
    configs = tenant_manager.get_all_tenant_configs(tenant_id)
    return {"tenant_id": tenant_id, "configs": configs}


@router.get("/{tenant_id}/export")
def export_tenant_data(
    tenant_id: str,
    include_nodes: bool = Query(True),
    include_relationships: bool = Query(True),
    include_metadata: bool = Query(True),
) -> dict:
    """Export tenant data."""
    try:
        data = exporter.export_tenant_data(
            tenant_id=tenant_id,
            include_nodes=include_nodes,
            include_relationships=include_relationships,
            include_metadata=include_metadata,
        )
        return data
    except Exception as e:
        logger.exception("Failed to export tenant data", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")


@router.post("/migrate", response_model=dict)
def migrate_tenant(request: MigrationRequest) -> dict:
    """Migrate tenant data."""
    try:
        result = migration_manager.migrate_tenant(
            source_tenant_id=request.source_tenant_id,
            target_tenant_id=request.target_tenant_id,
            dry_run=request.dry_run,
        )
        return result
    except Exception as e:
        logger.exception("Failed to migrate tenant", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to migrate: {str(e)}")


@router.get("/analytics/aggregated")
def get_aggregated_analytics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
) -> dict:
    """Get aggregated analytics across all tenants (no individual tenant data)."""
    try:
        stats = analytics.get_aggregated_stats(
            start_date=start_date,
            end_date=end_date,
        )
        return stats
    except Exception as e:
        logger.exception("Failed to get aggregated analytics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/current", response_model=dict)
def get_current_tenant_info() -> dict:
    """Get current tenant information from context."""
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant context")
    return tenant.model_dump(mode="json")
