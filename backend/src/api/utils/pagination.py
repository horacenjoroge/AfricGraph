"""Pagination utilities."""
from typing import Generic, List, TypeVar

from src.api.schemas.common import PaginatedResponse

T = TypeVar("T")


def paginate(items: List[T], total: int, limit: int, offset: int) -> PaginatedResponse[T]:
    """Create paginated response."""
    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(items)) < total,
    )
