"""Elasticsearch search API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from src.search.fulltext import (
    search_businesses,
    search_people,
    search_transactions,
    search_invoices,
)
from src.search.facets import search_businesses_with_facets
from src.search.autocomplete import (
    autocomplete_businesses,
    autocomplete_people,
    get_search_suggestions,
)
from src.search.geospatial import search_nearby_businesses, search_within_bounding_box
from src.search.indexing import (
    index_business,
    index_person,
    index_transaction,
    index_invoice,
    delete_from_index,
    INDEX_BUSINESSES,
    INDEX_PEOPLE,
    INDEX_TRANSACTIONS,
    INDEX_INVOICES,
)

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/businesses")
def search_businesses_endpoint(
    q: str = Query(..., min_length=1),
    fuzzy: bool = Query(True),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Full-text search for businesses."""
    return search_businesses(query=q, fuzzy=fuzzy, limit=limit, offset=offset)


@router.get("/people")
def search_people_endpoint(
    q: str = Query(..., min_length=1),
    fuzzy: bool = Query(True),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Full-text search for people."""
    return search_people(query=q, fuzzy=fuzzy, limit=limit, offset=offset)


@router.get("/transactions")
def search_transactions_endpoint(
    q: str = Query(..., min_length=1),
    business_id: Optional[str] = None,
    fuzzy: bool = Query(True),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Full-text search for transactions."""
    return search_transactions(
        query=q, business_id=business_id, fuzzy=fuzzy, limit=limit, offset=offset
    )


@router.get("/invoices")
def search_invoices_endpoint(
    q: str = Query(..., min_length=1),
    business_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Full-text search for invoices."""
    return search_invoices(query=q, business_id=business_id, limit=limit, offset=offset)


@router.get("/businesses/facets")
def search_businesses_facets_endpoint(
    q: str = Query(""),
    sector: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Search businesses with faceted filters."""
    return search_businesses_with_facets(
        query=q, sector=sector, limit=limit, offset=offset
    )


@router.get("/autocomplete/businesses")
def autocomplete_businesses_endpoint(
    prefix: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
):
    """Autocomplete for business names."""
    return {"suggestions": autocomplete_businesses(prefix=prefix, limit=limit)}


@router.get("/autocomplete/people")
def autocomplete_people_endpoint(
    prefix: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
):
    """Autocomplete for people names."""
    return {"suggestions": autocomplete_people(prefix=prefix, limit=limit)}


@router.get("/suggestions")
def get_suggestions_endpoint(
    q: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=10),
):
    """Get search query suggestions (did you mean)."""
    return {"suggestions": get_search_suggestions(query=q, limit=limit)}


@router.get("/nearby")
def search_nearby_endpoint(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    distance_km: float = Query(10.0, ge=0.1, le=1000),
    q: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
):
    """Search for businesses near a location."""
    return search_nearby_businesses(
        latitude=latitude,
        longitude=longitude,
        distance_km=distance_km,
        query=q,
        limit=limit,
    )


@router.get("/bounding-box")
def search_bounding_box_endpoint(
    top_left_lat: float = Query(..., ge=-90, le=90),
    top_left_lon: float = Query(..., ge=-180, le=180),
    bottom_right_lat: float = Query(..., ge=-90, le=90),
    bottom_right_lon: float = Query(..., ge=-180, le=180),
    q: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
):
    """Search for businesses within a bounding box."""
    return search_within_bounding_box(
        top_left_lat=top_left_lat,
        top_left_lon=top_left_lon,
        bottom_right_lat=bottom_right_lat,
        bottom_right_lon=bottom_right_lon,
        query=q,
        limit=limit,
    )


@router.post("/index/business/{business_id}")
def index_business_endpoint(business_id: str, data: dict):
    """Index a business in Elasticsearch."""
    success = index_business(business_id, data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to index business")
    return {"status": "indexed", "business_id": business_id}


@router.post("/index/person/{person_id}")
def index_person_endpoint(person_id: str, data: dict):
    """Index a person in Elasticsearch."""
    success = index_person(person_id, data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to index person")
    return {"status": "indexed", "person_id": person_id}


@router.delete("/index/{index_name}/{doc_id}")
def delete_indexed_document(index_name: str, doc_id: str):
    """Delete a document from an index."""
    valid_indices = [INDEX_BUSINESSES, INDEX_PEOPLE, INDEX_TRANSACTIONS, INDEX_INVOICES]
    if index_name not in valid_indices:
        raise HTTPException(
            status_code=400, detail=f"Invalid index name. Must be one of: {valid_indices}"
        )

    success = delete_from_index(index_name, doc_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete document")
    return {"status": "deleted", "index": index_name, "doc_id": doc_id}
