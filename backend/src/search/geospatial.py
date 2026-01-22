"""Geospatial search functionality."""
from typing import List, Dict, Optional
from elasticsearch.exceptions import RequestError, ConnectionError as ESConnectionError

from src.infrastructure.search.elasticsearch_client import elasticsearch_client
from src.search.indexing import INDEX_BUSINESSES
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def search_nearby_businesses(
    latitude: float,
    longitude: float,
    distance_km: float = 10.0,
    query: Optional[str] = None,
    limit: int = 20,
) -> Dict:
    """
    Search for businesses near a location.

    Args:
        latitude: Latitude of center point
        longitude: Longitude of center point
        distance_km: Search radius in kilometers
        query: Optional text query to filter results
        limit: Maximum number of results

    Returns:
        Search results with distance information
    """
    try:
        # Build query
        must_clauses = [
            {
                "geo_distance": {
                    "distance": f"{distance_km}km",
                    "location": {"lat": latitude, "lon": longitude},
                }
            }
        ]

        if query:
            must_clauses.append(
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["name^2", "sector"],
                        "fuzziness": "AUTO",
                    }
                }
            )

        search_body = {
            "query": {"bool": {"must": must_clauses}},
            "size": limit,
            "sort": [
                {
                    "_geo_distance": {
                        "location": {"lat": latitude, "lon": longitude},
                        "order": "asc",
                        "unit": "km",
                    }
                }
            ],
        }

        response = elasticsearch_client.client.search(
            index=INDEX_BUSINESSES, body=search_body
        )

        results = []
        for hit in response["hits"]["hits"]:
            # Calculate distance
            distance = None
            if "sort" in hit:
                distance = hit["sort"][0]  # First sort value is distance

            results.append(
                {
                    "id": hit["_source"]["id"],
                    "name": hit["_source"]["name"],
                    "sector": hit["_source"].get("sector"),
                    "location": hit["_source"].get("location"),
                    "distance_km": distance,
                    "score": hit["_score"],
                }
            )

        return {
            "results": results,
            "total": response["hits"]["total"]["value"],
            "center": {"latitude": latitude, "longitude": longitude},
            "radius_km": distance_km,
        }
    except Exception as e:
        logger.error(f"Geospatial search failed: {e}")
        return {"results": [], "total": 0}


def search_within_bounding_box(
    top_left_lat: float,
    top_left_lon: float,
    bottom_right_lat: float,
    bottom_right_lon: float,
    query: Optional[str] = None,
    limit: int = 20,
) -> Dict:
    """
    Search for businesses within a bounding box.

    Args:
        top_left_lat: Top-left corner latitude
        top_left_lon: Top-left corner longitude
        bottom_right_lat: Bottom-right corner latitude
        bottom_right_lon: Bottom-right corner longitude
        query: Optional text query
        limit: Maximum number of results

    Returns:
        Search results
    """
    try:
        must_clauses = [
            {
                "geo_bounding_box": {
                    "location": {
                        "top_left": {"lat": top_left_lat, "lon": top_left_lon},
                        "bottom_right": {
                            "lat": bottom_right_lat,
                            "lon": bottom_right_lon,
                        },
                    }
                }
            }
        ]

        if query:
            must_clauses.append(
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["name^2", "sector"],
                    }
                }
            )

        search_body = {
            "query": {"bool": {"must": must_clauses}},
            "size": limit,
        }

        response = elasticsearch_client.client.search(
            index=INDEX_BUSINESSES, body=search_body
        )

        results = []
        for hit in response["hits"]["hits"]:
            results.append(
                {
                    "id": hit["_source"]["id"],
                    "name": hit["_source"]["name"],
                    "sector": hit["_source"].get("sector"),
                    "location": hit["_source"].get("location"),
                    "score": hit["_score"],
                }
            )

        return {
            "results": results,
            "total": response["hits"]["total"]["value"],
        }
    except Exception as e:
        logger.error(f"Bounding box search failed: {e}")
        return {"results": [], "total": 0}
