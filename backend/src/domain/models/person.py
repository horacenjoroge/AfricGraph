"""Person entity model."""
from typing import Optional

from pydantic import Field

from .base import BaseNamedEntity


class Person(BaseNamedEntity):
    """Individual (director, owner, contact)."""

    national_id: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)

    def to_node_properties(self) -> dict:
        """Serialize to Neo4j node property dict."""
        d = self.model_dump(mode="json")
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_node_properties(cls, data: dict) -> "Person":
        """Deserialize from Neo4j node properties."""
        return cls.model_validate(data)
