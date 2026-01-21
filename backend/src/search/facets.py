"""Faceted search with filters."""
from typing import Dict, List, Optional
from elasticsearch import ElasticsearchException

from src.infrastructure.search.elasticsearch_client import elasticsearch_client
from src.search.indexing import INDEX_BUSINESSES, INDEX_TRANSACTIONS
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def search_with_facets(
    index: str,
    query: str,
    filters: Optional[Dict] = None,
    facets: Optional[List[str]] = None,
    limit: int = 20,
    offset: int = 0,
) -> Dict:
    """
    Search with faceted filters.

    Args:
        index: Index to search
        query: Search query
        filters: Dict of field:value filters
        facets: List of fields to aggregate
        limit: Result limit
        offset: Result offset

    Returns:
        Search results with facet aggregations
    """
    try:
        # Build query
        must_clauses = []
        if query:
            must_clauses.append(
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["name^2", "description", "registration_number"],
                        "fuzziness": "AUTO",
                    }
                }
            )

        # Add filters
        filter_clauses = []
        if filters:
            for field, value in filters.items():
                if isinstance(value, list):
                    filter_clauses.append({"terms": {field: value}})
                else:
                    filter_clauses.append({"term": {field: value}})

        query_body = {"bool": {}}
        if must_clauses:
            query_body["bool"]["must"] = must_clauses
        if filter_clauses:
            query_body["bool"]["filter"] = filter_clauses

        # Build aggregations for facets
        aggs = {}
        if facets:
            for facet_field in facets:
                aggs[facet_field] = {"terms": {"field": f"{facet_field}.keyword", "size": 100}}

        search_body = {
            "query": query_body,
            "from": offset,
            "size": limit,
            "aggs": aggs,
        }

        response = elasticsearch_client.client.search(index=index, body=search_body)

        # Process results
        results = []
        for hit in response["hits"]["hits"]:
            results.append(
                {
                    "id": hit["_source"]["id"],
                    **hit["_source"],
                    "score": hit["_score"],
                }
            )

        # Process facets
        facet_results = {}
        if facets and "aggregations" in response:
            for facet_field in facets:
                if facet_field in response["aggregations"]:
                    buckets = response["aggregations"][facet_field]["buckets"]
                    facet_results[facet_field] = [
                        {"value": bucket["key"], "count": bucket["doc_count"]}
                        for bucket in buckets
                    ]

        return {
            "results": results,
            "total": response["hits"]["total"]["value"],
            "facets": facet_results,
            "query": query,
        }
    except Exception as e:
        logger.error(f"Faceted search failed: {e}")
        return {"results": [], "total": 0, "facets": {}, "query": query}


def search_businesses_with_facets(
    query: str,
    sector: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Dict:
    """Search businesses with sector facet."""
    filters = {}
    if sector:
        filters["sector"] = sector

    return search_with_facets(
        index=INDEX_BUSINESSES,
        query=query,
        filters=filters,
        facets=["sector"],
        limit=limit,
        offset=offset,
    )
