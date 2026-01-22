#!/usr/bin/env python3
"""Seed the database with sample data for testing."""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from typing import List
import random

from src.infrastructure.database.neo4j_client import neo4j_client
from src.domain.models.business import Business
from src.domain.models.person import Person
from src.domain.models.invoice import Invoice
from src.domain.models.transaction import Transaction
from src.domain.models.enums import InvoiceStatus, TransactionType
from src.api.services.business import create_business
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)

# Sample data
SECTORS = ["Technology", "Finance", "Retail", "Manufacturing", "Healthcare", "Agriculture", "Energy", "Transportation"]
BUSINESS_NAMES = [
    "Acme Corporation", "TechStart Inc", "Global Finance Ltd", "RetailMax Stores",
    "Manufacturing Pro", "HealthCare Plus", "AgriSolutions", "EnergyCo",
    "TransportHub", "Digital Services", "Investment Group", "Supply Chain Co",
    "Innovation Labs", "Business Solutions", "Market Leaders", "Growth Partners"
]

PERSON_NAMES = [
    "John Smith", "Jane Doe", "Michael Johnson", "Sarah Williams",
    "David Brown", "Emily Davis", "Robert Miller", "Lisa Wilson",
    "James Moore", "Patricia Taylor", "William Anderson", "Jennifer Thomas",
    "Richard Jackson", "Linda White", "Joseph Harris", "Barbara Martin"
]

EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "company.com", "business.com"]

# Kenyan phone number prefixes
MPESA_PHONES = ["254712", "254713", "254714", "254715", "254716", "254717", "254718", "254719"]
AIRTEL_PHONES = ["254710", "254711", "254720", "254721", "254722", "254723", "254724", "254725"]

# M-Pesa transaction descriptions
MPESA_DESCRIPTIONS = [
    "Payment from {counterparty}",
    "Received from {counterparty}",
    "Payment to {counterparty}",
    "Sent to {counterparty}",
    "Paybill 123456 - {counterparty}",
    "Buy goods - {counterparty}",
    "Airtime purchase",
    "Withdrawal at {counterparty}",
    "Deposit from {counterparty}",
    "Business payment - {counterparty}",
]

# Invoice descriptions
INVOICE_DESCRIPTIONS = [
    "Consulting Services",
    "Software Development",
    "Monthly Retainer",
    "Product Delivery",
    "Service Fee",
    "Equipment Rental",
    "Maintenance Contract",
    "Training Services",
    "Marketing Services",
    "Legal Services",
]


def create_sample_businesses(count: int = 20) -> List[str]:
    """Create sample businesses."""
    logger.info(f"Creating {count} sample businesses...")
    business_ids = []
    
    for i in range(count):
        business_id = f"BIZ{i+1:03d}"
        name = random.choice(BUSINESS_NAMES) + f" {i+1}"
        sector = random.choice(SECTORS)
        registration_number = f"REG{random.randint(100000, 999999)}"
        
        business = Business(
            id=business_id,
            name=name,
            sector=sector,
            registration_number=registration_number,
        )
        
        try:
            create_business(business)
            business_ids.append(business_id)
            logger.info(f"Created business: {business_id} - {name}")
        except Exception as e:
            logger.error(f"Failed to create business {business_id}: {e}")
    
    return business_ids


def create_sample_people(count: int = 15) -> List[str]:
    """Create sample people."""
    logger.info(f"Creating {count} sample people...")
    person_ids = []
    
    for i in range(count):
        person_id = f"PERSON{i+1:03d}"
        name = random.choice(PERSON_NAMES)
        email = f"{name.lower().replace(' ', '.')}@{random.choice(EMAIL_DOMAINS)}"
        phone = f"+2547{random.randint(10000000, 99999999)}"
        
        props = {
            "id": person_id,
            "name": name,
            "email": email,
            "phone": phone,
        }
        
        try:
            node_id = neo4j_client.merge_node("Person", person_id, props)
            person_ids.append(person_id)
            logger.info(f"Created person: {person_id} - {name}")
        except Exception as e:
            logger.error(f"Failed to create person {person_id}: {e}")
    
    return person_ids


