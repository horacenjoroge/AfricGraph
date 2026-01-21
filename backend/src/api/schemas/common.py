"""Common API schemas for pagination, filtering, etc."""
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    items: List[T]
    total: int
    limit: int
    offset: int
    has_more: bool


class FilterParams(BaseModel):
    """Common filter parameters."""

    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)
    sort_by: Optional[str] = None
    sort_order: str = Field("asc", regex="^(asc|desc)$")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
