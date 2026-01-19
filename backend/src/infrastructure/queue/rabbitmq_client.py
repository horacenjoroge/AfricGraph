"""RabbitMQ message queue client."""
from typing import Optional
from kombu import Connection, Queue, Exchange
from kombu.exceptions import OperationalError

from src.config.settings import settings
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class RabbitMQClient:
    """RabbitMQ client for message queuing."""
    
    def __init__(self):
        """Initialize RabbitMQ connection."""
        self.connection: Optional[Connection] = None
        self._connection_url: str = ""
    
    def connect(self) -> None:
        """Establish connection to RabbitMQ."""
        try:
            self._connection_url = (
                f"amqp://{settings.rabbitmq_user}:{settings.rabbitmq_password}"
                f"@{settings.rabbitmq_host}:{settings.rabbitmq_port}"
                f"{settings.rabbitmq_vhost}"
            )
            
            self.connection = Connection(self._connection_url)
            self.connection.connect()
            
            logger.info("RabbitMQ connection established", host=settings.rabbitmq_host)
        except Exception as e:
            logger.error("Failed to connect to RabbitMQ", error=str(e))
            raise
    
    def close(self) -> None:
        """Close RabbitMQ connection."""
        if self.connection:
            self.connection.close()
            logger.info("RabbitMQ connection closed")
    
    def get_connection(self) -> Connection:
        """Get RabbitMQ connection."""
        if not self.connection:
            raise RuntimeError("RabbitMQ not initialized. Call connect() first.")
        return self.connection
    
    def create_queue(self, queue_name: str, exchange_name: str = "default") -> Queue:
        """Create a queue with exchange."""
        exchange = Exchange(exchange_name, type="direct")
        return Queue(queue_name, exchange=exchange, routing_key=queue_name)
    
    def health_check(self) -> bool:
        """Check if RabbitMQ connection is healthy."""
        try:
            if not self.connection:
                return False
            self.connection.ensure_connection(max_retries=1)
            return True
        except Exception as e:
            logger.error("RabbitMQ health check failed", error=str(e))
            return False


# Global RabbitMQ client instance
rabbitmq_client = RabbitMQClient()
