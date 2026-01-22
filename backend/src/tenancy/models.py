"""Tenant data models."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class Tenant(BaseModel):
    """Tenant/organization model."""
    tenant_id: str = Field(..., description="Unique tenant identifier")
    name: str = Field(..., description="Tenant name")
    domain: Optional[str] = Field(None, description="Tenant domain")
    status: str = Field("active", description="Tenant status (active, suspended, inactive)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Tenant-specific configuration")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TenantConfig(BaseModel):
    """Tenant-specific configuration."""
    tenant_id: str
    key: str
    value: Any
    description: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TenantStats(BaseModel):
    """Tenant statistics."""
    tenant_id: str
    node_count: int = 0
    relationship_count: int = 0
    user_count: int = 0
    storage_bytes: int = 0
    last_activity: Optional[datetime] = None
