"""Relationship search endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from src.graph.common_ownership import find_common_owners, find_ownership_path
from src.graph.relationship_search import find_connections
from src.graph.shared_directors import find_director_network_path, find_shared_directors

router = APIRouter(prefix="/relationships", tags=["relationships"])


@router.get("/connect/{entity_a_id}/{entity_b_id}")
def get_connections(
    entity_a_id: str,
    entity_b_id: str,
    max_depth: int = Query(5, ge=1, le=10),
    include_all_paths: bool = Query(False),
) -> dict:
    """Find how two entities are connected."""
    connections = find_connections(entity_a_id, entity_b_id, max_depth, include_all_paths)
    return {
        "entity_a_id": entity_a_id,
        "entity_b_id": entity_b_id,
        "connections": [c.to_dict() for c in connections],
        "count": len(connections),
    }


@router.get("/common-ownership/{entity_a_id}/{entity_b_id}")
def get_common_ownership_endpoint(entity_a_id: str, entity_b_id: str) -> dict:
    """Find common owners between two entities."""
    return find_common_owners(entity_a_id, entity_b_id)


@router.get("/shared-directors/{entity_a_id}/{entity_b_id}")
def get_shared_directors_endpoint(entity_a_id: str, entity_b_id: str) -> dict:
    """Find shared directors between two businesses."""
    return find_shared_directors(entity_a_id, entity_b_id)
