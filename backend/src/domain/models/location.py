"""Location entity model."""
from typing import Optional

from pydantic import Field

from .base import BaseNode


class Location(BaseNode):
    """Physical or registered address."""

    address: str = Field(..., min_length=1, max_length=500)
    country: str = Field(..., min_length=2, max_length=3)
    region: Optional[str] = Field(None, max_length=200)

    def to_node_properties(self) -> dict:
        d = self.model_dump(mode="json")
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_node_properties(cls, data: dict) -> "Location":
        return cls.model_validate(data)
