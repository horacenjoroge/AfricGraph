"""Middleware to enrich requests with ABAC environment context."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from src.config.settings import settings
from .attributes import EnvironmentAttributes


class PermissionContextMiddleware(BaseHTTPMiddleware):
    """Attach EnvironmentAttributes to request.state for downstream permission checks."""

    async def dispatch(self, request: Request, call_next):
        request.state.abac_environment = EnvironmentAttributes.from_request(
            request,
            timezone_name=getattr(settings, "abac_timezone", "UTC"),
        )
        response = await call_next(request)
        return response

