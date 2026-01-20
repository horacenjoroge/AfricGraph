"""Customer entity model."""
from .base import BaseNamedEntity


class Customer(BaseNamedEntity):
    """Entity that buys from a business."""

    def to_node_properties(self) -> dict:
        """Serialize to Neo4j node property dict."""
        d = self.model_dump(mode="json")
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_node_properties(cls, data: dict) -> "Customer":
        """Deserialize from Neo4j node properties."""
        return cls.model_validate(data)
