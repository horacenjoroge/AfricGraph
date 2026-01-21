"""Autocomplete and search suggestions."""
from typing import List, Dict

from src.infrastructure.search.elasticsearch_client import elasticsearch_client
from src.search.indexing import INDEX_BUSINESSES, INDEX_PEOPLE
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def autocomplete_businesses(prefix: str, limit: int = 10) -> List[Dict]:
    """Autocomplete for business names."""
    try:
        search_body = {
            "suggest": {
                "business_suggest": {
                    "prefix": prefix,
                    "completion": {
                        "field": "name.suggest",
                        "size": limit,
                        "skip_duplicates": True,
                    },
                }
            }
        }

        response = elasticsearch_client.client.search(
            index=INDEX_BUSINESSES, body=search_body
        )

        suggestions = []
        if "suggest" in response and "business_suggest" in response["suggest"]:
            for option in response["suggest"]["business_suggest"][0]["options"]:
                suggestions.append(
                    {
                        "text": option["text"],
                        "score": option.get("_score", 0),
                        "source": option.get("_source", {}),
                    }
                )

        return suggestions
    except Exception as e:
        logger.error(f"Business autocomplete failed: {e}")
        return []


def autocomplete_people(prefix: str, limit: int = 10) -> List[Dict]:
    """Autocomplete for people names."""
    try:
        search_body = {
            "suggest": {
                "person_suggest": {
                    "prefix": prefix,
                    "completion": {
                        "field": "name.suggest",
                        "size": limit,
                        "skip_duplicates": True,
                    },
                }
            }
        }

        response = elasticsearch_client.client.search(
            index=INDEX_PEOPLE, body=search_body
        )

        suggestions = []
        if "suggest" in response and "person_suggest" in response["suggest"]:
            for option in response["suggest"]["person_suggest"][0]["options"]:
                suggestions.append(
                    {
                        "text": option["text"],
                        "score": option.get("_score", 0),
                        "source": option.get("_source", {}),
                    }
                )

        return suggestions
    except Exception as e:
        logger.error(f"People autocomplete failed: {e}")
        return []


def get_search_suggestions(query: str, limit: int = 5) -> List[str]:
    """Get search query suggestions (did you mean)."""
    try:
        search_body = {
            "suggest": {
                "text": query,
                "business_suggest": {
                    "phrase": {
                        "field": "name",
                        "gram_size": 2,
                        "max_errors": 2,
                        "confidence": 0.0,
                    }
                }
            }
        }

        response = elasticsearch_client.client.search(
            index=INDEX_BUSINESSES, body=search_body
        )

        suggestions = []
        if "suggest" in response and "business_suggest" in response["suggest"]:
            for suggestion in response["suggest"]["business_suggest"]:
                for option in suggestion.get("options", []):
                    suggestions.append(option["text"])

        return list(set(suggestions))[:limit]  # Remove duplicates
    except Exception as e:
        logger.error(f"Search suggestions failed: {e}")
        return []