def create_ownership_relationships(business_ids: List[str], person_ids: List[str]):
    """Create ownership relationships between people and businesses."""
    logger.info("Creating ownership relationships...")
    
    for business_id in business_ids[:10]:  # First 10 businesses
        # Each business has 1-3 owners
        num_owners = random.randint(1, 3)
        owners = random.sample(person_ids, min(num_owners, len(person_ids)))
        
        total_percentage = 0
        for i, owner_id in enumerate(owners):
            if i == len(owners) - 1:
                # Last owner gets remaining percentage
                percentage = 100 - total_percentage
            else:
                percentage = random.randint(20, 50)
                total_percentage += percentage
            
            query = """
            MATCH (b:Business {id: $business_id}), (p:Person {id: $person_id})
            MERGE (p)-[r:OWNS]->(b)
            SET r.percentage = $percentage, r.since = $since
            """
            
            neo4j_client.execute_cypher(query, {
                "business_id": business_id,
                "person_id": owner_id,
                "percentage": percentage,
                "since": (datetime.now() - timedelta(days=random.randint(30, 3650))).isoformat()
            })
        
        logger.info(f"Created ownership for {business_id} with {len(owners)} owners")


def create_supplier_relationships(business_ids: List[str]):
    """Create supplier relationships between businesses."""
    logger.info("Creating supplier relationships...")
    
    # Create supplier relationships
    for i, business_id in enumerate(business_ids[:15]):
        # Each business has 2-5 suppliers
        num_suppliers = random.randint(2, 5)
        suppliers = random.sample([b for b in business_ids if b != business_id], 
                                 min(num_suppliers, len(business_ids) - 1))
        
        for supplier_id in suppliers:
            query = """
            MATCH (b:Business {id: $business_id}), (s:Business {id: $supplier_id})
            MERGE (b)-[r:SUPPLIED_BY]->(s)
            SET r.since = $since, r.contract_value = $contract_value
            """
            
            neo4j_client.execute_cypher(query, {
                "business_id": business_id,
                "supplier_id": supplier_id,
                "since": (datetime.now() - timedelta(days=random.randint(30, 1095))).isoformat(),
                "contract_value": random.randint(10000, 500000)
            })
        
        logger.info(f"Created {len(suppliers)} suppliers for {business_id}")


def create_transactions(business_ids: List[str], count: int = 50):
    """Create sample transactions."""
    logger.info(f"Creating {count} sample transactions...")
    
    for i in range(count):
        transaction_id = f"TXN{i+1:04d}"
        from_business = random.choice(business_ids)
        to_business = random.choice([b for b in business_ids if b != from_business])
        amount = random.randint(1000, 100000)
        transaction_date = datetime.now() - timedelta(days=random.randint(0, 365))
        
        descriptions = [
            "Payment for services", "Invoice payment", "Monthly subscription",
            "Product purchase", "Service fee", "Consulting payment",
            "Equipment purchase", "Software license", "Maintenance fee"
        ]
        
        query = """
        MATCH (from:Business {id: $from_id}), (to:Business {id: $to_id})
        MERGE (from)-[t:TRANSACTION]->(to)
        SET t.id = $transaction_id,
            t.amount = $amount,
            t.currency = 'KES',
            t.date = $date,
            t.description = $description,
            t.status = $status
        """
        
        neo4j_client.execute_cypher(query, {
            "from_id": from_business,
            "to_id": to_business,
            "transaction_id": transaction_id,
            "amount": amount,
            "date": transaction_date.isoformat(),
            "description": random.choice(descriptions),
            "status": random.choice(["completed", "pending", "failed"])
        })
        
        if (i + 1) % 10 == 0:
            logger.info(f"Created {i + 1} transactions...")


