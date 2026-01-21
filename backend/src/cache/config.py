"""Cache configuration and TTL settings."""
from enum import Enum
from typing import Optional


class CacheKey(Enum):
    """Cache key prefixes for different data types."""

    GRAPH_QUERY = "graph:query"
    PERMISSION = "permission"
    RISK_SCORE = "risk:score"
    USER_SESSION = "session"
    API_RESPONSE = "api:response"
    BUSINESS = "business"
    SUBGRAPH = "graph:subgraph"
    PATH = "graph:path"


class CacheTTL:
    """Time-to-live settings for different cache types (in seconds)."""

    # Graph query results: 5-30 minutes
    GRAPH_QUERY_SHORT = 5 * 60  # 5 minutes
    GRAPH_QUERY_MEDIUM = 15 * 60  # 15 minutes
    GRAPH_QUERY_LONG = 30 * 60  # 30 minutes

    # Permission decisions: 1 hour
    PERMISSION = 60 * 60  # 1 hour

    # Risk scores: 30 minutes
    RISK_SCORE = 30 * 60  # 30 minutes

    # User sessions: 24 hours
    USER_SESSION = 24 * 60 * 60  # 24 hours

    # API responses: variable
    API_RESPONSE_SHORT = 1 * 60  # 1 minute
    API_RESPONSE_MEDIUM = 5 * 60  # 5 minutes
    API_RESPONSE_LONG = 15 * 60  # 15 minutes

    # Business data: 10 minutes
    BUSINESS = 10 * 60  # 10 minutes

    # Subgraph: 15 minutes
    SUBGRAPH = 15 * 60  # 15 minutes

    # Path queries: 10 minutes
    PATH = 10 * 60  # 10 minutes


def get_ttl(key_type: CacheKey, default: Optional[int] = None) -> int:
    """Get TTL for a cache key type."""
    ttl_map = {
        CacheKey.GRAPH_QUERY: CacheTTL.GRAPH_QUERY_MEDIUM,
        CacheKey.PERMISSION: CacheTTL.PERMISSION,
        CacheKey.RISK_SCORE: CacheTTL.RISK_SCORE,
        CacheKey.USER_SESSION: CacheTTL.USER_SESSION,
        CacheKey.API_RESPONSE: CacheTTL.API_RESPONSE_MEDIUM,
        CacheKey.BUSINESS: CacheTTL.BUSINESS,
        CacheKey.SUBGRAPH: CacheTTL.SUBGRAPH,
        CacheKey.PATH: CacheTTL.PATH,
    }
    return ttl_map.get(key_type, default or CacheTTL.API_RESPONSE_MEDIUM)
