"""Person GraphQL types."""
import strawberry
from typing import Optional

from src.domain.models.person import Person


@strawberry.type
class PersonType:
    """GraphQL type for Person."""

    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None

    @classmethod
    def from_domain(cls, person: Person) -> "PersonType":
        """Create from domain model."""
        return cls(
            id=person.id,
            name=person.name,
            email=person.email,
            phone=person.phone,
        )
