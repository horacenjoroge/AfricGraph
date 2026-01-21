"""Unit tests for search functionality."""
import pytest
from unittest.mock import Mock, patch

from src.search.fulltext import search_businesses, search_people
from src.search.autocomplete import autocomplete_businesses


@pytest.mark.unit
class TestFullTextSearch:
    """Test full-text search."""

    @patch("src.search.fulltext.elasticsearch_client")
    def test_search_businesses(self, mock_es):
        """Test business search."""
        mock_es.search.return_value = {
            "hits": {
                "hits": [
                    {
                        "_source": {"id": "business-1", "name": "Test Business"},
                        "_score": 0.9,
                    }
                ],
                "total": {"value": 1},
            }
        }
        
        results = search_businesses("test")
        assert len(results) > 0
        assert results[0]["id"] == "business-1"

    @patch("src.search.fulltext.elasticsearch_client")
    def test_search_people(self, mock_es):
        """Test people search."""
        mock_es.search.return_value = {
            "hits": {
                "hits": [
                    {
                        "_source": {"id": "person-1", "name": "John Doe"},
                        "_score": 0.8,
                    }
                ],
                "total": {"value": 1},
            }
        }
        
        results = search_people("john")
        assert len(results) > 0


@pytest.mark.unit
class TestAutocomplete:
    """Test autocomplete functionality."""

    @patch("src.search.autocomplete.elasticsearch_client")
    def test_autocomplete_businesses(self, mock_es):
        """Test business autocomplete."""
        mock_es.search.return_value = {
            "hits": {
                "hits": [
                    {"_source": {"id": "business-1", "name": "Test Business"}},
                ],
                "total": {"value": 1},
            }
        }
        
        results = autocomplete_businesses("test")
        assert len(results) > 0
