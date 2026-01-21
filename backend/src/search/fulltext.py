"""Full-text search with fuzzy matching."""
from typing import List, Dict, Optional
from elasticsearch import ElasticsearchException

from src.infrastructure.search.elasticsearch_client import elasticsearch_client
from src.search.indexing import (
    INDEX_BUSINESSES,
    INDEX_PEOPLE,
    INDEX_TRANSACTIONS,
    INDEX_INVOICES,
)
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def search_businesses(
    query: str,
    fuzzy: bool = True,
    fuzziness: str = "AUTO",
    limit: int = 20,
    offset: int = 0,
) -> Dict:
    """Full-text search for businesses with fuzzy matching."""
    try:
        search_body = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "match": {
                                "name": {
                                    "query": query,
                                    "fuzziness": fuzziness if fuzzy else "0",
                                    "boost": 2.0,
                                }
                            }
                        },
                        {
                            "match": {
                                "registration_number": {
                                    "query": query,
                                    "fuzziness": fuzziness if fuzzy else "0",
                                }
                            }
                        },
                        {
                            "wildcard": {"name.keyword": f"*{query}*"},
                        },
                    ]
                }
            },
            "from": offset,
            "size": limit,
            "highlight": {
                "fields": {
                    "name": {},
                    "registration_number": {},
                }
            },
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
                    "registration_number": hit["_source"].get("registration_number"),
                    "sector": hit["_source"].get("sector"),
                    "score": hit["_score"],
                    "highlight": hit.get("highlight", {}),
                }
            )

        return {
            "results": results,
            "total": response["hits"]["total"]["value"],
            "query": query,
        }
    except Exception as e:
        logger.error(f"Business search failed: {e}")
        return {"results": [], "total": 0, "query": query}


def search_people(
    query: str,
    fuzzy: bool = True,
    limit: int = 20,
    offset: int = 0,
) -> Dict:
    """Full-text search for people with fuzzy matching."""
    try:
        search_body = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "match": {
                                "name": {
                                    "query": query,
                                    "fuzziness": "AUTO" if fuzzy else "0",
                                    "boost": 2.0,
                                }
                            }
                        },
                        {
                            "match": {"email": {"query": query, "fuzziness": "0"}},
                        },
                        {
                            "match": {"phone": {"query": query, "fuzziness": "0"}},
                        },
                    ]
                }
            },
            "from": offset,
            "size": limit,
        }

        response = elasticsearch_client.client.search(
            index=INDEX_PEOPLE, body=search_body
        )

        results = []
        for hit in response["hits"]["hits"]:
            results.append(
                {
                    "id": hit["_source"]["id"],
                    "name": hit["_source"]["name"],
                    "email": hit["_source"].get("email"),
                    "phone": hit["_source"].get("phone"),
                    "score": hit["_score"],
                }
            )

        return {
            "results": results,
            "total": response["hits"]["total"]["value"],
            "query": query,
        }
    except Exception as e:
        logger.error(f"People search failed: {e}")
        return {"results": [], "total": 0, "query": query}


def search_transactions(
    query: str,
    business_id: Optional[str] = None,
    fuzzy: bool = True,
    limit: int = 20,
    offset: int = 0,
) -> Dict:
    """Full-text search for transactions."""
    try:
        must_clauses = [
            {
                "match": {
                    "description": {
                        "query": query,
                        "fuzziness": "AUTO" if fuzzy else "0",
                    }
                }
            }
        ]

        if business_id:
            must_clauses.append({"term": {"business_id": business_id}})

        search_body = {
            "query": {"bool": {"must": must_clauses}},
            "from": offset,
            "size": limit,
            "sort": [{"timestamp": {"order": "desc"}}],
        }

        response = elasticsearch_client.client.search(
            index=INDEX_TRANSACTIONS, body=search_body
        )

        results = []
        for hit in response["hits"]["hits"]:
            results.append(
                {
                    "id": hit["_source"]["id"],
                    "description": hit["_source"]["description"],
                    "amount": hit["_source"].get("amount"),
                    "business_id": hit["_source"].get("business_id"),
                    "timestamp": hit["_source"].get("timestamp"),
                    "score": hit["_score"],
                }
            )

        return {
            "results": results,
            "total": response["hits"]["total"]["value"],
            "query": query,
        }
    except Exception as e:
        logger.error(f"Transaction search failed: {e}")
        return {"results": [], "total": 0, "query": query}


def search_invoices(
    query: str,
    business_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Dict:
    """Full-text search for invoices."""
    try:
        must_clauses = [
            {
                "bool": {
                    "should": [
                        {
                            "match": {
                                "invoice_number": {
                                    "query": query,
                                    "fuzziness": "AUTO",
                                }
                            }
                        },
                        {"wildcard": {"invoice_number.keyword": f"*{query}*"}},
                    ]
                }
            }
        ]

        if business_id:
            must_clauses.append({"term": {"business_id": business_id}})

        search_body = {
            "query": {"bool": {"must": must_clauses}},
            "from": offset,
            "size": limit,
        }

        response = elasticsearch_client.client.search(
            index=INDEX_INVOICES, body=search_body
        )

        results = []
        for hit in response["hits"]["hits"]:
            results.append(
                {
                    "id": hit["_source"]["id"],
                    "invoice_number": hit["_source"]["invoice_number"],
                    "business_id": hit["_source"].get("business_id"),
                    "amount": hit["_source"].get("amount"),
                    "status": hit["_source"].get("status"),
                    "score": hit["_score"],
                }
            )

        return {
            "results": results,
            "total": response["hits"]["total"]["value"],
            "query": query,
        }
    except Exception as e:
        logger.error(f"Invoice search failed: {e}")
        return {"results": [], "total": 0, "query": query}
