"""Payment entity model."""
from datetime import date
from typing import Optional

from pydantic import Field, field_validator

from .base import BaseNode


class Payment(BaseNode):
    """Settlement of an obligation."""

    amount: float = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    date: date
    method: Optional[str] = Field(None, max_length=50)
    reference: Optional[str] = Field(None, max_length=200)

    @field_validator("currency")
    @classmethod
    def currency_alpha(cls, v: str) -> str:
        if not v.isalpha():
            raise ValueError("currency must be 3-letter alphabetic code")
        return v.upper()

    def to_node_properties(self) -> dict:
        d = self.model_dump(mode="json")
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_node_properties(cls, data: dict) -> "Payment":
        return cls.model_validate(data)
