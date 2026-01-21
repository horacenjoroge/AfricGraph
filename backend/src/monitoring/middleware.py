"""Monitoring middleware for API metrics."""
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from src.monitoring.metrics import (
    api_requests_total,
    api_request_duration_seconds,
    api_errors_total,
)
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect API metrics."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        method = request.method
        endpoint = request.url.path

        # Skip metrics endpoint itself
        if endpoint == "/metrics":
            return await call_next(request)

        try:
            response = await call_next(request)
            status_code = response.status_code
            status_class = f"{status_code // 100}xx"

            # Record metrics
            api_requests_total.labels(
                method=method, endpoint=endpoint, status=status_class
            ).inc()

            duration = time.time() - start_time
            api_request_duration_seconds.labels(
                method=method, endpoint=endpoint
            ).observe(duration)

            # Record errors
            if status_code >= 400:
                error_type = "client_error" if status_code < 500 else "server_error"
                api_errors_total.labels(
                    method=method, endpoint=endpoint, error_type=error_type
                ).inc()

            return response

        except Exception as e:
            # Record exception
            duration = time.time() - start_time
            api_errors_total.labels(
                method=method, endpoint=endpoint, error_type="exception"
            ).inc()
            api_request_duration_seconds.labels(
                method=method, endpoint=endpoint
            ).observe(duration)

            logger.exception("Request failed", endpoint=endpoint, error=str(e))
            raise
