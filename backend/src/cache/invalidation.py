"""Cache invalidation strategies."""
from typing import List, Optional

from src.cache.service import CacheService
from src.cache.config import CacheKey
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def invalidate_business_cache(business_id: str):
    """Invalidate all cache entries related to a business."""
    # Invalidate business data
    CacheService.invalidate(CacheKey.BUSINESS, business_id)

    # Invalidate risk scores
    CacheService.invalidate(CacheKey.RISK_SCORE, business_id)

    # Invalidate graph queries involving this business
    CacheService.invalidate_pattern(CacheKey.SUBGRAPH, f"*{business_id}*")
    CacheService.invalidate_pattern(CacheKey.PATH, f"*{business_id}*")

    # Invalidate API responses for this business
    CacheService.invalidate_pattern(CacheKey.API_RESPONSE, f"*business*{business_id}*")

    logger.info("Business cache invalidated", business_id=business_id)


def invalidate_user_cache(user_id: str):
    """Invalidate all cache entries related to a user."""
    # Invalidate user session
    CacheService.invalidate(CacheKey.USER_SESSION, user_id)

    # Invalidate permission decisions
    CacheService.invalidate_pattern(CacheKey.PERMISSION, f"*{user_id}*")

    logger.info("User cache invalidated", user_id=user_id)


def invalidate_graph_cache(node_id: Optional[str] = None):
    """Invalidate graph query cache."""
    if node_id:
        # Invalidate specific node's graph queries
        CacheService.invalidate_pattern(CacheKey.SUBGRAPH, f"*{node_id}*")
        CacheService.invalidate_pattern(CacheKey.PATH, f"*{node_id}*")
        CacheService.invalidate_pattern(CacheKey.GRAPH_QUERY, f"*{node_id}*")
    else:
        # Invalidate all graph queries
        CacheService.invalidate_pattern(CacheKey.GRAPH_QUERY)
        CacheService.invalidate_pattern(CacheKey.SUBGRAPH)
        CacheService.invalidate_pattern(CacheKey.PATH)

    logger.info("Graph cache invalidated", node_id=node_id)


def invalidate_risk_cache(business_id: Optional[str] = None):
    """Invalidate risk score cache."""
    if business_id:
        # The cache key includes function name, so we need to use pattern matching
        # Cache key format: risk_score:compute_business_risk:BIZ003
        CacheService.invalidate_pattern(CacheKey.RISK_SCORE, f"*{business_id}*")
    else:
        CacheService.invalidate_pattern(CacheKey.RISK_SCORE)

    logger.info("Risk cache invalidated", business_id=business_id)


def invalidate_on_transaction_update(business_id: str):
    """Invalidate relevant caches when a transaction is updated."""
    # Transactions affect cash flow, risk scores, and business data
    invalidate_business_cache(business_id)
    invalidate_risk_cache(business_id)
    invalidate_graph_cache()  # Graph structure may have changed

    logger.info("Cache invalidated on transaction update", business_id=business_id)


def invalidate_on_relationship_update(from_id: str, to_id: str):
    """Invalidate relevant caches when a relationship is updated."""
    # Relationships affect graph queries
    invalidate_graph_cache(from_id)
    invalidate_graph_cache(to_id)
    
    # May affect risk scores if ownership/supplier relationships change
    invalidate_risk_cache(from_id)
    invalidate_risk_cache(to_id)

    logger.info("Cache invalidated on relationship update", from_id=from_id, to_id=to_id)
