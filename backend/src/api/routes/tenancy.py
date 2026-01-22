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
        manager = get_tenant_manager()
        tenant = manager.create_tenant(
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
    manager = get_tenant_manager()
    tenant = manager.get_tenant(tenant_id)
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
def update_tenant(tenant_id: str, request: TenantUpdateRequest) -> dict:
    """Update tenant."""
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
    return tenant.model_dump(mode="json")


@router.post("/{tenant_id}/config", response_model=dict)
def set_tenant_config(tenant_id: str, request: TenantConfigRequest) -> dict:
    """Set tenant-specific configuration."""
    try:
        manager = get_tenant_manager()
        config = manager.set_tenant_config(
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
    manager = get_tenant_manager()
    configs = manager.get_all_tenant_configs(tenant_id)
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
        exp = get_exporter()
        data = exp.export_tenant_data(
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
        mgr = get_migration_manager()
        result = mgr.migrate_tenant(
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
    """Get current tenant information from context."""
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant context")
    return tenant.model_dump(mode="json")