def create_director_relationships(business_ids: List[str], person_ids: List[str]):
    """Create director relationships."""
    logger.info("Creating director relationships...")
    
    for business_id in business_ids[:12]:
        # Each business has 1-4 directors
        num_directors = random.randint(1, 4)
        directors = random.sample(person_ids, min(num_directors, len(person_ids)))
        
        for director_id in directors:
            query = """
            MATCH (b:Business {id: $business_id}), (p:Person {id: $person_id})
            MERGE (p)-[r:DIRECTS]->(b)
            SET r.since = $since, r.role = $role
            """
            
            roles = ["CEO", "CTO", "CFO", "Director", "Board Member"]
            
            neo4j_client.execute_cypher(query, {
                "business_id": business_id,
                "person_id": director_id,
                "since": (datetime.now() - timedelta(days=random.randint(30, 1825))).isoformat(),
                "role": random.choice(roles)
            })
        
        logger.info(f"Created {len(directors)} directors for {business_id}")


def create_mobile_money_transactions(business_ids: List[str], person_ids: List[str], count: int = 200):
    """Create realistic M-Pesa and Airtel Money transactions."""
    logger.info(f"Creating {count} mobile money transactions...")
    
    providers = ["M-Pesa", "Airtel Money"]
    transaction_types = ["payment_in", "payment_out", "merchant", "withdrawal"]
    
    for i in range(count):
        transaction_id = f"MM{random.choice(['MP', 'AM'])}{i+1:05d}"
        provider = random.choice(providers)
        txn_type = random.choice(transaction_types)
        
        # Select business and person
        business_id = random.choice(business_ids)
        person_id = random.choice(person_ids)
        
        # Get person details for counterparty
        person_query = "MATCH (p:Person {id: $person_id}) RETURN p.name as name, p.phone as phone"
        person_data = neo4j_client.execute_cypher(person_query, {"person_id": person_id})
        person_name = person_data[0]["name"] if person_data else f"Person {person_id}"
        person_phone = person_data[0].get("phone", f"{random.choice(MPESA_PHONES)}{random.randint(100000, 999999)}")
        
        # Realistic amounts for mobile money (KES)
        if txn_type == "payment_in":
            amount = random.randint(100, 50000)
        elif txn_type == "payment_out":
            amount = random.randint(50, 20000)
        elif txn_type == "merchant":
            amount = random.randint(100, 10000)
        else:  # withdrawal
            amount = random.randint(500, 50000)
        
        # Transaction date (last 6 months)
        transaction_date = datetime.now() - timedelta(days=random.randint(0, 180))
        
        # Description
        description_template = random.choice(MPESA_DESCRIPTIONS)
        description = description_template.format(counterparty=person_name)
        
        # Receipt number
        receipt_no = f"{provider[:2].upper()}{random.randint(10000000, 99999999)}"
        
        # Balance after (realistic)
        balance_after = random.randint(1000, 100000)
        
        # Create Transaction node
        transaction_props = {
            "id": transaction_id,
            "amount": float(amount),
            "currency": "KES",
            "date": transaction_date.isoformat(),
            "type": txn_type,
            "description": description,
            "source_provider": provider,
            "provider_txn_id": receipt_no,
            "balance_after": float(balance_after),
            "receipt_no": receipt_no,
            "created_at": datetime.now().isoformat(),
        }
        
        neo4j_client.merge_node("Transaction", transaction_id, transaction_props)
        
        # Link transaction to business
        query1 = """
        MATCH (t:Transaction {id: $transaction_id}), (b:Business {id: $business_id})
        MERGE (b)-[:HAS_TRANSACTION]->(t)
        """
        neo4j_client.execute_cypher(query1, {
            "transaction_id": transaction_id,
            "business_id": business_id
        })
        
        # Link transaction to person (counterparty)
        query2 = """
        MATCH (t:Transaction {id: $transaction_id}), (p:Person {id: $person_id})
        MERGE (t)-[:INVOLVES]->(p)
        SET t.counterparty = $person_name, t.counterparty_phone = $person_phone
        """
        neo4j_client.execute_cypher(query2, {
            "transaction_id": transaction_id,
            "person_id": person_id,
            "person_name": person_name,
            "person_phone": person_phone
        })
        
        if (i + 1) % 50 == 0:
            logger.info(f"Created {i + 1} mobile money transactions...")
    
    logger.info(f"Created {count} mobile money transactions")


