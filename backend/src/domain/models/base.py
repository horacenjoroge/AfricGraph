"""Base models and common fields for entity inheritance."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseNode(BaseModel):
    """Base for all graph nodes: id and created_at."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        str_min_length=1,
        populate_by_name=True,
        extra="forbid",
    )

    id: str = Field(..., min_length=1, description="Unique business identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")


class BaseNamedEntity(BaseNode):
    """Base for entities with id, name, created_at."""

    name: str = Field(..., min_length=1, max_length=500)
