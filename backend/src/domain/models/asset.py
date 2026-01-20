"""Asset entity model."""
from typing import Optional

from pydantic import Field

from .base import BaseNode
from .enums import AssetType


class Asset(BaseNode):
    """Owned resource (physical, intangible)."""

    name: str = Field(..., min_length=1, max_length=500)
    type: str = Field(..., min_length=1, max_length=100)
    value: Optional[float] = Field(None, ge=0)
    acquired_date: Optional[str] = Field(None, max_length=10)

    def to_node_properties(self) -> dict:
        """Serialize to Neo4j node property dict."""
        d = self.model_dump(mode="json")
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_node_properties(cls, data: dict) -> "Asset":
        """Deserialize from Neo4j node properties."""
        return cls.model_validate(data)
