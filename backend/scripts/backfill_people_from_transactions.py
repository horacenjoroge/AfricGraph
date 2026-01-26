#!/usr/bin/env python3
"""
Backfill tenant_id for Person nodes based on their relationships with Transaction nodes.

This is useful when:
- Person nodes were created during ingestion but don't have tenant_id
- Person nodes are connected to Transaction nodes that have tenant_id
- We can infer the Person's tenant_id from the Transaction's tenant_id

Usage:
    python backend/scripts/backfill_people_from_transactions.py <tenant_id> [--dry-run]
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.database.postgres_client import postgres_client
from src.tenancy.manager import TenantManager
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def backfill_people_from_transactions(tenant_id: str, dry_run: bool = False):
    """
    Backfill tenant_id for Person nodes based on their Transaction relationships.
    
    Args:
        tenant_id: The tenant ID to assign to Person nodes
        dry_run: If True, only show what would be updated without making changes
    """
    # Connect to databases first
    postgres_client.connect()
    neo4j_client.connect()
    
    try:
        # Verify tenant exists
        tenant_manager = TenantManager()
        tenant = tenant_manager.get_tenant(tenant_id)
        if not tenant:
            logger.error(f"Tenant not found: {tenant_id}")
            return False
        
        logger.info(f"Backfilling Person nodes from Transaction relationships", tenant_id=tenant_id, tenant_name=tenant.name)
        
        # Find Person nodes connected to this tenant's transactions
        # These are people who should belong to this tenant
        query = """
        MATCH (t:Transaction {tenant_id: $tenant_id})-[r:INVOLVES]->(p:Person)
        WHERE p.tenant_id IS NULL OR p.tenant_id = '' OR p.tenant_id <> $tenant_id
        RETURN DISTINCT p.id as person_id, count(t) as tx_count
        ORDER BY tx_count DESC
        """
        result = neo4j_client.execute_cypher(query, {"tenant_id": tenant_id}, skip_tenant_filter=True)
        
        person_ids = [row["person_id"] for row in result]
        count = len(person_ids)
        
        logger.info(f"Found {count} Person nodes connected to {tenant_id} transactions that need tenant_id")
        
        if count == 0:
            logger.info("No Person nodes need backfilling")
            return True
        
        if dry_run:
            logger.info(f"[DRY RUN] Would update {count} Person nodes with tenant_id={tenant_id}")
            for i, pid in enumerate(person_ids[:10]):  # Show first 10
                logger.info(f"  - {pid}")
            if count > 10:
                logger.info(f"  ... and {count - 10} more")
            return True
        
        # Update Person nodes with tenant_id
        # Update in batches to avoid very long queries
        batch_size = 50
        updated = 0
        
        for i in range(0, len(person_ids), batch_size):
            batch = person_ids[i:i + batch_size]
            # Create a query that updates all Person nodes in the batch
            batch_query = f"""
            MATCH (p:Person)
            WHERE p.id IN {batch}
            SET p.tenant_id = $tenant_id
            RETURN count(p) as updated
            """
            # Convert batch to Cypher list format
            batch_list = "['" + "','".join(batch) + "']"
            batch_query = batch_query.replace(str(batch), batch_list)
            
            batch_result = neo4j_client.execute_cypher(
                batch_query,
                {"tenant_id": tenant_id},
                skip_tenant_filter=True
            )
            batch_updated = batch_result[0]["updated"] if batch_result else 0
            updated += batch_updated
            logger.info(f"Updated batch {i//batch_size + 1}: {batch_updated} Person nodes")
        
        logger.info(f"Successfully updated {updated} Person nodes with tenant_id={tenant_id}")
        
        # Also update relationships if they have tenant_id property
        rel_update_query = """
        MATCH (t:Transaction {tenant_id: $tenant_id})-[r:INVOLVES]->(p:Person {tenant_id: $tenant_id})
        WHERE r.tenant_id IS NULL OR r.tenant_id = ''
        SET r.tenant_id = $tenant_id
        RETURN count(r) as updated
        """
        rel_result = neo4j_client.execute_cypher(
            rel_update_query,
            {"tenant_id": tenant_id},
            skip_tenant_filter=True
        )
        rel_updated = rel_result[0]["updated"] if rel_result else 0
        
        if rel_updated > 0:
            logger.info(f"Successfully updated {rel_updated} INVOLVES relationships with tenant_id={tenant_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during backfill", error=str(e), exc_info=True)
        return False
    finally:
        neo4j_client.close()
        postgres_client.close()


def main():
    parser = argparse.ArgumentParser(description="Backfill Person tenant_id from Transaction relationships")
    parser.add_argument("tenant_id", help="Tenant ID to assign to Person nodes")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated without making changes")
    
    args = parser.parse_args()
    
    success = backfill_people_from_transactions(
        tenant_id=args.tenant_id,
        dry_run=args.dry_run
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