def create_invoices(business_ids: List[str], count: int = 100):
    """Create realistic invoices."""
    logger.info(f"Creating {count} invoices...")
    
    invoice_statuses = ["draft", "sent", "paid", "overdue", "cancelled"]
    
    for i in range(count):
        invoice_id = f"INV{i+1:05d}"
        invoice_number = f"INV-{datetime.now().year}-{random.randint(1000, 9999)}"
        
        # Select businesses (from and to)
        from_business = random.choice(business_ids)
        to_business = random.choice([b for b in business_ids if b != from_business])
        
        # Invoice dates
        issue_date = datetime.now() - timedelta(days=random.randint(0, 180))
        due_date = issue_date + timedelta(days=random.randint(7, 60))
        status = random.choice(invoice_statuses)
        
        # If paid, set paid_date
        paid_date = None
        if status == "paid":
            paid_date = issue_date + timedelta(days=random.randint(1, (due_date - issue_date).days))
        
        # Amounts
        subtotal = random.randint(5000, 500000)
        tax_rate = 0.16  # 16% VAT in Kenya
        tax_amount = subtotal * tax_rate
        total_amount = subtotal + tax_amount
        
        # Description
        description = random.choice(INVOICE_DESCRIPTIONS)
        
        # Create Invoice node (using Invoice model structure)
        invoice_props = {
            "id": invoice_id,
            "number": invoice_number,
            "amount": float(total_amount),  # Invoice model uses 'amount' not 'total_amount'
            "currency": "KES",
            "issue_date": issue_date.isoformat(),
            "due_date": due_date.isoformat(),
            "status": status,
            "description": description,
            "subtotal": float(subtotal),
            "tax_amount": float(tax_amount),
            "created_at": datetime.now().isoformat(),
        }
        
        if paid_date:
            invoice_props["paid_date"] = paid_date.isoformat()
        
        neo4j_client.merge_node("Invoice", invoice_id, invoice_props)
        
        # Link invoice to businesses
        query1 = """
        MATCH (i:Invoice {id: $invoice_id}), (from:Business {id: $from_id})
        MERGE (from)-[:ISSUED]->(i)
        """
        neo4j_client.execute_cypher(query1, {
            "invoice_id": invoice_id,
            "from_id": from_business
        })
        
        query2 = """
        MATCH (i:Invoice {id: $invoice_id}), (to:Business {id: $to_id})
        MERGE (i)-[:ISSUED_TO]->(to)
        """
        neo4j_client.execute_cypher(query2, {
            "invoice_id": invoice_id,
            "to_id": to_business
        })
        
        # If paid, create payment transaction
        if status == "paid" and paid_date:
            payment_id = f"PAY{i+1:05d}"
            payment_props = {
                "id": payment_id,
                "amount": float(total_amount),
                "currency": "KES",
                "date": paid_date.isoformat(),
                "type": "payment",
                "description": f"Payment for {invoice_number}",
                "invoice_id": invoice_id,
                "created_at": datetime.now().isoformat(),
            }
            
            neo4j_client.merge_node("Payment", payment_id, payment_props)
            
            # Link payment to invoice
            query3 = """
            MATCH (p:Payment {id: $payment_id}), (i:Invoice {id: $invoice_id})
            MERGE (p)-[:PAYS]->(i)
            """
            neo4j_client.execute_cypher(query3, {
                "payment_id": payment_id,
                "invoice_id": invoice_id
            })
            
            # Link payment to businesses
            query4 = """
            MATCH (p:Payment {id: $payment_id}), (from:Business {id: $from_id}), (to:Business {id: $to_id})
            MERGE (from)-[:MADE_PAYMENT]->(p)
            MERGE (p)-[:PAYMENT_TO]->(to)
            """
            neo4j_client.execute_cypher(query4, {
                "payment_id": payment_id,
                "from_id": from_business,
                "to_id": to_business
            })
        
        if (i + 1) % 20 == 0:
            logger.info(f"Created {i + 1} invoices...")
    
    logger.info(f"Created {count} invoices")


