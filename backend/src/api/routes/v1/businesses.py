"""Business CRUD and search endpoints."""
from fastapi import APIRouter, HTTPException, Query
from starlette import status

from src.api.schemas.business import (
    BusinessCreate,
    BusinessResponse,
    BusinessSearchRequest,
    BusinessSearchResponse,
)
from src.api.services.business import create_business, get_business, search_businesses, update_business
from src.domain.models.business import Business
from src.graph.traversal import extract_subgraph
from src.infrastructure.database.neo4j_client import neo4j_client

router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.post("", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED)
def create_business_endpoint(body: BusinessCreate) -> BusinessResponse:
    """Create a new business."""
    business = Business(
        id=body.id,
        name=body.name,
        registration_number=body.registration_number,
        sector=body.sector,
    )
    create_business(business)
    return BusinessResponse.model_validate(business)


@router.get("/search", response_model=BusinessSearchResponse)
def search_businesses_endpoint(
    query: str = Query(None),
    sector: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> BusinessSearchResponse:
    """Search businesses."""
    # Debug: Check tenant context
    from src.tenancy.context import get_current_tenant
    tenant = get_current_tenant()
    from src.infrastructure.logging import get_logger
    logger = get_logger(__name__)
    logger.info(
        "Business search endpoint called",
        has_tenant=tenant is not None,
        tenant_id=tenant.tenant_id if tenant else None,
    )
    
    businesses, total = search_businesses(query=query, sector=sector, limit=limit, offset=offset)
    return BusinessSearchResponse(
        businesses=[BusinessResponse.model_validate(b) for b in businesses],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{business_id}", response_model=BusinessResponse)
def get_business_endpoint(business_id: str) -> BusinessResponse:
    """Get business by ID."""
    business = get_business(business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business '{business_id}' not found"
        )
    return BusinessResponse.model_validate(business)


@router.get("/{business_id}/graph")
def get_business_graph(
    business_id: str,
    max_hops: int = Query(2, ge=1, le=5),
    format: str = Query("json", pattern="^(json|visualization)$"),
) -> dict:
    """Get subgraph around a business."""
    # First verify business exists
    business = get_business(business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business '{business_id}' not found"
        )

    # Get node ID from Neo4j
    node = neo4j_client.find_node("Business", {"id": business_id})
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business node not found")

    # Use internal Neo4j ID for traversal
    node_id = str(neo4j_client.execute_cypher(
        "MATCH (b:Business {id: $business_id}) RETURN id(b) as node_id",
        {"business_id": business_id}
    )[0]["node_id"])

    subgraph = extract_subgraph(node_id, max_hops=max_hops)

    if format == "visualization":
        from src.graph.export import export_subgraph_for_visualization
        return export_subgraph_for_visualization(subgraph)
    return subgraph.model_dump(mode="json")
