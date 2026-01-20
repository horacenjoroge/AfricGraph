"""Relationship property models for graph edges."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OwnsProperties(BaseModel):
    """Properties for (Person|Business)-[:OWNS]->(Business|Asset)."""

    model_config = ConfigDict(extra="forbid")

    percentage: Optional[float] = Field(None, ge=0, le=100)
    since: Optional[date] = None

    def to_rel_properties(self) -> dict:
        return {k: v for k, v in self.model_dump(mode="json").items() if v is not None}


class DirectorOfProperties(BaseModel):
    """Properties for (Person)-[:DIRECTOR_OF]->(Business)."""

    model_config = ConfigDict(extra="forbid")

    role: Optional[str] = Field(None, max_length=200)
    since: Optional[date] = None

    def to_rel_properties(self) -> dict:
        return {k: v for k, v in self.model_dump(mode="json").items() if v is not None}


class BuysFromProperties(BaseModel):
    """Properties for (Business)-[:BUYS_FROM]->(Supplier)."""

    model_config = ConfigDict(extra="forbid")

    since: Optional[date] = None

    def to_rel_properties(self) -> dict:
        return {k: v for k, v in self.model_dump(mode="json").items() if v is not None}


class InvolvesProperties(BaseModel):
    """Properties for (Transaction)-[:INVOLVES]->(Person|Business|BankAccount)."""

    model_config = ConfigDict(extra="forbid")

    role: Optional[str] = Field(None, max_length=200)

    def to_rel_properties(self) -> dict:
        return {k: v for k, v in self.model_dump(mode="json").items() if v is not None}
