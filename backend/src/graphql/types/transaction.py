"""Transaction GraphQL types."""
import strawberry
from typing import Optional
from datetime import datetime

from src.domain.models.transaction import Transaction


@strawberry.type
class TransactionType:
    """GraphQL type for Transaction."""

    id: str
    amount: float
    currency: str
    timestamp: datetime
    transaction_type: str
    description: Optional[str] = None

    @classmethod
    def from_domain(cls, transaction: Transaction) -> "TransactionType":
        """Create from domain model."""
        return cls(
            id=transaction.id,
            amount=transaction.amount,
            currency=transaction.currency,
            timestamp=transaction.timestamp,
            transaction_type=transaction.transaction_type,
            description=transaction.description,
        )
