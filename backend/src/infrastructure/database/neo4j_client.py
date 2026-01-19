"""Neo4j database client with connection pooling."""
from typing import Dict, List, Optional, Any
from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import ServiceUnavailable, TransientError
import time
from contextlib import contextmanager

from src.config.settings import settings
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class Neo4jClient:
    """Neo4j client with connection pooling and retry logic."""
    
    def __init__(self):
        """Initialize Neo4j driver with connection pooling."""
        self.driver: Optional[Driver] = None
        self._max_retries = 3
        self._retry_delay = 1
    
    def connect(self) -> None:
        """Establish connection to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )
            # Verify connectivity
            self.driver.verify_connectivity()
            logger.info("Neo4j connection established", uri=settings.neo4j_uri)
        except Exception as e:
            logger.error("Failed to connect to Neo4j", error=str(e))
            raise
    
    def close(self) -> None:
        """Close Neo4j driver connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    @contextmanager
    def get_session(self, access_mode=None):
        """Get a Neo4j session with automatic cleanup."""
        if not self.driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")
        
        session = self.driver.session(access_mode=access_mode)
        try:
            yield session
        finally:
            session.close()
    
    def _execute_with_retry(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry logic."""
        last_exception = None
        for attempt in range(self._max_retries):
            try:
                return func(*args, **kwargs)
            except (ServiceUnavailable, TransientError) as e:
                last_exception = e
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (2 ** attempt)
                    logger.warning(
                        "Neo4j operation failed, retrying",
                        attempt=attempt + 1,
                        delay=delay,
                        error=str(e)
                    )
                    time.sleep(delay)
                else:
                    logger.error("Neo4j operation failed after retries", error=str(e))
            except Exception as e:
                logger.error("Neo4j operation failed", error=str(e))
                raise
        
        if last_exception:
            raise last_exception
    
    def execute_cypher(self, query: str, parameters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results."""
        if parameters is None:
            parameters = {}
        
        def _execute():
            with self.get_session() as session:
                result = session.run(query, parameters)
                return [record.data() for record in result]
        
        return self._execute_with_retry(_execute)
    
    def create_node(self, label: str, properties: Dict[str, Any]) -> str:
        """Create a node and return its ID."""
        query = f"CREATE (n:{label} $properties) RETURN id(n) as node_id"
        
        def _execute():
            with self.get_session() as session:
                result = session.run(query, {"properties": properties})
                record = result.single()
                return str(record["node_id"])
        
        node_id = self._execute_with_retry(_execute)
        logger.debug("Node created", label=label, node_id=node_id)
        return node_id
    
    def find_node(self, label: str, filters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Find a single node by label and optional filters."""
        if filters is None:
            filters = {}
        
        conditions = " AND ".join([f"n.{k} = ${k}" for k in filters.keys()])
        where_clause = f"WHERE {conditions}" if conditions else ""
        query = f"MATCH (n:{label}) {where_clause} RETURN n LIMIT 1"
        
        def _execute():
            with self.get_session() as session:
                result = session.run(query, filters)
                record = result.single()
                if record:
                    node = record["n"]
                    return dict(node)
                return None
        
        return self._execute_with_retry(_execute)
    
    def create_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create a relationship between two nodes."""
        if properties is None:
            properties = {}
        
        query = (
            f"MATCH (a), (b) "
            f"WHERE id(a) = $from_id AND id(b) = $to_id "
            f"CREATE (a)-[r:{rel_type} $properties]->(b) "
            f"RETURN r"
        )
        
        def _execute():
            with self.get_session() as session:
                session.run(query, {
                    "from_id": int(from_id),
                    "to_id": int(to_id),
                    "properties": properties
                })
        
        self._execute_with_retry(_execute)
        logger.debug(
            "Relationship created",
            from_id=from_id,
            to_id=to_id,
            rel_type=rel_type
        )
    
    def health_check(self) -> bool:
        """Check if Neo4j connection is healthy."""
        try:
            if not self.driver:
                return False
            self.driver.verify_connectivity()
            return True
        except Exception as e:
            logger.error("Neo4j health check failed", error=str(e))
            return False


# Global Neo4j client instance
neo4j_client = Neo4jClient()
