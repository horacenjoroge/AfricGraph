"""Elasticsearch client."""
from typing import Optional
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError, ConnectionError as ESConnectionError

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
            # For Elasticsearch 8.x, use compatible client settings
            self.client = Elasticsearch(
                [f"http://{settings.elasticsearch_host}:{settings.elasticsearch_port}"],
                request_timeout=30,
                verify_certs=False,
                ssl_show_warn=False,
            )
            
            # Use info() instead of ping() to get better error messages
            try:
                info = self.client.info()
                logger.info(
                    "Elasticsearch connection established",
                    host=settings.elasticsearch_host,
                    version=info.get("version", {}).get("number", "unknown"),
                )
            except RequestError as e:
                logger.error("Elasticsearch request failed", error=str(e), status_code=getattr(e, 'status_code', None))
                raise ConnectionError(f"Elasticsearch connection failed: {e}")
            except Exception as e:
                logger.error("Elasticsearch connection error", error=str(e))
                raise ConnectionError(f"Elasticsearch connection failed: {e}")
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
