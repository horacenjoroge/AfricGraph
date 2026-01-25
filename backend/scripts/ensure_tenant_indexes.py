#!/usr/bin/env python3
"""
Script to ensure all tenant isolation indexes are created in Neo4j.

Usage:
    python scripts/ensure_tenant_indexes.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.infrastructure.database.neo4j_client import neo4j_client
from src.tenancy.indexes import ensure_tenant_indexes
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def main():
    print("Connecting to Neo4j...")
    neo4j_client.connect()
    
    try:
        print("\nEnsuring tenant isolation indexes...")
        print("=" * 60)
        
        results = ensure_tenant_indexes()
        
        print("=" * 60)
        print(f"\nIndex creation completed!")
        print(f"  - Node indexes created: {len(results['node_indexes_created'])}")
        print(f"  - Composite indexes created: {len(results['composite_indexes_created'])}")
        print(f"  - Relationship indexes created: {len(results['relationship_indexes_created'])}")
        
        if results['errors']:
            print(f"\n  - Errors: {len(results['errors'])}")
            for error in results['errors']:
                print(f"    * {error}")
        else:
            print(f"  - Errors: 0")
        
    except Exception as e:
        print(f"\nError during index creation: {e}")
        sys.exit(1)
    finally:
        neo4j_client.close()


if __name__ == "__main__":
    main()
