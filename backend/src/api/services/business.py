"""Business service layer."""
from typing import List, Optional

from src.domain.models.business import Business
from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.logging import get_logger
from src.cache.integrations import cached_business
from src.cache.service import make_cache_key, CacheService
from src.cache.config import CacheKey, CacheTTL
from src.cache.invalidation import invalidate_business_cache
from src.search.sync import sync_business_to_elasticsearch

logger = get_logger(__name__)


def create_business(business: Business) -> str:
    """Create a business node in Neo4j and index in Elasticsearch."""
    props = business.to_node_properties()
    node_id = neo4j_client.merge_node("Business", business.id, props)
    
    # Index in Elasticsearch
    try:
        sync_business_to_elasticsearch(business.id)
    except Exception as e:
        logger.warning(f"Failed to index business in Elasticsearch: {e}")
    
    logger.info("Business created", business_id=business.id, node_id=node_id)
    return node_id


@cached_business
def get_business(business_id: str) -> Optional[Business]:
    """Get business by ID (cached)."""
    node = neo4j_client.find_node("Business", {"id": business_id})
    if not node:
        return None
    return Business.from_node_properties(node)


def update_business(business_id: str, updates: dict) -> Optional[Business]:
    """Update business properties (invalidates cache)."""
    existing = get_business(business_id)
    if not existing:
        return None

    updated_props = {**existing.model_dump(), **updates}
    updated_props = {k: v for k, v in updated_props.items() if v is not None}
    updated = Business.model_validate(updated_props)
    updated.id = business_id

    props = updated.to_node_properties()
    neo4j_client.merge_node("Business", business_id, props)
    
    # Invalidate cache
    invalidate_business_cache(business_id)
    
    # Re-index in Elasticsearch
    try:
        sync_business_to_elasticsearch(business_id)
    except Exception as e:
        logger.warning(f"Failed to re-index business in Elasticsearch: {e}")
    
    logger.info("Business updated", business_id=business_id)
    return updated


def search_businesses(
    query: Optional[str] = None,
    sector: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[List[Business], int]:
    """Search businesses with filters."""
    conditions = []
    params = {"limit": limit, "offset": offset}

    if query:
        conditions.append("(b.name CONTAINS $query OR b.id CONTAINS $query)")
        params["query"] = query
    if sector:
        conditions.append("b.sector = $sector")
        params["sector"] = sector

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Get total count
    count_query = f"MATCH (b:Business) WHERE {where_clause} RETURN count(b) as total"
    count_rows = neo4j_client.execute_cypher(count_query, params)
    total = count_rows[0]["total"] if count_rows else 0

    # Get results
    search_query = f"""
    MATCH (b:Business)
    WHERE {where_clause}
    RETURN b
    ORDER BY b.name ASC
    SKIP $offset LIMIT $limit
    """
    rows = neo4j_client.execute_cypher(search_query, params)

    businesses = []
    for row in rows:
        node_props = dict(row["b"])
        businesses.append(Business.from_node_properties(node_props))

    return businesses, total
