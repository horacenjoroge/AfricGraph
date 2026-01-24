#!/usr/bin/env python3
"""Migration script to update existing Transaction nodes with new properties."""
import os
import sys
from pathlib import Path

# Set environment variables before importing
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("NEO4J_URI", os.getenv("NEO4J_URI", "bolt://neo4j:7687"))
os.environ.setdefault("NEO4J_USER", os.getenv("NEO4J_USER", "neo4j"))
os.environ.setdefault("NEO4J_PASSWORD", os.getenv("NEO4J_PASSWORD", ""))

from neo4j import GraphDatabase
import re

# Direct connection
neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "")

neo4j_driver = GraphDatabase.driver(
    neo4j_uri,
    auth=(neo4j_user, neo4j_password)
)

# Patterns for extracting counterparty with direction
_FUNDS_RECEIVED_FROM = re.compile(r"funds\s+received\s+from\s+(\d{10,12})\s*[-–]\s*([A-Za-z\s\.\-]+?)(?:\s+completed|\s+unknown|\s*$)", re.I)
_FUNDS_SENT_TO = re.compile(r"funds\s+sent\s+to\s+(\d{10,12})\s*[-–]\s*([A-Za-z\s\.\-]+?)(?:\s+completed|\s+unknown|\s*$)", re.I)
_TO_PATTERN = re.compile(r"\bto\s+(\d{10,12})\s*[-–]\s*([A-Za-z\s\.\-]+?)(?:\s+completed|\s+unknown|\s*$)", re.I)
_FROM_PATTERN = re.compile(r"\bfrom\s+(\d{10,12})\s*[-–]\s*([A-Za-z\s\.\-]+?)(?:\s+completed|\s+unknown|\s*$)", re.I)
_PHONE_NAME = re.compile(r"(\d{10,12})\s*[-–]\s*([A-Za-z\s\.\-]+?)(?:\s+completed|\s+unknown|\s*$)", re.I)
_PHONE = re.compile(r"\b(254\d{9}|07\d{8}|01\d{8}|256\d{9}|0\d{8,9})\b")


def normalize_phone(phone: str) -> str:
    """Normalize phone number to E.164 format."""
    phone = re.sub(r'[^\d+]', '', phone)
    if phone.startswith('+'):
        return phone
    if phone.startswith('0'):
        return '+254' + phone[1:]
    if len(phone) == 9:
        return '+254' + phone
    if len(phone) == 12 and phone.startswith('254'):
        return '+' + phone
    return phone


def extract_counterparty_with_phone(description: str) -> tuple:
    """Extract counterparty name, phone, and direction from description."""
    if not description:
        return None, None, None
    
    text = str(description).strip()
    direction = None
    phone = None
    name = None
    
    # Check for "Funds received from" pattern
    m = _FUNDS_RECEIVED_FROM.search(text)
    if m:
        direction = "from"
        phone = m.group(1)
        name = m.group(2).strip() if m.group(2) else None
        return name, phone, direction
    
    # Check for "Funds sent to" pattern
    m = _FUNDS_SENT_TO.search(text)
    if m:
        direction = "to"
        phone = m.group(1)
        name = m.group(2).strip() if m.group(2) else None
        return name, phone, direction
    
    # Check for generic "to phone - name" pattern
    m = _TO_PATTERN.search(text)
    if m:
        direction = "to"
        phone = m.group(1)
        name = m.group(2).strip() if m.group(2) else None
        return name, phone, direction
    
    # Check for generic "from phone - name" pattern
    m = _FROM_PATTERN.search(text)
    if m:
        direction = "from"
        phone = m.group(1)
        name = m.group(2).strip() if m.group(2) else None
        return name, phone, direction
    
    # Try generic phone-name pattern
    m = _PHONE_NAME.search(text)
    if m:
        phone = m.group(1)
        name = m.group(2).strip() if m.group(2) else None
        if "received" in text.lower() or "from" in text.lower():
            direction = "from"
        elif "sent" in text.lower() or "to" in text.lower():
            direction = "to"
        return name, phone, direction
    
    # Fallback: try to extract phone only
    pm = _PHONE.search(text)
    if pm:
        phone = pm.group(1)
        if "received" in text.lower() or "from" in text.lower():
            direction = "from"
        elif "sent" in text.lower() or "to" in text.lower():
            direction = "to"
        return None, phone, direction
    
    return None, None, None


