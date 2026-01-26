#!/usr/bin/env python3
"""
Fix Person nodes where name is a phone number instead of an actual name.

Updates Person nodes where the name field contains only digits (phone numbers)
to use a formatted name like "Phone: {number}" or "Unknown" if no phone is available.

Usage:
    python backend/scripts/fix_person_names.py <tenant_id> [--dry-run]
"""

import sys
import argparse
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.database.postgres_client import postgres_client
from src.tenancy.manager import TenantManager
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def is_phone_number(text: str) -> bool:
    """Check if text is likely a phone number (mostly digits, 9+ digits)."""
    if not text:
        return False
    digits = [c for c in text if c.isdigit()]
    return len(digits) >= 9 and len(digits) / len(text.replace(' ', '')) > 0.7


def fix_person_names(tenant_id: str, dry_run: bool = False):
    """
    Fix Person nodes where name is a phone number.
    
    Args:
        tenant_id: The tenant ID to fix people for
        dry_run: If True, only show what would be updated without making changes
    """
    postgres_client.connect()
    neo4j_client.connect()
    
    try:
        # Verify tenant exists
        tenant_manager = TenantManager()
        tenant = tenant_manager.get_tenant(tenant_id)
        if not tenant:
            logger.error(f"Tenant not found: {tenant_id}")
            return False
        
        logger.info(f"Fixing person names", tenant_id=tenant_id, tenant_name=tenant.name)
        
        # Find Person nodes where name is a phone number
        query = """
        MATCH (p:Person {tenant_id: $tenant_id})
        WHERE p.name IS NOT NULL
        RETURN p.id as person_id, p.name as current_name, p.phone as phone
        """
        result = neo4j_client.execute_cypher(query, {"tenant_id": tenant_id}, skip_tenant_filter=True)
        
        to_fix = []
        for row in result:
            person_id = row["person_id"]
            current_name = row.get("current_name", "")
            phone = row.get("phone")
            
            if is_phone_number(current_name):
                to_fix.append({
                    "person_id": person_id,
                    "current_name": current_name,
                    "phone": phone,
                    "new_name": f"Phone: {phone}" if phone else "Unknown"
                })
        
        count = len(to_fix)
        logger.info(f"Found {count} Person nodes with phone numbers as names")
        
        if count == 0:
            logger.info("No person names need fixing")
            return True
        
        if dry_run:
            logger.info(f"[DRY RUN] Would update {count} Person nodes")
            for item in to_fix[:10]:  # Show first 10
                logger.info(f"  {item['person_id']}: '{item['current_name']}' -> '{item['new_name']}'")
            if count > 10:
                logger.info(f"  ... and {count - 10} more")
            return True
        
        # Update Person nodes
        updated = 0
        for item in to_fix:
            update_query = """
            MATCH (p:Person {id: $person_id, tenant_id: $tenant_id})
            SET p.name = $new_name
            RETURN count(p) as updated
            """
            result = neo4j_client.execute_cypher(
                update_query,
                {
                    "person_id": item["person_id"],
                    "tenant_id": tenant_id,
                    "new_name": item["new_name"]
                },
                skip_tenant_filter=True
            )
            if result and result[0].get("updated", 0) > 0:
                updated += 1
        
        logger.info(f"Successfully updated {updated} Person nodes")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing person names", error=str(e), exc_info=True)
        return False
    finally:
        neo4j_client.close()
        postgres_client.close()


def main():
    parser = argparse.ArgumentParser(description="Fix Person nodes where name is a phone number")
    parser.add_argument("tenant_id", help="Tenant ID to fix people for")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated without making changes")
    
    args = parser.parse_args()
    
    success = fix_person_names(
        tenant_id=args.tenant_id,
        dry_run=args.dry_run
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
