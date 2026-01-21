"""Cache warming strategies."""
from typing import List, Optional
import asyncio

from src.infrastructure.database.neo4j_client import neo4j_client
from src.cache.service import CacheService
from src.cache.config import CacheKey, CacheTTL
from src.risk.scoring.engine import compute_business_risk
from src.api.services.business import get_business
from src.graph.traversal import extract_subgraph
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def warm_risk_scores(business_ids: Optional[List[str]] = None, limit: int = 100):
    """Warm cache with risk scores for businesses."""
    if business_ids is None:
        # Get top businesses by transaction volume
        query = """
        MATCH (b:Business)<-[:INVOLVES]-(t:Transaction)
        WITH b, count(t) as tx_count
        ORDER BY tx_count DESC
        LIMIT $limit
        RETURN b.id as business_id
        """
        rows = neo4j_client.execute_cypher(query, {"limit": limit})
        business_ids = [row["business_id"] for row in rows]

    warmed = 0
    for business_id in business_ids:
        try:
            # Compute and cache risk score
            risk_result = compute_business_risk(business_id)
            cache_key = make_cache_key(CacheKey.RISK_SCORE, business_id)
            CacheService.set(
                cache_key,
                {
                    "score": risk_result.score,
                    "factors": [f.model_dump() for f in risk_result.factors],
                },
                ttl=CacheTTL.RISK_SCORE,
            )
            warmed += 1
        except Exception as e:
            logger.warning(f"Failed to warm risk score for {business_id}: {e}")

    logger.info(f"Warmed {warmed} risk scores")
    return warmed


def warm_business_data(business_ids: Optional[List[str]] = None, limit: int = 100):
    """Warm cache with business data."""
    if business_ids is None:
        query = """
        MATCH (b:Business)
        RETURN b.id as business_id
        ORDER BY b.id
        LIMIT $limit
        """
        rows = neo4j_client.execute_cypher(query, {"limit": limit})
        business_ids = [row["business_id"] for row in rows]

    warmed = 0
    for business_id in business_ids:
        try:
            business = get_business(business_id)
            if business:
                cache_key = make_cache_key(CacheKey.BUSINESS, business_id)
                CacheService.set(
                    cache_key, business.model_dump(), ttl=CacheTTL.BUSINESS
                )
                warmed += 1
        except Exception as e:
            logger.warning(f"Failed to warm business data for {business_id}: {e}")

    logger.info(f"Warmed {warmed} business records")
    return warmed


def warm_graph_queries(node_ids: Optional[List[str]] = None, limit: int = 50):
    """Warm cache with common graph queries."""
    if node_ids is None:
        # Get businesses with most connections
        query = """
        MATCH (b:Business)-[r]-(n)
        WITH b, count(r) as connection_count
        ORDER BY connection_count DESC
        LIMIT $limit
        RETURN id(b) as node_id, b.id as business_id
        """
        rows = neo4j_client.execute_cypher(query, {"limit": limit})
        node_ids = [str(row["node_id"]) for row in rows]

    warmed = 0
    for node_id in node_ids:
        try:
            # Warm subgraph queries
            subgraph = extract_subgraph(node_id, max_hops=2)
            cache_key = make_cache_key(CacheKey.SUBGRAPH, node_id, "2")
            CacheService.set(
                cache_key, subgraph.model_dump(mode="json"), ttl=CacheTTL.SUBGRAPH
            )
            warmed += 1
        except Exception as e:
            logger.warning(f"Failed to warm graph query for {node_id}: {e}")

    logger.info(f"Warmed {warmed} graph queries")
    return warmed


def warm_all(risk_limit: int = 100, business_limit: int = 100, graph_limit: int = 50):
    """Warm all caches."""
    logger.info("Starting cache warming")
    
    total_warmed = 0
    total_warmed += warm_risk_scores(limit=risk_limit)
    total_warmed += warm_business_data(limit=business_limit)
    total_warmed += warm_graph_queries(limit=graph_limit)
    
    logger.info(f"Cache warming complete: {total_warmed} items warmed")
    return total_warmed


# Import needed for make_cache_key
from src.cache.service import make_cache_key
