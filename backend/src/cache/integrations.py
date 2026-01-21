"""Cache integrations for existing services."""
from functools import wraps
from typing import Callable, TypeVar

from src.cache.service import CacheService, make_cache_key, cache_aside
from src.cache.config import CacheKey, CacheTTL
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


def cached_risk_score(func: Callable[..., T]) -> Callable[..., T]:
    """Cache decorator for risk score computation."""
    return cache_aside(CacheKey.RISK_SCORE, ttl=CacheTTL.RISK_SCORE)(func)


def cached_graph_query(key_type: CacheKey = CacheKey.GRAPH_QUERY, ttl: int = CacheTTL.GRAPH_QUERY_MEDIUM):
    """Cache decorator for graph queries."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        return cache_aside(key_type, ttl=ttl)(func)
    return decorator


def cached_business(func: Callable[..., T]) -> Callable[..., T]:
    """Cache decorator for business data."""
    return cache_aside(CacheKey.BUSINESS, ttl=CacheTTL.BUSINESS)(func)


def cached_permission(func: Callable[..., T]) -> Callable[..., T]:
    """Cache decorator for permission decisions."""
    return cache_aside(CacheKey.PERMISSION, ttl=CacheTTL.PERMISSION)(func)


def cached_api_response(ttl: int = CacheTTL.API_RESPONSE_MEDIUM):
    """Cache decorator for API responses."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Create cache key from request
            import hashlib
            import json
            
            # Use function name and arguments for key
            key_data = {
                "func": func.__name__,
                "args": str(args),
                "kwargs": json.dumps(kwargs, sort_keys=True, default=str),
            }
            key_str = json.dumps(key_data, sort_keys=True)
            key_hash = hashlib.md5(key_str.encode()).hexdigest()
            cache_key = make_cache_key(CacheKey.API_RESPONSE, func.__name__, key_hash)
            
            # Try cache
            cached = CacheService.get(cache_key)
            if cached is not None:
                logger.debug("API response cache hit", key=cache_key)
                return cached
            
            # Cache miss - execute function
            result = func(*args, **kwargs)
            
            # Cache result
            if result is not None:
                CacheService.set(cache_key, result, ttl=ttl)
                logger.debug("API response cached", key=cache_key)
            
            return result
        return wrapper
    return decorator
