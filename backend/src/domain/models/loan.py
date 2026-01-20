"""Loan entity model."""
from datetime import date
from typing import Optional

from pydantic import Field, field_validator, model_validator

from .base import BaseNode
from .enums import LoanStatus


class Loan(BaseNode):
    """Credit facility."""

    principal: float = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    start_date: date
    status: LoanStatus
    end_date: Optional[date] = None
    interest_rate: Optional[float] = Field(None, ge=0, le=100)

    @field_validator("currency")
    @classmethod
    def currency_alpha(cls, v: str) -> str:
        if not v.isalpha():
            raise ValueError("currency must be 3-letter alphabetic code")
        return v.upper()

    @model_validator(mode="after")
    def end_after_start(self) -> "Loan":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self

    def to_node_properties(self) -> dict:
        d = self.model_dump(mode="json")
        d["status"] = d["status"].value
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_node_properties(cls, data: dict) -> "Loan":
        if isinstance(data.get("status"), str):
            data = {**data, "status": LoanStatus(data["status"])}
        return cls.model_validate(data)
