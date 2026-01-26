#!/usr/bin/env python3
"""
Reassign only MPESA transactions from one tenant to another.

This is more selective than reassign_transactions.py - it only moves
transactions that match specific criteria (e.g., MPESA provider, ID pattern).

Usage:
    python backend/scripts/reassign_mpesa_only.py <source_tenant_id> <target_tenant_id> [--dry-run]
    python backend/scripts/reassign_mpesa_only.py code-vault migrated-tenant --dry-run
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.database.postgres_client import postgres_client
from src.tenancy.manager import TenantManager
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def reassign_mpesa_transactions(source_tenant_id: str, target_tenant_id: str, dry_run: bool = False):
    """
    Reassign only MPESA transactions from source tenant to target tenant.
    
    Args:
        source_tenant_id: The tenant ID to move MPESA transactions from
        target_tenant_id: The tenant ID to move MPESA transactions to
        dry_run: If True, only show what would be reassigned without making changes
    """
    postgres_client.connect()
    neo4j_client.connect()
    
    try:
        # Verify both tenants exist
        tenant_manager = TenantManager()
        source_tenant = tenant_manager.get_tenant(source_tenant_id)
        target_tenant = tenant_manager.get_tenant(target_tenant_id)
        
        if not source_tenant:
            logger.error(f"Source tenant not found: {source_tenant_id}")
            return False
        if not target_tenant:
            logger.error(f"Target tenant not found: {target_tenant_id}")
            return False
        
        logger.info(
            f"Reassigning MPESA transactions",
            source_tenant_id=source_tenant_id,
            source_tenant_name=source_tenant.name,
            target_tenant_id=target_tenant_id,
            target_tenant_name=target_tenant.name,
        )
        
        # Count MPESA transactions to reassign (by ID pattern or provider)
        count_query = """
        MATCH (t:Transaction {tenant_id: $source_tenant_id})
        WHERE t.id STARTS WITH "mpesa:" OR t.source_provider = "mpesa"
        RETURN count(t) as cnt
        """
        result = neo4j_client.execute_cypher(
            count_query,
            {"source_tenant_id": source_tenant_id},
            skip_tenant_filter=True
        )
        count = result[0]["cnt"] if result else 0
        
        logger.info(f"Found {count} MPESA transactions to reassign")
        
        if count == 0:
            logger.info("No MPESA transactions to reassign")
            return True
        
        if dry_run:
            logger.info(f"[DRY RUN] Would reassign {count} MPESA transactions from {source_tenant_id} to {target_tenant_id}")
            # Show sample transactions
            sample_query = """
            MATCH (t:Transaction {tenant_id: $source_tenant_id})
            WHERE t.id STARTS WITH "mpesa:" OR t.source_provider = "mpesa"
            RETURN t.id, t.date, t.amount, t.source_provider
            ORDER BY t.date DESC
            LIMIT 10
            """
            sample_result = neo4j_client.execute_cypher(
                sample_query,
                {"source_tenant_id": source_tenant_id},
                skip_tenant_filter=True
            )
            logger.info("Sample MPESA transactions to reassign:")
            for row in sample_result:
                logger.info(f"  {row.get('t.id')}: {row.get('t.date')} - {row.get('t.amount')} ({row.get('t.source_provider')})")
            return True
        
        # Reassign MPESA transactions only
        update_query = """
        MATCH (t:Transaction {tenant_id: $source_tenant_id})
        WHERE t.id STARTS WITH "mpesa:" OR t.source_provider = "mpesa"
        SET t.tenant_id = $target_tenant_id
        RETURN count(t) as updated
        """
        result = neo4j_client.execute_cypher(
            update_query,
            {"source_tenant_id": source_tenant_id, "target_tenant_id": target_tenant_id},
            skip_tenant_filter=True
        )
        updated = result[0]["updated"] if result else 0
        
        logger.info(f"Successfully reassigned {updated} MPESA transactions to {target_tenant_id}")
        
        # Also reassign related Person nodes if they're only connected to these MPESA transactions
        person_query = """
        MATCH (t:Transaction {tenant_id: $target_tenant_id})-[r:INVOLVES]->(p:Person)
        WHERE (t.id STARTS WITH "mpesa:" OR t.source_provider = "mpesa")
          AND (p.tenant_id = $source_tenant_id OR p.tenant_id IS NULL OR p.tenant_id = '')
        WITH DISTINCT p
        SET p.tenant_id = $target_tenant_id
        RETURN count(p) as updated
        """
        person_result = neo4j_client.execute_cypher(
            person_query,
            {"source_tenant_id": source_tenant_id, "target_tenant_id": target_tenant_id},
            skip_tenant_filter=True
        )
        person_updated = person_result[0]["updated"] if person_result else 0
        
        if person_updated > 0:
            logger.info(f"Successfully reassigned {person_updated} Person nodes to {target_tenant_id}")
        
        # Reassign relationships
        rel_query = """
        MATCH (t:Transaction {tenant_id: $target_tenant_id})-[r:INVOLVES]->(p:Person {tenant_id: $target_tenant_id})
        WHERE (t.id STARTS WITH "mpesa:" OR t.source_provider = "mpesa")
          AND (r.tenant_id = $source_tenant_id OR r.tenant_id IS NULL OR r.tenant_id = '')
        SET r.tenant_id = $target_tenant_id
        RETURN count(r) as updated
        """
        rel_result = neo4j_client.execute_cypher(
            rel_query,
            {"source_tenant_id": source_tenant_id, "target_tenant_id": target_tenant_id},
            skip_tenant_filter=True
        )
        rel_updated = rel_result[0]["updated"] if rel_result else 0
        
        if rel_updated > 0:
            logger.info(f"Successfully reassigned {rel_updated} relationships to {target_tenant_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during reassignment", error=str(e), exc_info=True)
        return False
    finally:
        neo4j_client.close()
        postgres_client.close()


def main():
    parser = argparse.ArgumentParser(description="Reassign only MPESA transactions from one tenant to another")
    parser.add_argument("source_tenant_id", help="Source tenant ID to move MPESA transactions from")
    parser.add_argument("target_tenant_id", help="Target tenant ID to move MPESA transactions to")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be reassigned without making changes")
    
    args = parser.parse_args()
    
    success = reassign_mpesa_transactions(
        source_tenant_id=args.source_tenant_id,
        target_tenant_id=args.target_tenant_id,
        dry_run=args.dry_run
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
