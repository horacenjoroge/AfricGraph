"""Product entity model."""
from typing import Optional

from pydantic import Field

from .base import BaseNamedEntity


class Product(BaseNamedEntity):
    """Good or service."""

    sku: Optional[str] = Field(None, max_length=100)
    unit_price: Optional[float] = Field(None, gt=0)

    def to_node_properties(self) -> dict:
        """Serialize to Neo4j node property dict."""
        d = self.model_dump(mode="json")
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_node_properties(cls, data: dict) -> "Product":
        """Deserialize from Neo4j node properties."""
        return cls.model_validate(data)
