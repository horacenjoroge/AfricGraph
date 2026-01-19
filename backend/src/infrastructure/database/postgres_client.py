"""PostgreSQL database client."""
from typing import Optional
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager

from src.config.settings import settings
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class PostgresClient:
    """PostgreSQL client with connection pooling."""
    
    def __init__(self):
        """Initialize PostgreSQL engine."""
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
    
    def connect(self) -> None:
        """Establish connection to PostgreSQL database."""
        try:
            database_url = (
                f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
                f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
            )
            
            self.engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=False
            )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("PostgreSQL connection established", host=settings.postgres_host)
        except Exception as e:
            logger.error("Failed to connect to PostgreSQL", error=str(e))
            raise
    
    def close(self) -> None:
        """Close PostgreSQL engine."""
        if self.engine:
            self.engine.dispose()
            logger.info("PostgreSQL connection closed")
    
    @contextmanager
    def get_session(self):
        """Get a PostgreSQL session with automatic cleanup."""
        if not self.SessionLocal:
            raise RuntimeError("PostgreSQL not initialized. Call connect() first.")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """Check if PostgreSQL connection is healthy."""
        try:
            if not self.engine:
                return False
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error("PostgreSQL health check failed", error=str(e))
            return False


# Global PostgreSQL client instance
postgres_client = PostgresClient()
