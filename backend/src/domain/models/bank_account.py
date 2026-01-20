"""BankAccount entity model."""
from pydantic import Field, field_validator

from .base import BaseNode


class BankAccount(BaseNode):
    """Financial account."""

    account_number: str = Field(..., min_length=1, max_length=100)
    bank_name: str = Field(..., min_length=1, max_length=200)
    currency: str = Field(..., min_length=3, max_length=3)

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
    def from_node_properties(cls, data: dict) -> "BankAccount":
        return cls.model_validate(data)
