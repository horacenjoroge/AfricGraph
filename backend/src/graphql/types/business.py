"""Business GraphQL types."""
import strawberry
from typing import Optional, List

from src.domain.models.business import Business


@strawberry.type
class BusinessType:
    """GraphQL type for Business."""

    id: str
    name: str
    registration_number: Optional[str] = None
    sector: Optional[str] = None

    @classmethod
    def from_domain(cls, business: Business) -> "BusinessType":
        """Create from domain model."""
        return cls(
            id=business.id,
            name=business.name,
            registration_number=business.registration_number,
            sector=business.sector,
        )
