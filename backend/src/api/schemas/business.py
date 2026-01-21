"""Business API schemas."""
from typing import Optional

from pydantic import BaseModel, Field


class BusinessCreate(BaseModel):
    """Request schema for creating a business."""

    id: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=500)
    registration_number: Optional[str] = Field(None, max_length=100)
    sector: Optional[str] = Field(None, max_length=200)


class BusinessUpdate(BaseModel):
    """Request schema for updating a business."""

    name: Optional[str] = Field(None, min_length=1, max_length=500)
    registration_number: Optional[str] = Field(None, max_length=100)
    sector: Optional[str] = Field(None, max_length=200)


class BusinessResponse(BaseModel):
    """Response schema for business."""

    id: str
    name: str
    registration_number: Optional[str] = None
    sector: Optional[str] = None

    class Config:
        from_attributes = True


class BusinessSearchRequest(BaseModel):
    """Request schema for business search."""

    query: Optional[str] = None
    sector: Optional[str] = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class BusinessSearchResponse(BaseModel):
    """Response schema for business search."""

    businesses: list[BusinessResponse]
    total: int
    limit: int
    offset: int
