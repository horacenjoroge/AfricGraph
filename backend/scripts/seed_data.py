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
        
        logger.info("Data seeding completed successfully!")
        logger.info(f"Created: {len(business_ids)} businesses, {len(person_ids)} people, and relationships")
        
    except Exception as e:
        logger.error(f"Error during seeding: {e}", exc_info=True)
        sys.exit(1)
    finally:
        neo4j_client.close()


if __name__ == "__main__":
    main()
