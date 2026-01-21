"""Unit tests for cache service."""
import pytest
from unittest.mock import Mock, patch

from src.cache.service import CacheService, cache_aside, CacheKey
from src.cache.config import CacheTTL


@pytest.mark.unit
class TestCacheService:
    """Test cache service."""

    @patch("src.cache.service.redis_client")
    def test_cache_get_hit(self, mock_redis):
        """Test cache get with hit."""
        mock_redis.get.return_value = '{"key": "value"}'
        
        result = CacheService.get("test:key")
        assert result == {"key": "value"}
        mock_redis.get.assert_called_once_with("test:key")

    @patch("src.cache.service.redis_client")
    def test_cache_get_miss(self, mock_redis):
        """Test cache get with miss."""
        mock_redis.get.return_value = None
        
        result = CacheService.get("test:key")
        assert result is None

    @patch("src.cache.service.redis_client")
    def test_cache_set(self, mock_redis):
        """Test cache set."""
        mock_redis.set.return_value = True
        
        result = CacheService.set("test:key", {"key": "value"}, ttl=3600)
        assert result is True
        mock_redis.set.assert_called_once()

    @patch("src.cache.service.redis_client")
    def test_cache_delete(self, mock_redis):
        """Test cache delete."""
        mock_redis.delete.return_value = True
        
        result = CacheService.delete("test:key")
        assert result is True
        mock_redis.delete.assert_called_once_with("test:key")


@pytest.mark.unit
class TestCacheDecorator:
    """Test cache decorator."""

    @cache_aside(CacheKey.RISK_SCORE, ttl=CacheTTL.RISK_SCORE)
    def cached_function(self, business_id: str):
        """Test function for caching."""
        return {"business_id": business_id, "score": 75.0}

    @patch("src.cache.service.CacheService")
    def test_cache_aside_hit(self, mock_cache_service):
        """Test cache-aside pattern with hit."""
        mock_cache_service.get.return_value = {"cached": "value"}
        
        result = self.cached_function("business-123")
        assert result == {"cached": "value"}

    @patch("src.cache.service.CacheService")
    def test_cache_aside_miss(self, mock_cache_service):
        """Test cache-aside pattern with miss."""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        result = self.cached_function("business-123")
        assert result["business_id"] == "business-123"
        mock_cache_service.set.assert_called_once()
