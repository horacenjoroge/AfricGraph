"""Tenant-aware middleware for FastAPI."""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.infrastructure.logging import get_logger
from src.tenancy.context import get_tenant_from_request, set_current_tenant, get_current_tenant
from src.tenancy.models import Tenant

logger = get_logger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to extract and set tenant context."""

    async def dispatch(self, request: Request, call_next):
        """Process request with tenant context."""
        # Skip tenant check for certain paths
        skip_paths = ["/health", "/metrics", "/docs", "/openapi.json", "/redoc", "/"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)

        # Extract tenant from request
        tenant = await get_tenant_from_request(request)
        
        if not tenant:
            # Allow some endpoints without tenant (e.g., tenant creation, auth)
            allowed_without_tenant = [
                "/api/tenants",
                "/api/auth",
                "/graphql",  # GraphQL handles auth internally
            ]
            if any(request.url.path.startswith(path) for path in allowed_without_tenant):
                return await call_next(request)
            
            # For development: try to get or create a default tenant
            # In production, this should be more strict
            try:
                from src.tenancy.manager import tenant_manager
                # Try to get a default tenant or create one
                default_tenants = tenant_manager.list_tenants(limit=1)
                if default_tenants:
                    tenant = default_tenants[0]
                else:
                    # Create a default tenant for development
                    tenant = tenant_manager.create_tenant(
                        name="Default Tenant",
                        domain=None,
                        config={"development": True}
                    )
                    logger.info("Created default tenant for development", tenant_id=tenant.tenant_id)
            except Exception as e:
                logger.warning("Could not get/create default tenant", error=str(e))
                # For development, allow requests to proceed without tenant
                # In production, this should return 403
                return await call_next(request)
        
        if tenant:
            # Set tenant in context
            set_current_tenant(tenant)
            
            # Add tenant to request state for easy access
            request.state.tenant = tenant
            request.state.tenant_id = tenant.tenant_id

        try:
            response = await call_next(request)
            return response
        finally:
            # Clear tenant context after request
            set_current_tenant(None)
