"""Neo4j index management for tenant isolation and performance."""
from typing import List, Dict, Any
from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.logging import get_logger
from src.domain.ontology import NODE_LABELS, RELATIONSHIP_TYPES

logger = get_logger(__name__)


def ensure_tenant_indexes() -> Dict[str, Any]:
    """
    Ensure all necessary indexes exist for tenant isolation and performance.
    
    Creates:
    - tenant_id index on all node labels
    - Composite indexes for common query patterns
    - Relationship tenant_id indexes
    
    Returns:
        Dictionary with index creation results
    """
    results = {
        "node_indexes_created": [],
        "composite_indexes_created": [],
        "relationship_indexes_created": [],
        "errors": [],
    }
    
    # Create tenant_id index for each node label
    for label in NODE_LABELS:
        try:
            index_name = f"tenant_id_{label.lower()}"
            query = f"""
            CREATE INDEX {index_name} IF NOT EXISTS
            FOR (n:{label})
            ON (n.tenant_id)
            """
            neo4j_client.execute_cypher(query, skip_tenant_filter=True)
            results["node_indexes_created"].append(f"{label}:tenant_id")
            logger.info(f"Created tenant_id index for {label}")
        except Exception as e:
            error_msg = f"Failed to create index for {label}: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
    
    # Create composite indexes for common query patterns
    composite_patterns = [
        ("Business", ["tenant_id", "id"]),
        ("Business", ["tenant_id", "name"]),
        ("Transaction", ["tenant_id", "date"]),
        ("Transaction", ["tenant_id", "amount"]),
        ("Person", ["tenant_id", "name"]),
        ("Invoice", ["tenant_id", "status"]),
        ("Invoice", ["tenant_id", "issue_date"]),
    ]
    
    for label, properties in composite_patterns:
        try:
            index_name = f"tenant_{label.lower()}_{'_'.join(properties)}"
            props_str = ", ".join([f"n.{prop}" for prop in properties])
            query = f"""
            CREATE INDEX {index_name} IF NOT EXISTS
            FOR (n:{label})
            ON ({props_str})
            """
            neo4j_client.execute_cypher(query, skip_tenant_filter=True)
            results["composite_indexes_created"].append(f"{label}:{','.join(properties)}")
            logger.info(f"Created composite index for {label}: {properties}")
        except Exception as e:
            error_msg = f"Failed to create composite index for {label} {properties}: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
    
    # Create relationship tenant_id indexes (if relationships store tenant_id)
    # Convert set to list and limit to first 10 types
    relationship_types_list = list(RELATIONSHIP_TYPES)[:10]
    for rel_type in relationship_types_list:
        try:
            index_name = f"tenant_id_rel_{rel_type.lower().replace('_', '')}"
            query = f"""
            CREATE INDEX {index_name} IF NOT EXISTS
            FOR ()-[r:{rel_type}]-()
            ON (r.tenant_id)
            """
            neo4j_client.execute_cypher(query, skip_tenant_filter=True)
            results["relationship_indexes_created"].append(rel_type)
            logger.info(f"Created tenant_id index for relationship {rel_type}")
        except Exception as e:
            # Some Neo4j versions don't support relationship property indexes
            # This is okay, relationships inherit tenant_id from nodes
            logger.debug(f"Relationship index creation skipped for {rel_type}: {str(e)}")
    
    logger.info(
        "Tenant index creation completed",
        node_indexes=len(results["node_indexes_created"]),
        composite_indexes=len(results["composite_indexes_created"]),
        relationship_indexes=len(results["relationship_indexes_created"]),
        errors=len(results["errors"]),
    )
    
    return results


def get_index_status() -> Dict[str, Any]:
    """Get status of all tenant-related indexes."""
    query = """
    SHOW INDEXES
    WHERE name CONTAINS 'tenant' OR name CONTAINS 'Tenant'
    YIELD name, type, entityType, labelsOrTypes, properties, state, populationPercent
    RETURN name, type, entityType, labelsOrTypes, properties, state, populationPercent
    ORDER BY name
    """
    
    try:
        indexes = neo4j_client.execute_cypher(query, skip_tenant_filter=True)
        return {
            "total_indexes": len(indexes),
            "indexes": indexes,
        }
    except Exception as e:
        logger.error(f"Failed to get index status: {str(e)}")
        return {
            "total_indexes": 0,
            "indexes": [],
            "error": str(e),
        }


def drop_tenant_indexes() -> Dict[str, Any]:
    """Drop all tenant-related indexes (use with caution!)."""
    query = """
    SHOW INDEXES
    WHERE name CONTAINS 'tenant' OR name CONTAINS 'Tenant'
    YIELD name
    RETURN name
    """
    
    try:
        indexes = neo4j_client.execute_cypher(query, skip_tenant_filter=True)
        dropped = []
        errors = []
        
        for idx in indexes:
            index_name = idx.get("name")
            try:
                drop_query = f"DROP INDEX {index_name} IF EXISTS"
                neo4j_client.execute_cypher(drop_query, skip_tenant_filter=True)
                dropped.append(index_name)
            except Exception as e:
                errors.append(f"{index_name}: {str(e)}")
        
        return {
            "dropped": dropped,
            "errors": errors,
        }
    except Exception as e:
        logger.error(f"Failed to drop indexes: {str(e)}")
        return {
            "dropped": [],
            "errors": [str(e)],
        }
