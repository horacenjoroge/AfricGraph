"""Tenant context management."""
from typing import Optional
from contextvars import ContextVar
from fastapi import Request, Header
from src.tenancy.models import Tenant
from src.tenancy.manager import TenantManager

# Context variable for current tenant
current_tenant: ContextVar[Optional[Tenant]] = ContextVar("current_tenant", default=None)

tenant_manager = TenantManager()


def get_current_tenant() -> Optional[Tenant]:
    """Get current tenant from context."""
    return current_tenant.get()


def set_current_tenant(tenant: Optional[Tenant]) -> None:
    """Set current tenant in context."""
    current_tenant.set(tenant)


async def get_tenant_from_request(request: Request) -> Optional[Tenant]:
    """
    Extract tenant from request.

    Checks:
    1. X-Tenant-ID header
    2. Subdomain from Host header
    3. Tenant from JWT token (if available)
    """
    # Check X-Tenant-ID header
    tenant_id = request.headers.get("X-Tenant-ID")
    if tenant_id:
        tenant = tenant_manager.get_tenant(tenant_id)
        if tenant and tenant.status == "active":
            return tenant

    # Check subdomain
    host = request.headers.get("Host", "")
    if host:
        parts = host.split(".")
        if len(parts) >= 3:  # tenant.domain.com
            subdomain = parts[0]
            tenant = tenant_manager.get_tenant(subdomain)
            if tenant and tenant.status == "active":
                return tenant

    # Check JWT token (if available)
    # This would be implemented with your auth system
    # For now, return None if no tenant found
    return None


def require_tenant(func):
    """Decorator to require tenant context."""
    async def wrapper(*args, **kwargs):
        tenant = get_current_tenant()
        if not tenant:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Tenant context required")
        return await func(*args, **kwargs)
    return wrapper
