"""Invoice entity model."""
from datetime import date
from typing import Optional

from pydantic import Field, field_validator, model_validator

from .base import BaseNode
from .enums import InvoiceStatus


class Invoice(BaseNode):
    """Billing document."""

    number: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    issue_date: date
    status: InvoiceStatus
    due_date: Optional[date] = None

    @field_validator("currency")
    @classmethod
    def currency_alpha(cls, v: str) -> str:
        if not v.isalpha():
            raise ValueError("currency must be 3-letter alphabetic code")
        return v.upper()

    @model_validator(mode="after")
    def due_after_issue(self) -> "Invoice":
        if self.due_date is not None and self.due_date < self.issue_date:
            raise ValueError("due_date must be on or after issue_date")
        return self

    def to_node_properties(self) -> dict:
        d = self.model_dump(mode="json")
        d["status"] = d["status"].value
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_node_properties(cls, data: dict) -> "Invoice":
        if isinstance(data.get("status"), str):
            data = {**data, "status": InvoiceStatus(data["status"])}
        return cls.model_validate(data)
