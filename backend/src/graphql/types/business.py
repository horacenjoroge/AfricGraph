"""Business GraphQL types."""
import strawberry
from strawberry.types import Info
from typing import Optional, List

from src.domain.models.business import Business
from src.graphql.types.person import PersonType
from src.graphql.types.transaction import TransactionType


@strawberry.type
class BusinessType:
    """GraphQL type for Business."""

    id: str
    name: str
    registration_number: Optional[str] = None
    sector: Optional[str] = None

    @strawberry.field
    def owners(self, info: Info) -> List[PersonType]:
        """Get business owners (nested relationship)."""
        from src.infrastructure.database.neo4j_client import neo4j_client
        from src.domain.models.person import Person
        
        query = """
        MATCH (b:Business {id: $business_id})<-[:OWNS]-(p:Person)
        RETURN p
        """
        rows = neo4j_client.execute_cypher(query, {"business_id": self.id})
        owners = []
        for row in rows:
            person = Person.from_node_properties(dict(row["p"]))
            owners.append(PersonType.from_domain(person))
        return owners

    @strawberry.field
    def transactions(self, info: Info, limit: int = 50) -> List[TransactionType]:
        """Get business transactions (nested relationship)."""
        from src.infrastructure.database.neo4j_client import neo4j_client
        from src.domain.models.transaction import Transaction
        
        query = """
        MATCH (b:Business {id: $business_id})<-[:INVOLVES]-(t:Transaction)
        RETURN t
        ORDER BY t.timestamp DESC
        LIMIT $limit
        """
        rows = neo4j_client.execute_cypher(query, {"business_id": self.id, "limit": limit})
        transactions = []
        for row in rows:
            trans = Transaction.from_node_properties(dict(row["t"]))
            transactions.append(TransactionType.from_domain(trans))
        return transactions

    @strawberry.field
    def suppliers(self, info: Info) -> List["BusinessType"]:
        """Get supplier businesses (nested relationship)."""
        from src.infrastructure.database.neo4j_client import neo4j_client
        from src.domain.models.business import Business
        
        query = """
        MATCH (b:Business {id: $business_id})-[:SUPPLIED_BY]->(s:Business)
        RETURN s
        """
        rows = neo4j_client.execute_cypher(query, {"business_id": self.id})
        suppliers = []
        for row in rows:
            supplier = Business.from_node_properties(dict(row["s"]))
            suppliers.append(BusinessType.from_domain(supplier))
        return suppliers

    @classmethod
    def from_domain(cls, business: Business) -> "BusinessType":
        """Create from domain model."""
        return cls(
            id=business.id,
            name=business.name,
            registration_number=business.registration_number,
            sector=business.sector,
        )
