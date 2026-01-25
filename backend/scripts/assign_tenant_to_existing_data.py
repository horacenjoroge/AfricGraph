#!/usr/bin/env python3
"""
Migration script to assign tenant_id to existing Neo4j nodes and relationships
that don't have a tenant_id property.

Usage:
    python scripts/assign_tenant_to_existing_data.py <tenant_id>

Example:
    python scripts/assign_tenant_to_existing_data.py code-vault
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def assign_tenant_to_nodes(tenant_id: str) -> int:
    """Assign tenant_id to all nodes that don't have it."""
    query = """
    MATCH (n)
    WHERE n.tenant_id IS NULL
    SET n.tenant_id = $tenant_id
    RETURN count(n) as updated
    """
    
    try:
        result = neo4j_client.execute_cypher(
            query,
            {"tenant_id": tenant_id},
            skip_tenant_filter=True,  # Skip tenant filter for migration
        )
        if result:
            count = result[0].get("updated", 0)
            logger.info(f"Assigned tenant_id to {count} nodes", tenant_id=tenant_id)
            return count
        return 0
    except Exception as e:
        logger.exception("Failed to assign tenant_id to nodes", error=str(e))
        raise


def assign_tenant_to_relationships(tenant_id: str) -> int:
    """Assign tenant_id to all relationships that don't have it."""
    query = """
    MATCH ()-[r]->()
    WHERE r.tenant_id IS NULL
    SET r.tenant_id = $tenant_id
    RETURN count(r) as updated
    """
    
    try:
        result = neo4j_client.execute_cypher(
            query,
            {"tenant_id": tenant_id},
            skip_tenant_filter=True,  # Skip tenant filter for migration
        )
        if result:
            count = result[0].get("updated", 0)
            logger.info(f"Assigned tenant_id to {count} relationships", tenant_id=tenant_id)
            return count
        return 0
    except Exception as e:
        logger.exception("Failed to assign tenant_id to relationships", error=str(e))
        raise


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/assign_tenant_to_existing_data.py <tenant_id>")
        print("Example: python scripts/assign_tenant_to_existing_data.py code-vault")
        sys.exit(1)
    
    tenant_id = sys.argv[1]
    
    print(f"Connecting to Neo4j...")
    neo4j_client.connect()
    
    try:
        print(f"\nAssigning tenant_id '{tenant_id}' to existing data...")
        print("=" * 60)
        
        node_count = assign_tenant_to_nodes(tenant_id)
        rel_count = assign_tenant_to_relationships(tenant_id)
        
        print("=" * 60)
        print(f"\nMigration completed!")
        print(f"  - Nodes updated: {node_count}")
        print(f"  - Relationships updated: {rel_count}")
        print(f"  - Total: {node_count + rel_count}")
        
    except Exception as e:
        print(f"\nError during migration: {e}")
        sys.exit(1)
    finally:
        neo4j_client.close()


if __name__ == "__main__":
    main()