def convert_usd_to_kes(usd_amount: float) -> float:
    """Convert USD amount back to KES (approximate, using rate 0.0077)."""
    # If rate is 1 KES = 0.0077 USD, then 1 USD = 1/0.0077 KES ≈ 129.87 KES
    # So to convert USD back: USD_amount / 0.0077
    return usd_amount / 0.0077


def migrate_transactions():
    """Update existing Transaction nodes with new properties."""
    print("="*80)
    print("Transaction Properties Migration Script")
    print("="*80)
    
    updated_count = 0
    skipped_count = 0
    
    with neo4j_driver.session() as session:
        # Get all transactions that need updating (those with USD currency or missing new properties)
        query = """
        MATCH (t:Transaction)
        WHERE t.id STARTS WITH 'mpesa:' OR t.id STARTS WITH 'airtel:'
        RETURN t.id as id, properties(t) as props
        """
        
        result = session.run(query)
        
        for record in result:
            tx_id = record["id"]
            props = dict(record["props"])
            
            # Check if already has new properties
            if props.get("counterparty_name") and props.get("counterparty_phone") and props.get("direction"):
                print(f"Skipping {tx_id} - already has new properties")
                skipped_count += 1
                continue
            
            description = props.get("description", "")
            currency = props.get("currency", "USD")
            amount = props.get("amount", 0)
            tx_type = props.get("type", "")
            
            # Extract counterparty info
            counterparty_name, counterparty_phone_raw, direction = extract_counterparty_with_phone(description)
            
            # Normalize phone
            counterparty_phone = None
            if counterparty_phone_raw:
                counterparty_phone = normalize_phone(counterparty_phone_raw)
            
            # Convert currency and amount if needed
            if currency == "USD" and amount > 0:
                # Convert back to KES (approximate)
                original_amount = convert_usd_to_kes(amount)
                new_currency = "KES"
            else:
                original_amount = amount
                new_currency = currency if currency else "KES"
            
            # Infer direction from type if not extracted
            if not direction:
                if tx_type == "payment_in":
                    direction = "from"
                elif tx_type == "payment_out":
                    direction = "to"
            
            # Extract provider_txn_id from source_id
            provider_txn_id = None
            if ":" in tx_id:
                provider_txn_id = tx_id.split(":", 1)[1]
            
            # Build SET clause dynamically based on what we have
            set_clauses = []
            params = {"tx_id": tx_id}
            
            # Always update amount and currency
            set_clauses.append("t.amount = $amount")
            set_clauses.append("t.currency = $currency")
            params["amount"] = original_amount
            params["currency"] = new_currency
            
            # Add optional properties only if they have values
            if counterparty_name:
                set_clauses.append("t.counterparty_name = $counterparty_name")
                params["counterparty_name"] = counterparty_name
            
            if counterparty_phone:
                set_clauses.append("t.counterparty_phone = $counterparty_phone")
                params["counterparty_phone"] = counterparty_phone
            
            if direction:
                set_clauses.append("t.direction = $direction")
                params["direction"] = direction
            
            if provider_txn_id:
                set_clauses.append("t.provider_txn_id = $provider_txn_id")
                params["provider_txn_id"] = provider_txn_id
            
            # Build and execute update query
            update_query = f"""
            MATCH (t:Transaction {{id: $tx_id}})
            SET {', '.join(set_clauses)}
            RETURN t.id as id
            """
            
            try:
                session.run(update_query, params)
                print(f"Updated {tx_id}: amount={original_amount:.2f} {new_currency}, direction={direction}, counterparty={counterparty_name or counterparty_phone or 'N/A'}")
                updated_count += 1
            except Exception as e:
                print(f"Error updating {tx_id}: {e}")
    
    print("\n" + "="*80)
    print(f"Migration completed!")
    print(f"  Updated: {updated_count} transactions")
    print(f"  Skipped: {skipped_count} transactions (already have new properties)")
    print("="*80)
    print("\nNext steps:")
    print("1. Clear the cache (Admin → Cache Management → Clear Graph Cache)")
    print("2. Refresh the frontend page")
    print("3. Check the transaction properties again")


if __name__ == "__main__":
    try:
        migrate_transactions()
    finally:
        neo4j_driver.close()
