"""Cache management API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from src.cache.service import CacheService
from src.cache.config import CacheKey
from src.cache.warming import warm_all, warm_risk_scores, warm_business_data, warm_graph_queries
from src.cache.invalidation import (
    invalidate_business_cache,
    invalidate_user_cache,
    invalidate_graph_cache,
    invalidate_risk_cache,
)

router = APIRouter(prefix="/cache", tags=["cache"])


@router.post("/warm")
def warm_cache(
    risk_limit: int = Query(100, ge=1, le=1000),
    business_limit: int = Query(100, ge=1, le=1000),
    graph_limit: int = Query(50, ge=1, le=500),
):
    """Warm cache with frequently accessed data."""
    try:
        total = warm_all(
            risk_limit=risk_limit,
            business_limit=business_limit,
            graph_limit=graph_limit,
        )
        return {
            "status": "success",
            "items_warmed": total,
            "risk_limit": risk_limit,
            "business_limit": business_limit,
            "graph_limit": graph_limit,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache warming failed: {str(e)}")


@router.post("/warm/risk")
def warm_risk_cache(limit: int = Query(100, ge=1, le=1000)):
    """Warm risk score cache."""
    try:
        count = warm_risk_scores(limit=limit)
        return {"status": "success", "items_warmed": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to warm risk cache: {str(e)}")


@router.post("/warm/business")
def warm_business_cache(limit: int = Query(100, ge=1, le=1000)):
    """Warm business data cache."""
    try:
        count = warm_business_data(limit=limit)
        return {"status": "success", "items_warmed": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to warm business cache: {str(e)}")


@router.post("/warm/graph")
def warm_graph_cache(limit: int = Query(50, ge=1, le=500)):
    """Warm graph query cache."""
    try:
        count = warm_graph_queries(limit=limit)
        return {"status": "success", "items_warmed": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to warm graph cache: {str(e)}")


@router.delete("/invalidate/business/{business_id}")
def invalidate_business(business_id: str):
    """Invalidate all cache entries for a business."""
    try:
        invalidate_business_cache(business_id)
        return {"status": "success", "business_id": business_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Invalidation failed: {str(e)}")


@router.delete("/invalidate/user/{user_id}")
def invalidate_user(user_id: str):
    """Invalidate all cache entries for a user."""
    try:
        invalidate_user_cache(user_id)
        return {"status": "success", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Invalidation failed: {str(e)}")


@router.delete("/invalidate/graph")
def invalidate_graph(node_id: Optional[str] = None):
    """Invalidate graph query cache."""
    try:
        invalidate_graph_cache(node_id)
        return {"status": "success", "node_id": node_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Invalidation failed: {str(e)}")


@router.delete("/invalidate/risk")
def invalidate_risk(business_id: Optional[str] = None):
    """Invalidate risk score cache."""
    try:
        invalidate_risk_cache(business_id)
        return {"status": "success", "business_id": business_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Invalidation failed: {str(e)}")


@router.delete("/clear")
def clear_cache():
    """Clear all cache (use with caution)."""
    try:
        # Clear all cache keys (this is destructive)
        from src.infrastructure.cache.redis_client import redis_client
        redis_client.client.flushdb()
        return {"status": "success", "message": "All cache cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")


@router.get("/stats")
def get_cache_stats():
    """Get cache statistics."""
    try:
        from src.infrastructure.cache.redis_client import redis_client
        
        info = redis_client.client.info("stats")
        keyspace = redis_client.client.info("keyspace")
        
        return {
            "status": "success",
            "stats": {
                "total_keys": redis_client.client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0)
                    / (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
                    * 100
                ),
                "keyspace": keyspace,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
