"""Tenant-aware middleware for FastAPI."""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from src.infrastructure.logging import get_logger
from src.tenancy.context import get_tenant_from_request, set_current_tenant

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
        # Log all headers for debugging
        x_tenant_header = request.headers.get("X-Tenant-ID") or request.headers.get("x-tenant-id") or request.headers.get("X-TENANT-ID")
        
        # Log ALL headers to see what's actually being sent
        all_headers_dict = dict(request.headers)
        logger.info(
            "Tenant middleware - checking request",
            path=request.url.path,
            method=request.method,
            x_tenant_id_header=x_tenant_header,
            all_headers=all_headers_dict,
        )
        
        tenant = await get_tenant_from_request(request)
        
        logger.info(
            "Tenant middleware - after extraction",
            path=request.url.path,
            has_tenant=tenant is not None,
            tenant_id=tenant.tenant_id if tenant else None,
        )
        
        if not tenant:
            # Allow some endpoints without tenant (e.g., tenant creation, auth, health checks)
            allowed_without_tenant = [
                "/tenants",
                "/api/tenants",
                "/api/auth",
                "/auth",
                "/graphql",  # GraphQL handles auth internally
                "/health",
                "/metrics",
                "/docs",
                "/openapi.json",
                "/redoc",
            ]
            if any(request.url.path.startswith(path) for path in allowed_without_tenant):
                return await call_next(request)
            
            # For data access endpoints, require tenant
            # Data access endpoints that require tenant isolation
            data_access_paths = [
                "/api/v1",
                "/api/graph",
                "/api/businesses",
                "/api/transactions",
                "/api/alerts",
                "/api/fraud",
            ]
            
            if any(request.url.path.startswith(path) for path in data_access_paths):
                logger.warning(
                    "Data access attempted without tenant",
                    path=request.url.path,
                    method=request.method,
                    x_tenant_header=x_tenant_header,
                    all_headers=list(request.headers.keys()),
                )
                # Don't raise 403 - allow request but it will return empty results
                # This is to prevent breaking existing clients
                # raise HTTPException(
                #     status_code=403,
                #     detail="Tenant context required for data access. Please set X-Tenant-ID header or select a tenant."
                # )
            
            # For other endpoints, allow but log warning
            logger.warning(
                "Request without tenant context",
                path=request.url.path,
                method=request.method,
            )
        
        if tenant:
            # Set tenant in context
            logger.info(
                "Setting tenant context",
                tenant_id=tenant.tenant_id,
                path=request.url.path,
            )
            set_current_tenant(tenant)
            
            # Verify it was set
            from src.tenancy.context import get_current_tenant as verify_tenant
            verified = verify_tenant()
            if verified:
                logger.info(
                    "Tenant context verified",
                    tenant_id=verified.tenant_id,
                )
            else:
                logger.error("Failed to set tenant context!")
            
            # Add tenant to request state for easy access
            request.state.tenant = tenant
            request.state.tenant_id = tenant.tenant_id

        try:
            response = await call_next(request)
            return response
        finally:
            # Clear tenant context after request
            set_current_tenant(None)
