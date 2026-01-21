"""Elasticsearch indexing for entities."""
from typing import Dict, Optional, List
from datetime import datetime

from src.infrastructure.search.elasticsearch_client import elasticsearch_client
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)

# Index names
INDEX_BUSINESSES = "businesses"
INDEX_PEOPLE = "people"
INDEX_TRANSACTIONS = "transactions"
INDEX_INVOICES = "invoices"


def ensure_indices():
    """Create Elasticsearch indices with proper mappings."""
    # Business index mapping
    business_mapping = {
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "name": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "suggest": {"type": "completion"},
                    },
                },
                "registration_number": {"type": "keyword"},
                "sector": {"type": "keyword"},
                "location": {"type": "geo_point"},
                "created_at": {"type": "date"},
            }
        }
    }

    # Person index mapping
    person_mapping = {
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "name": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "suggest": {"type": "completion"},
                    },
                },
                "email": {"type": "keyword"},
                "phone": {"type": "keyword"},
            }
        }
    }

    # Transaction index mapping
    transaction_mapping = {
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "description": {
                    "type": "text",
                    "analyzer": "standard",
                },
                "amount": {"type": "float"},
                "currency": {"type": "keyword"},
                "transaction_type": {"type": "keyword"},
                "business_id": {"type": "keyword"},
                "timestamp": {"type": "date"},
            }
        }
    }

    # Invoice index mapping
    invoice_mapping = {
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "invoice_number": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword"},
                    },
                },
                "business_id": {"type": "keyword"},
                "amount": {"type": "float"},
                "status": {"type": "keyword"},
                "created_at": {"type": "date"},
            }
        }
    }

    # Create indices
    for index_name, mapping in [
        (INDEX_BUSINESSES, business_mapping),
        (INDEX_PEOPLE, person_mapping),
        (INDEX_TRANSACTIONS, transaction_mapping),
        (INDEX_INVOICES, invoice_mapping),
    ]:
        try:
            if not elasticsearch_client.client.indices.exists(index=index_name):
                elasticsearch_client.client.indices.create(
                    index=index_name, body=mapping
                )
                logger.info(f"Created Elasticsearch index: {index_name}")
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")


def index_business(business_id: str, data: Dict) -> bool:
    """Index a business in Elasticsearch."""
    ensure_indices()
    try:
        doc = {
            "id": business_id,
            "name": data.get("name", ""),
            "registration_number": data.get("registration_number"),
            "sector": data.get("sector"),
            "created_at": data.get("created_at", datetime.now().isoformat()),
        }
        
        # Add location if available
        if "latitude" in data and "longitude" in data:
            doc["location"] = {
                "lat": data["latitude"],
                "lon": data["longitude"],
            }
        
        elasticsearch_client.client.index(
            index=INDEX_BUSINESSES, id=business_id, body=doc
        )
        logger.debug(f"Indexed business: {business_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to index business {business_id}: {e}")
        return False


def index_person(person_id: str, data: Dict) -> bool:
    """Index a person in Elasticsearch."""
    ensure_indices()
    try:
        doc = {
            "id": person_id,
            "name": data.get("name", ""),
            "email": data.get("email"),
            "phone": data.get("phone"),
        }
        elasticsearch_client.client.index(
            index=INDEX_PEOPLE, id=person_id, body=doc
        )
        logger.debug(f"Indexed person: {person_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to index person {person_id}: {e}")
        return False


def index_transaction(transaction_id: str, data: Dict) -> bool:
    """Index a transaction in Elasticsearch."""
    ensure_indices()
    try:
        doc = {
            "id": transaction_id,
            "description": data.get("description", ""),
            "amount": data.get("amount", 0),
            "currency": data.get("currency", "USD"),
            "transaction_type": data.get("transaction_type"),
            "business_id": data.get("business_id"),
            "timestamp": data.get("timestamp", datetime.now().isoformat()),
        }
        elasticsearch_client.client.index(
            index=INDEX_TRANSACTIONS, id=transaction_id, body=doc
        )
        logger.debug(f"Indexed transaction: {transaction_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to index transaction {transaction_id}: {e}")
        return False


def index_invoice(invoice_id: str, data: Dict) -> bool:
    """Index an invoice in Elasticsearch."""
    ensure_indices()
    try:
        doc = {
            "id": invoice_id,
            "invoice_number": data.get("invoice_number", ""),
            "business_id": data.get("business_id"),
            "amount": data.get("amount", 0),
            "status": data.get("status"),
            "created_at": data.get("created_at", datetime.now().isoformat()),
        }
        elasticsearch_client.client.index(
            index=INDEX_INVOICES, id=invoice_id, body=doc
        )
        logger.debug(f"Indexed invoice: {invoice_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to index invoice {invoice_id}: {e}")
        return False


def delete_from_index(index_name: str, doc_id: str) -> bool:
    """Delete a document from an index."""
    try:
        elasticsearch_client.client.delete(index=index_name, id=doc_id)
        logger.debug(f"Deleted from {index_name}: {doc_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete from {index_name}: {e}")
        return False
