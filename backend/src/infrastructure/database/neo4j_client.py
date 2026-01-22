"""Neo4j database client with connection pooling, CRUD, transactions, retry, streaming, timeout, and deadlock handling."""
from typing import Dict, List, Optional, Any, Callable, Iterator, TYPE_CHECKING
from contextlib import contextmanager
import time

from neo4j import GraphDatabase, Driver, Query
from neo4j.exceptions import ServiceUnavailable, TransientError

from src.config.settings import settings
from src.infrastructure.logging import get_logger
import src.infrastructure.database.cypher_queries as cypher_queries
from src.domain.ontology import NODE_LABELS, RELATIONSHIP_TYPES
from src.security.query_rewriter import (
    rewrite_node_query_with_permissions,
    rewrite_traversal_with_permissions,
)
from src.monitoring.instrumentation import track_neo4j_query

if TYPE_CHECKING:
    from src.security.abac import SubjectAttributes, Action

logger = get_logger(__name__)

DEADLOCK_INDICATORS = ("deadlock", "lock", "lockexception", "acquirelock")


class Neo4jClient:
    """Neo4j client with connection pooling, retry, CRUD, traversal, batch, and pagination."""

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
                connection_acquisition_timeout=60,
            )
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

    @staticmethod
    def _is_deadlock(e: Exception) -> bool:
        """Heuristic: TransientError with deadlock/lock-related message."""
        msg = str(e).lower()
        return any(x in msg for x in DEADLOCK_INDICATORS)

    def _execute_with_retry(self, func: Callable, *args, **kwargs):
        """Execute function with exponential backoff. Extra retries for deadlock-like TransientError."""
        last_exception = None
        max_retries = self._max_retries
        attempt = 0
        while attempt < max_retries:
            try:
                return func(*args, **kwargs)
            except (ServiceUnavailable, TransientError) as e:
                last_exception = e
                is_deadlock = isinstance(e, TransientError) and self._is_deadlock(e)
                if is_deadlock:
                    logger.warning("Deadlock detected, retrying", attempt=attempt + 1, error=str(e))
                    if attempt == 0:
                        max_retries = max(max_retries, 5)
                if attempt < max_retries - 1:
                    delay = self._retry_delay * (2 ** attempt)
                    if not is_deadlock:
                        logger.warning(
                            "Neo4j operation failed, retrying",
                            attempt=attempt + 1,
                            delay=delay,
                            error=str(e),
                        )
                    time.sleep(delay)
                else:
                    logger.error("Neo4j operation failed after retries", error=str(e))
                attempt += 1
            except Exception as e:
                logger.error("Neo4j operation failed", error=str(e))
                raise
        if last_exception:
            raise last_exception

    def read_transaction(self, unit_of_work: Callable) -> Any:
        """Execute a read-only transaction. unit_of_work(tx) -> result; tx.run(...)."""
        if not self.driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")

        def _run():
            with self.driver.session() as session:
                return session.execute_read(unit_of_work)

        return self._execute_with_retry(_run)

    def write_transaction(self, unit_of_work: Callable) -> Any:
        """Execute a write transaction. unit_of_work(tx) -> result; tx.run(...)."""
        if not self.driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")

        def _run():
            with self.driver.session() as session:
                return session.execute_write(unit_of_work)

        return self._execute_with_retry(_run)

    def execute_cypher(
        self,
        query: str,
        parameters: Optional[Dict] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        timeout: Optional[float] = None,
        *,
        subject: Optional["SubjectAttributes"] = None,
        action: Optional["Action"] = None,
        node_alias: str = "n",
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query with optional permission-aware filtering.

        If a SubjectAttributes is provided, node-level filters are injected using the
        configured alias (defaults to 'n').
        """
        if parameters is None:
            parameters = {}

        if subject is not None:
            from src.security.abac import Action as AbacAction
            if action is None:
                action = AbacAction.READ
            rewritten = rewrite_node_query_with_permissions(
                query,
                parameters,
                action=action,
                subject=subject,
                node_alias=node_alias,
            )
            query, parameters = rewritten.cypher, rewritten.params

        if skip is not None and limit is not None:
            query = query.rstrip().rstrip(";") + " SKIP $skip LIMIT $limit"
            parameters = dict(parameters, skip=skip, limit=limit)
        run_arg = Query(query, timeout=timeout) if timeout is not None else query

        with track_neo4j_query("cypher"):
            def _execute():
                with self.get_session() as session:
                    result = session.run(run_arg, parameters)
                    return [record.data() for record in result]

            return self._execute_with_retry(_execute)

    @contextmanager
    def stream_cypher(
        self,
        query: str,
        parameters: Optional[Dict] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Stream query results one record at a time without loading all into memory.
        Yields record.data() for each row. Session is held until the context exits;
        consume or exit early to avoid holding the connection.
        """
        if parameters is None:
            parameters = {}
        if skip is not None and limit is not None:
            query = query.rstrip().rstrip(";") + " SKIP $skip LIMIT $limit"
            parameters = dict(parameters, skip=skip, limit=limit)
        run_arg = Query(query, timeout=timeout) if timeout is not None else query
        if not self.driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")

        def _run():
            session = self.driver.session()
            result = session.run(run_arg, parameters)
            return (session, result)

        session, result = self._execute_with_retry(_run)
        try:
            yield (record.data() for record in result)
        finally:
            session.close()

    def create_node(self, label: str, properties: Dict[str, Any]) -> str:
        """Create a node and return its internal id as string. Label validated via ontology."""
        query = cypher_queries.create_node_query(label)

        def _execute():
            with self.get_session() as session:
                result = session.run(query, {"properties": properties})
                record = result.single()
                return str(record["node_id"])

        node_id = self._execute_with_retry(_execute)
        logger.debug("Node created", label=label, node_id=node_id)
        return node_id

    def find_node(self, label: str, filters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Find a single node by label and optional filters. Returns property dict or None. Filter keys validated."""
        if filters is None:
            filters = {}
        query = cypher_queries.find_node_query(label, list(filters.keys()))

        def _execute():
            with self.get_session() as session:
                result = session.run(query, filters)
                record = result.single()
                if record and record["n"] is not None:
                    return dict(record["n"])
                return None

        return self._execute_with_retry(_execute)

    def create_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create a relationship between two nodes by internal id. rel_type validated via ontology."""
        if properties is None:
            properties = {}
        query = cypher_queries.create_relationship_query(rel_type)
        params = {"from_id": int(from_id), "to_id": int(to_id), "props": properties}

        def _execute():
            with self.get_session() as session:
                session.run(query, params)

        self._execute_with_retry(_execute)
        logger.debug("Relationship created", from_id=from_id, to_id=to_id, rel_type=rel_type)

    def traverse(
        self,
        start_id: str,
        rel_types: Optional[List[str]] = None,
        max_depth: int = 3,
        *,
        subject: Optional["SubjectAttributes"] = None,
        action: Optional["Action"] = None,
    ) -> Dict[str, Any]:
        """
        Traverse from start_id along rel_types (or all) up to max_depth.
        Returns {start_id, nodes, relationships}. If a subject is provided,
        node and relationship visibility are filtered using ABAC rules.
        """
        query = cypher_queries.traverse_query(rel_types, max_depth)
        params: Dict[str, Any] = {"start_id": int(start_id)}

        if subject is not None:
            from src.security.abac import Action as AbacAction
            if action is None:
                action = AbacAction.READ
            rewritten = rewrite_traversal_with_permissions(
                query,
                params,
                action=action,
                subject=subject,
                node_alias="n",
                rel_alias="r",
            )
            query, params = rewritten.cypher, rewritten.params

        with track_neo4j_query("traversal"):
            def _execute():
                with self.get_session() as session:
                    result = session.run(query, params)
                    record = result.single()
                    if record is None:
                        return {"start_id": int(start_id), "nodes": [], "relationships": []}
                    return {
                        "start_id": record["start_id"],
                        "nodes": list(record["nodes"]) if record["nodes"] else [],
                        "relationships": list(record["relationships"]) if record["relationships"] else [],
                    }

            return self._execute_with_retry(_execute)

    def find_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find shortest path(s) between start_id and end_id. Returns list of {nodes, relationships} (empty if none)."""
        query = cypher_queries.find_path_query(max_depth)
        params = {"start_id": int(start_id), "end_id": int(end_id)}

        def _execute():
            with self.get_session() as session:
                result = session.run(query, params)
                rows = list(result)
                return [{"nodes": r["nodes"], "relationships": r["rels"]} for r in rows]

        return self._execute_with_retry(_execute)

    def merge_node(self, label: str, id_val: str, props: Dict[str, Any]) -> str:
        """Upsert node by (label, id). ON CREATE and ON MATCH both set props. Returns internal id. Idempotent."""
        if "id" not in props:
            props = dict(props, id=id_val)
        query = cypher_queries.merge_node_query(label)

        def _execute():
            with self.get_session() as session:
                result = session.run(query, {"id": id_val, "props": props})
                record = result.single()
                return str(record["node_id"])

        node_id = self._execute_with_retry(_execute)
        logger.debug("Node merged", label=label, id=id_val)
        return node_id

    def merge_relationship_by_business_id(
        self,
        from_label: str,
        from_id: str,
        to_label: str,
        to_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Upsert relationship (a:FromLabel {id: from_id})-[r:RelType]->(b:ToLabel {id: to_id}). Idempotent."""
        props = properties or {}
        query = cypher_queries.merge_relationship_by_business_id_query(from_label, to_label, rel_type)

        def _execute():
            with self.get_session() as session:
                session.run(query, {"from_id": from_id, "to_id": to_id, "props": props})

        self._execute_with_retry(_execute)
        logger.debug("Relationship merged", from_label=from_label, to_label=to_label, rel_type=rel_type)

    def batch_create(
        self,
        nodes: Optional[List[Dict[str, Any]]] = None,
        relationships: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Bulk create nodes and relationships in one write transaction. Node: {label, props}. Rel: {from_id, to_id, type, props?}. Validates labels and types."""
        nodes = nodes or []
        relationships = relationships or []
        for n in nodes:
            if n.get("label") not in NODE_LABELS:
                raise ValueError(f"Invalid node label in batch: {n.get('label')}")
        for r in relationships:
            if r.get("type") not in RELATIONSHIP_TYPES:
                raise ValueError(f"Invalid relationship type in batch: {r.get('type')}")

        nodes_payload = [{"label": n["label"], "props": n.get("props", {})} for n in nodes]
        rels_payload = [
            {
                "from_id": int(r["from_id"]),
                "to_id": int(r["to_id"]),
                "type": r["type"],
                "props": r.get("props", {}),
            }
            for r in relationships
        ]

        def _tx(tx):
            node_ids = []
            rel_count = 0
            if nodes_payload:
                qn = cypher_queries.batch_create_nodes_query()
                res = tx.run(qn, {"nodes": nodes_payload})
                rec = res.single()
                if rec and rec["ids"]:
                    node_ids = list(rec["ids"])
            if rels_payload:
                qr = cypher_queries.batch_create_relationships_query()
                res = tx.run(qr, {"rels": rels_payload})
                rec = res.single()
                if rec:
                    rel_count = rec["count"] or 0
            return {"node_ids": node_ids, "relationships_created": rel_count}

        return self.write_transaction(_tx)

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


neo4j_client = Neo4jClient()
