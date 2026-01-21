"""Rate limiting middleware."""
from collections import defaultdict
from time import time
from typing import Callable

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.infrastructure.logging import get_logger

logger = get_logger(__name__)

# Simple in-memory rate limiter (can be replaced with Redis)
_rate_limits: dict[str, list[float]] = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/"]:
            return await call_next(request)

        # Get client identifier (IP or user ID from token)
        client_id = request.client.host if request.client else "unknown"
        # TODO: Extract user_id from JWT token if authenticated

        # Check rate limit
        now = time()
        window_start = now - 60  # 1 minute window

        # Clean old entries
        _rate_limits[client_id] = [
            ts for ts in _rate_limits[client_id] if ts > window_start
        ]

        # Check if limit exceeded
        if len(_rate_limits[client_id]) >= self.requests_per_minute:
            logger.warning("Rate limit exceeded", client_id=client_id)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )

        # Record request
        _rate_limits[client_id].append(now)

        return await call_next(request)
