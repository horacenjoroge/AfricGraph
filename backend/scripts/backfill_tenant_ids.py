#!/usr/bin/env python3
"""
Backfill tenant_id for existing nodes that don't have it set.

This script is useful when:
- Data was ingested before tenant isolation was implemented
- Nodes were created without tenant context
- You need to assign existing data to a specific tenant

Usage:
    python backend/scripts/backfill_tenant_ids.py <tenant_id> [--dry-run] [--label Transaction]
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
from src.tenancy.context import set_current_tenant

logger = get_logger(__name__)


def backfill_tenant_id(tenant_id: str, label: str = "Transaction", dry_run: bool = False):
    """
    Backfill tenant_id for nodes of a specific label that don't have it set.
    
    Args:
        tenant_id: The tenant ID to assign to nodes
        label: The node label to update (default: Transaction)
        dry_run: If True, only show what would be updated without making changes
    """
    # Connect to databases first (needed for tenant lookup)
    postgres_client.connect()
    neo4j_client.connect()
    
    # Initialize tenant manager and verify tenant exists
    tenant_manager = TenantManager()
    tenant = tenant_manager.get_tenant(tenant_id)
    if not tenant:
        logger.error(f"Tenant not found: {tenant_id}")
        return False
    
    logger.info(f"Backfilling tenant_id for {label} nodes", tenant_id=tenant_id, tenant_name=tenant.name)
    
    # Set tenant context for the operation
    set_current_tenant(tenant)
    
    try:
        # Count nodes without tenant_id
        count_query = f"""
        MATCH (n:{label})
        WHERE n.tenant_id IS NULL OR n.tenant_id = ''
        RETURN count(n) as count
        """
        result = neo4j_client.execute_cypher(count_query, {}, skip_tenant_filter=True)
        count = result[0]["count"] if result else 0
        
        logger.info(f"Found {count} {label} nodes without tenant_id")
        
        if count == 0:
            logger.info("No nodes need backfilling")
            return True
        
        if dry_run:
            logger.info(f"[DRY RUN] Would update {count} {label} nodes with tenant_id={tenant_id}")
            return True
        
        # Update nodes with tenant_id
        update_query = f"""
        MATCH (n:{label})
        WHERE n.tenant_id IS NULL OR n.tenant_id = ''
        SET n.tenant_id = $tenant_id
        RETURN count(n) as updated
        """
        result = neo4j_client.execute_cypher(
            update_query,
            {"tenant_id": tenant_id},
            skip_tenant_filter=True
        )
        updated = result[0]["updated"] if result else 0
        
        logger.info(f"Successfully updated {updated} {label} nodes with tenant_id={tenant_id}")
        
        # Also update relationships if they have tenant_id
        rel_update_query = f"""
        MATCH ()-[r]->()
        WHERE type(r) IN ['INVOLVES', 'HAS', 'OWNS', 'BELONGS_TO'] 
          AND (r.tenant_id IS NULL OR r.tenant_id = '')
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
            logger.info(f"Successfully updated {rel_updated} relationships with tenant_id={tenant_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during backfill", error=str(e), exc_info=True)
        return False
    finally:
        neo4j_client.close()
        postgres_client.close()
        set_current_tenant(None)


def main():
    parser = argparse.ArgumentParser(description="Backfill tenant_id for existing nodes")
    parser.add_argument("tenant_id", help="Tenant ID to assign to nodes")
    parser.add_argument("--label", default="Transaction", help="Node label to update (default: Transaction)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated without making changes")
    
    args = parser.parse_args()
    
    success = backfill_tenant_id(
        tenant_id=args.tenant_id,
        label=args.label,
        dry_run=args.dry_run
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
