"""Sync Neo4j data to Elasticsearch indices."""
from typing import Optional

from src.infrastructure.database.neo4j_client import neo4j_client
from src.search.indexing import (
    index_business,
    index_person,
    index_transaction,
    index_invoice,
    ensure_indices,
)
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def sync_business_to_elasticsearch(business_id: str) -> bool:
    """Sync a business from Neo4j to Elasticsearch."""
    try:
        query = """
        MATCH (b:Business {id: $business_id})
        OPTIONAL MATCH (b)-[:LOCATED_AT]->(loc:Location)
        RETURN b, loc
        """
        rows = neo4j_client.execute_cypher(query, {"business_id": business_id})

        if not rows:
            return False

        row = rows[0]
        business = dict(row["b"])

        # Extract location if available
        location = row.get("loc")
        if location:
            business["latitude"] = location.get("latitude")
            business["longitude"] = location.get("longitude")

        return index_business(business_id, business)
    except Exception as e:
        logger.error(f"Failed to sync business {business_id}: {e}")
        return False


def sync_person_to_elasticsearch(person_id: str) -> bool:
    """Sync a person from Neo4j to Elasticsearch."""
    try:
        query = "MATCH (p:Person {id: $person_id}) RETURN p"
        rows = neo4j_client.execute_cypher(query, {"person_id": person_id})

        if not rows:
            return False

        person = dict(rows[0]["p"])
        return index_person(person_id, person)
    except Exception as e:
        logger.error(f"Failed to sync person {person_id}: {e}")
        return False


def sync_transaction_to_elasticsearch(transaction_id: str) -> bool:
    """Sync a transaction from Neo4j to Elasticsearch."""
    try:
        query = """
        MATCH (t:Transaction {id: $transaction_id})
        OPTIONAL MATCH (t)-[:INVOLVES]->(b:Business)
        RETURN t, b.id as business_id
        """
        rows = neo4j_client.execute_cypher(query, {"transaction_id": transaction_id})

        if not rows:
            return False

        row = rows[0]
        transaction = dict(row["t"])
        transaction["business_id"] = row.get("business_id")

        return index_transaction(transaction_id, transaction)
    except Exception as e:
        logger.error(f"Failed to sync transaction {transaction_id}: {e}")
        return False


def sync_all_businesses(limit: Optional[int] = None) -> int:
    """Sync all businesses to Elasticsearch."""
    ensure_indices()

    query = "MATCH (b:Business) RETURN b.id as business_id"
    if limit:
        query += f" LIMIT {limit}"

    rows = neo4j_client.execute_cypher(query, {})

    synced = 0
    for row in rows:
        business_id = row["business_id"]
        if sync_business_to_elasticsearch(business_id):
            synced += 1

    logger.info(f"Synced {synced} businesses to Elasticsearch")
    return synced


def sync_all_people(limit: Optional[int] = None) -> int:
    """Sync all people to Elasticsearch."""
    ensure_indices()

    query = "MATCH (p:Person) RETURN p.id as person_id"
    if limit:
        query += f" LIMIT {limit}"

    rows = neo4j_client.execute_cypher(query, {})

    synced = 0
    for row in rows:
        person_id = row["person_id"]
        if sync_person_to_elasticsearch(person_id):
            synced += 1

    logger.info(f"Synced {synced} people to Elasticsearch")
    return synced
