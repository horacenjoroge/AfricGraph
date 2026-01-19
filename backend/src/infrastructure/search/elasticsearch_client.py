"""Elasticsearch client."""
from typing import Optional
from elasticsearch import Elasticsearch

from src.config.settings import settings
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class ElasticsearchClient:
    """Elasticsearch client for search and indexing."""

    def __init__(self):
        """Initialize Elasticsearch client."""
        self.client: Optional[Elasticsearch] = None

    def connect(self) -> None:
        """Establish connection to Elasticsearch."""
        try:
            self.client = Elasticsearch(
                [f"http://{settings.elasticsearch_host}:{settings.elasticsearch_port}"],
                request_timeout=10,
            )
            if not self.client.ping():
                raise ConnectionError("Elasticsearch ping failed")
            logger.info(
                "Elasticsearch connection established",
                host=settings.elasticsearch_host,
            )
        except Exception as e:
            logger.error("Failed to connect to Elasticsearch", error=str(e))
            raise

    def close(self) -> None:
        """Close Elasticsearch connection."""
        if self.client:
            self.client.close()
            logger.info("Elasticsearch connection closed")

    def health_check(self) -> bool:
        """Check if Elasticsearch connection is healthy."""
        try:
            if not self.client:
                return False
            return bool(self.client.ping())
        except Exception as e:
            logger.error("Elasticsearch health check failed", error=str(e))
            return False


elasticsearch_client = ElasticsearchClient()