def create_realistic_business_scenarios(business_ids: List[str], person_ids: List[str]):
    """Create realistic business scenarios with complex relationships."""
    logger.info("Creating realistic business scenarios...")
    
    # Create a business group (parent company with subsidiaries)
    parent_id = business_ids[0]
    subsidiaries = business_ids[1:4]
    
    for sub_id in subsidiaries:
        query = """
        MATCH (parent:Business {id: $parent_id}), (sub:Business {id: $sub_id})
        MERGE (sub)-[:SUBSIDIARY_OF]->(parent)
        SET sub.parent_company = $parent_id
        """
        neo4j_client.execute_cypher(query, {
            "parent_id": parent_id,
            "sub_id": sub_id
        })
    
    logger.info(f"Created business group with {len(subsidiaries)} subsidiaries")
    
    # Create shared directors (people directing multiple businesses)
    shared_directors = person_ids[:3]
    for director_id in shared_directors:
        businesses = random.sample(business_ids[5:10], 3)
        for business_id in businesses:
            query = """
            MATCH (p:Person {id: $director_id}), (b:Business {id: $business_id})
            MERGE (p)-[r:DIRECTS]->(b)
            SET r.since = $since, r.role = 'Director'
            """
            neo4j_client.execute_cypher(query, {
                "director_id": director_id,
                "business_id": business_id,
                "since": (datetime.now() - timedelta(days=random.randint(365, 1825))).isoformat()
            })
    
    logger.info(f"Created shared directors across multiple businesses")


def main():
    """Main seeding function."""
    logger.info("Starting data seeding...")
    
    try:
        # Connect to Neo4j
        neo4j_client.connect()
        logger.info("Connected to Neo4j")
        
        # Create businesses
        business_ids = create_sample_businesses(20)
        
        # Create people
        person_ids = create_sample_people(15)
        
        # Create relationships
        create_ownership_relationships(business_ids, person_ids)
        create_supplier_relationships(business_ids)
        create_director_relationships(business_ids, person_ids)
        create_transactions(business_ids, 50)
        
        # Create realistic business scenarios
        create_realistic_business_scenarios(business_ids, person_ids)
        
        # Create mobile money transactions (M-Pesa and Airtel)
        create_mobile_money_transactions(business_ids, person_ids, 200)
        
        # Create invoices
        create_invoices(business_ids, 100)
        
        logger.info("=" * 60)
        logger.info("Data seeding completed successfully!")
        logger.info("=" * 60)
        logger.info(f"Created:")
        logger.info(f"  - {len(business_ids)} businesses")
        logger.info(f"  - {len(person_ids)} people")
        logger.info(f"  - Ownership, supplier, and director relationships")
        logger.info(f"  - 50 business-to-business transactions")
        logger.info(f"  - 200 mobile money transactions (M-Pesa & Airtel)")
        logger.info(f"  - 100 invoices with payment relationships")
        logger.info(f"  - Complex business scenarios (groups, shared directors)")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during seeding: {e}", exc_info=True)
        sys.exit(1)
    finally:
        neo4j_client.close()


if __name__ == "__main__":
    main()
