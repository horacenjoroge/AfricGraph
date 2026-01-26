#!/usr/bin/env python3
"""
Check tenant data distribution and find orphaned nodes.

This script helps identify:
- Which tenant_ids exist in the data
- How many nodes each tenant has
- Nodes without tenant_id (orphaned data)
- Nodes with tenant_id that doesn't exist in tenant table

Usage:
    python backend/scripts/check_tenant_data.py [--label Transaction]
"""

import sys
import argparse
from pathlib import Path
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.database.postgres_client import postgres_client
from src.tenancy.manager import TenantManager
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def check_tenant_data(label: str = None):
    """Check tenant data distribution."""
    # Connect to databases
    postgres_client.connect()
    neo4j_client.connect()
    
    try:
        # Get all tenants
        tenant_manager = TenantManager()
        all_tenants = tenant_manager.list_tenants(limit=1000)
        tenant_ids = {t.tenant_id for t in all_tenants}
        
        logger.info(f"Found {len(tenant_ids)} tenants in database")
        
        # Check Neo4j data
        if label:
            labels_to_check = [label]
        else:
            # Check common labels
            labels_to_check = ["Business", "Transaction", "Person", "Invoice", "Payment"]
        
        for node_label in labels_to_check:
            logger.info(f"\n=== Checking {node_label} nodes ===")
            
            # Get distribution by tenant_id
            query = f"""
            MATCH (n:{node_label})
            RETURN 
                COALESCE(n.tenant_id, 'NULL') as tenant_id,
                count(n) as count
            ORDER BY count DESC
            """
            result = neo4j_client.execute_cypher(query, {}, skip_tenant_filter=True)
            
            total = 0
            orphaned = 0
            invalid_tenant = 0
            
            print(f"\n{node_label} Distribution:")
            print("-" * 60)
            
            for row in result:
                tid = row["tenant_id"]
                count = row["count"]
                total += count
                
                if tid == "NULL" or tid == "" or tid is None:
                    orphaned += count
                    print(f"  [ORPHANED] No tenant_id: {count} nodes")
                elif tid not in tenant_ids:
                    invalid_tenant += count
                    print(f"  [INVALID] tenant_id='{tid}' (not in tenant table): {count} nodes")
                else:
                    tenant = next((t for t in all_tenants if t.tenant_id == tid), None)
                    tenant_name = tenant.name if tenant else "Unknown"
                    print(f"  [{tid}] {tenant_name}: {count} nodes")
            
            print("-" * 60)
            print(f"  Total: {total} nodes")
            if orphaned > 0:
                print(f"  ⚠️  Orphaned (no tenant_id): {orphaned} nodes")
            if invalid_tenant > 0:
                print(f"  ⚠️  Invalid tenant_id: {invalid_tenant} nodes")
            
    except Exception as e:
        logger.error(f"Error checking tenant data", error=str(e), exc_info=True)
        return False
    finally:
        neo4j_client.close()
        postgres_client.close()
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Check tenant data distribution")
    parser.add_argument("--label", help="Specific node label to check (default: all common labels)")
    
    args = parser.parse_args()
    
    success = check_tenant_data(label=args.label)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
