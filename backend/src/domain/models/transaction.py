"""Transaction entity model."""
from datetime import date
from typing import Optional

from pydantic import Field, field_validator

from .base import BaseNode


class Transaction(BaseNode):
    """Money or value movement."""

    amount: float = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(..., min_length=3, max_length=3)
    date: date
    type: Optional[str] = Field(None, max_length=50)

    @field_validator("currency")
    @classmethod
    def currency_alpha(cls, v: str) -> str:
        if not v.isalpha():
            raise ValueError("currency must be 3-letter alphabetic code (e.g. USD, KES)")
        return v.upper()

    def to_node_properties(self) -> dict:
        d = self.model_dump(mode="json")
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_node_properties(cls, data: dict) -> "Transaction":
        return cls.model_validate(data)
