"""Request/response audit middleware. Logs access (view) for HTTP requests."""
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.infrastructure.logging import get_logger

from .audit_logger import audit_logger

logger = get_logger(__name__)


def _get_actor_id(request: Request) -> Optional[str]:
    """From JWT or request.state if set by auth middleware."""
    return getattr(request.state, "actor_id", None)


def _get_client_ip(request: Request) -> Optional[str]:
    return request.client.host if request.client else None


def _get_user_agent(request: Request) -> Optional[str]:
    return request.headers.get("user-agent")


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Logs ACCESS (view) for each request. Call audit_logger.ensure_audit_table() at app
    startup so the audit_events table exists.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        try:
            path = str(request.url.path)
            if path in ("/health", "/", "/docs", "/redoc", "/openapi.json"):
                return response
            method = request.method
            actor_id = _get_actor_id(request)
            ip = _get_client_ip(request)
            ua = _get_user_agent(request)
            audit_logger.log_access(
                action="view",
                actor_id=actor_id,
                resource_type="http",
                resource_id=f"{method} {path}",
                extra={"method": method, "path": path, "status": response.status_code},
                ip_address=ip,
                user_agent=ua[:500] if ua else None,
            )
        except Exception as e:
            logger.warning("Audit logging failed", error=str(e))
        return response
