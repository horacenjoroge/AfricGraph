"""Cache service with cache-aside and write-through patterns."""
import json
import hashlib
from typing import Optional, Any, Callable, TypeVar
from functools import wraps

from src.infrastructure.cache.redis_client import redis_client
from src.cache.config import CacheKey, CacheTTL, get_ttl
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


def make_cache_key(key_type: CacheKey, *parts: str) -> str:
    """Create a cache key from parts."""
    key_parts = [key_type.value] + [str(p) for p in parts]
    return ":".join(key_parts)


def serialize_value(value: Any) -> str:
    """Serialize value for caching."""
    if isinstance(value, str):
        return value
    return json.dumps(value, default=str)


def deserialize_value(value: str) -> Any:
    """Deserialize cached value."""
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


def cache_aside(
    key_type: CacheKey,
    ttl: Optional[int] = None,
    key_func: Optional[Callable] = None,
):
    """
    Cache-aside pattern decorator.

    Usage:
        @cache_aside(CacheKey.RISK_SCORE)
        def get_risk_score(business_id: str):
            # Fetch from database
            return compute_risk(business_id)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: use function name and arguments
                key_parts = [func.__name__] + [str(arg) for arg in args]
                key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
                cache_key = make_cache_key(key_type, *key_parts)

            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached is not None:
                logger.debug("Cache hit", key=cache_key)
                return deserialize_value(cached)

            # Cache miss - compute value
            logger.debug("Cache miss", key=cache_key)
            value = func(*args, **kwargs)

            # Store in cache
            if value is not None:
                cache_ttl = ttl or get_ttl(key_type)
                serialized = serialize_value(value)
                redis_client.set(cache_key, serialized, ttl=cache_ttl)

            return value

        return wrapper

    return decorator


def write_through(
    key_type: CacheKey,
    ttl: Optional[int] = None,
    key_func: Optional[Callable] = None,
):
    """
    Write-through pattern decorator.

    Updates both cache and data source.

    Usage:
        @write_through(CacheKey.BUSINESS)
        def update_business(business_id: str, data: dict):
            # Update database
            db.update(business_id, data)
            # Cache is automatically updated
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Execute function (updates data source)
            value = func(*args, **kwargs)

            # Update cache
            if value is not None:
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    key_parts = [func.__name__] + [str(arg) for arg in args]
                    key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
                    cache_key = make_cache_key(key_type, *key_parts)

                cache_ttl = ttl or get_ttl(key_type)
                serialized = serialize_value(value)
                redis_client.set(cache_key, serialized, ttl=cache_ttl)
                logger.debug("Cache updated (write-through)", key=cache_key)

            return value

        return wrapper

    return decorator


class CacheService:
    """Centralized cache service."""

    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get value from cache."""
        cached = redis_client.get(key)
        if cached is not None:
            return deserialize_value(cached)
        return None

    @staticmethod
    def set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        serialized = serialize_value(value)
        return redis_client.set(key, serialized, ttl=ttl)

    @staticmethod
    def delete(key: str) -> bool:
        """Delete key from cache."""
        return redis_client.delete(key)

    @staticmethod
    def delete_pattern(pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            keys = redis_client.client.keys(pattern)
            if keys:
                return redis_client.client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning("Failed to delete pattern", pattern=pattern, error=str(e))
            return 0

    @staticmethod
    def invalidate(key_type: CacheKey, *parts: str) -> bool:
        """Invalidate cache for a specific key."""
        cache_key = make_cache_key(key_type, *parts)
        return CacheService.delete(cache_key)

    @staticmethod
    def invalidate_pattern(key_type: CacheKey, pattern: str = "*") -> int:
        """Invalidate all keys matching pattern for a key type."""
        full_pattern = f"{key_type.value}:{pattern}"
        return CacheService.delete_pattern(full_pattern)
