"""Redis cache client."""
from typing import Optional, Any
import redis
from redis.exceptions import ConnectionError, TimeoutError

from src.config.settings import settings
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Redis client with connection pooling."""
    
    def __init__(self):
        """Initialize Redis connection pool."""
        self.client: Optional[redis.Redis] = None
    
    def connect(self) -> None:
        """Establish connection to Redis."""
        try:
            self.client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.client.ping()
            
            logger.info("Redis connection established", host=settings.redis_host)
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    def close(self) -> None:
        """Close Redis connection."""
        if self.client:
            self.client.close()
            logger.info("Redis connection closed")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            return self.client.get(key)
        except (ConnectionError, TimeoutError) as e:
            logger.warning("Redis get operation failed", key=key, error=str(e))
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        try:
            if ttl:
                return self.client.setex(key, ttl, value)
            else:
                return self.client.set(key, value)
        except (ConnectionError, TimeoutError) as e:
            logger.warning("Redis set operation failed", key=key, error=str(e))
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            return bool(self.client.delete(key))
        except (ConnectionError, TimeoutError) as e:
            logger.warning("Redis delete operation failed", key=key, error=str(e))
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return bool(self.client.exists(key))
        except (ConnectionError, TimeoutError) as e:
            logger.warning("Redis exists operation failed", key=key, error=str(e))
            return False
    
    def health_check(self) -> bool:
        """Check if Redis connection is healthy."""
        try:
            if not self.client:
                return False
            self.client.ping()
            return True
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
            return False


# Global Redis client instance
redis_client = RedisClient()
