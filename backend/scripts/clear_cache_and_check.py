#!/usr/bin/env python3
"""Script to clear cache and check what's actually in Neo4j."""
import os
import sys
from pathlib import Path

# Set environment variables before importing anything
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("NEO4J_URI", os.getenv("NEO4J_URI", "bolt://neo4j:7687"))
os.environ.setdefault("NEO4J_USER", os.getenv("NEO4J_USER", "neo4j"))
os.environ.setdefault("NEO4J_PASSWORD", os.getenv("NEO4J_PASSWORD", ""))
os.environ.setdefault("REDIS_HOST", os.getenv("REDIS_HOST", "redis"))
os.environ.setdefault("REDIS_PORT", os.getenv("REDIS_PORT", "6379"))

from neo4j import GraphDatabase
import redis

# Direct connections using environment variables
neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "")

neo4j_driver = GraphDatabase.driver(
    neo4j_uri,
    auth=(neo4j_user, neo4j_password)
)
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=False
)

def log(msg):
    print(msg)


def clear_all_cache():
    """Clear all cache from Redis."""
    try:
        log("Clearing all cache...")
        # Clear all keys
        keys = redis_client.keys("*")
        if keys:
            deleted = redis_client.delete(*keys)
            log(f"Deleted {deleted} cache keys")
        else:
            log("No cache keys found")
        return True
    except Exception as e:
        log(f"Failed to clear cache: {e}")
        import traceback
        traceback.print_exc()
        return False


def clear_graph_cache():
    """Clear graph cache specifically."""
    try:
        log("Clearing graph cache...")
        # Clear all graph-related keys
        keys = redis_client.keys("*graph*")
        if keys:
            deleted = redis_client.delete(*keys)
            log(f"Deleted {deleted} graph cache keys")
        else:
            log("No graph cache keys found")
        return True
    except Exception as e:
        log(f"Failed to clear graph cache: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_transaction_properties():
    """Check what properties are actually stored in Neo4j for transactions."""
    try:
        log("Checking transaction properties in Neo4j...")
        
        # Get a few sample transactions
        query = """
        MATCH (t:Transaction)
        WHERE t.id STARTS WITH 'mpesa:'
        RETURN t.id, properties(t) as props
        ORDER BY t.id
        LIMIT 5
        """
        
        with neo4j_driver.session() as session:
            result = session.run(query)
            
            log(f"\n{'='*80}")
            log("Sample Transaction Properties in Neo4j:")
            log(f"{'='*80}\n")
            
            for record in result:
                tx_id = record.get("id", "unknown")
                props = dict(record.get("props", {}))
                
                log(f"Transaction ID: {tx_id}")
                log(f"  Properties found: {list(props.keys())}")
                log(f"  Amount: {props.get('amount')}")
                log(f"  Currency: {props.get('currency')}")
                log(f"  Counterparty Name: {props.get('counterparty_name')}")
                log(f"  Counterparty Phone: {props.get('counterparty_phone')}")
                log(f"  Direction: {props.get('direction')}")
                log(f"  Provider TXN ID: {props.get('provider_txn_id')}")
                log(f"  Balance After: {props.get('balance_after')}")
                log(f"  Type: {props.get('type')}")
                log(f"  Description: {props.get('description', '')[:50]}...")
                log("")
        
        return True
    except Exception as e:
        log(f"Failed to check transaction properties: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_cache_keys():
    """Check what cache keys exist."""
    try:
        log("Checking cache keys...")
        keys = redis_client.keys("*")
        graph_keys = [k for k in keys if b"graph" in k.lower() or b"subgraph" in k.lower()]
        
        log(f"\n{'='*80}")
        log("Cache Keys:")
        log(f"{'='*80}\n")
        log(f"Total keys: {len(keys)}")
        log(f"Graph-related keys: {len(graph_keys)}")
        
        if graph_keys:
            log("\nGraph cache keys:")
            for key in graph_keys[:10]:  # Show first 10
                log(f"  - {key.decode() if isinstance(key, bytes) else key}")
            if len(graph_keys) > 10:
                log(f"  ... and {len(graph_keys) - 10} more")
        
        return True
    except Exception as e:
        log(f"Failed to check cache keys: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    log("="*80)
    log("Cache Clearing and Data Verification Script")
    log("="*80)
    
    try:
        # Step 1: Check what's in Neo4j
        log("\n[Step 1] Checking what's actually stored in Neo4j...")
        check_transaction_properties()
        
        # Step 2: Check cache keys
        log("\n[Step 2] Checking cache keys...")
        check_cache_keys()
        
        # Step 3: Clear graph cache
        log("\n[Step 3] Clearing graph cache...")
        clear_graph_cache()
        
        # Step 4: Clear all cache
        log("\n[Step 4] Clearing all cache...")
        clear_all_cache()
        
        # Step 5: Verify cache is cleared
        log("\n[Step 5] Verifying cache is cleared...")
        check_cache_keys()
        
        log("\n" + "="*80)
        log("Script completed!")
        log("="*80)
        log("\nNext steps:")
        log("1. If properties are missing in Neo4j, you need to re-ingest your CSV file")
        log("2. If properties exist in Neo4j but not showing in frontend, check the API response")
        log("3. Try refreshing the frontend page after clearing cache")
    finally:
        neo4j_driver.close()


if __name__ == "__main__":
    main()
