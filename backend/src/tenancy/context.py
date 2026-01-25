"""Tenant context management."""
from typing import Optional
from contextvars import ContextVar
from fastapi import Request, Header
from src.tenancy.models import Tenant
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)

# Context variable for current tenant
current_tenant: ContextVar[Optional[Tenant]] = ContextVar("current_tenant", default=None)

# Lazy initialization to avoid circular imports
_tenant_manager = None

def get_tenant_manager():
    """Get tenant manager instance (lazy initialization)."""
    global _tenant_manager
    if _tenant_manager is None:
        from src.tenancy.manager import TenantManager
        _tenant_manager = TenantManager()
    return _tenant_manager


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
    # Check X-Tenant-ID header (case-insensitive)
    # FastAPI/Starlette headers are case-insensitive, but let's check both
    tenant_id = request.headers.get("X-Tenant-ID") or request.headers.get("x-tenant-id") or request.headers.get("X-TENANT-ID")
    
    # Also check all headers for debugging
    all_header_keys = list(request.headers.keys())
    print(f"[DEBUG] get_tenant_from_request: path={request.url.path}, tenant_id={tenant_id}, headers={all_header_keys[:5]}")
    logger.info(
        "Checking for tenant header",
        path=request.url.path,
        x_tenant_id=tenant_id,
        header_keys=all_header_keys[:10],
    )
    
    if tenant_id:
        logger.info("Found X-Tenant-ID header", tenant_id=tenant_id, path=request.url.path)
        tenant_manager = get_tenant_manager()
        tenant = tenant_manager.get_tenant(tenant_id.strip())  # Strip whitespace
        if tenant:
            if tenant.status == "active":
                logger.info("Tenant found and active", tenant_id=tenant_id, name=tenant.name)
                return tenant
            else:
                logger.warning("Tenant found but not active", tenant_id=tenant_id, status=tenant.status)
        else:
            logger.warning("Tenant not found in database", tenant_id=tenant_id)
    else:
        logger.warning("No X-Tenant-ID header found", path=request.url.path, available_headers=all_header_keys[:10])

    # Check subdomain
    host = request.headers.get("Host", "")
    if host:
        parts = host.split(".")
        if len(parts) >= 3:  # tenant.domain.com
            subdomain = parts[0]
            tenant_manager = get_tenant_manager()
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
