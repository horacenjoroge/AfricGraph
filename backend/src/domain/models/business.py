"""Business entity model."""
from typing import Optional

from pydantic import Field

from .base import BaseNamedEntity


class Business(BaseNamedEntity):
    """Registered company or venture."""

    registration_number: Optional[str] = Field(None, max_length=100)
    sector: Optional[str] = Field(None, max_length=200)

    def to_node_properties(self) -> dict:
        """Serialize to Neo4j node property dict."""
        d = self.model_dump(mode="json")
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_node_properties(cls, data: dict) -> "Business":
        """Deserialize from Neo4j node properties."""
        return cls.model_validate(data)
