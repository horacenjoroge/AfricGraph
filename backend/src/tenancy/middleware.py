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
        skip_paths = ["/health", "/metrics", "/docs", "/openapi.json", "/redoc"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)

        # Extract tenant from request
        tenant = await get_tenant_from_request(request)
        
        if not tenant:
            # Allow some endpoints without tenant (e.g., tenant creation)
            if request.url.path.startswith("/api/tenants") and request.method == "POST":
                return await call_next(request)
            
            # For other endpoints, require tenant
            return Response(
                content='{"detail": "Tenant context required. Provide X-Tenant-ID header or use tenant subdomain."}',
                status_code=403,
                media_type="application/json",
            )

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
