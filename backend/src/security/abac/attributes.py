"""Attribute containers for ABAC decisions."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from zoneinfo import ZoneInfo


def _safe_list(values: Optional[List[str]]) -> List[str]:
    return list(values) if values else []


@dataclass
class SubjectAttributes:
    """Who is acting."""

    user_id: str
    role: str
    business_ids: List[str] = field(default_factory=list)
    clearance_level: int = 0
    owner_ids: List[str] = field(default_factory=list)

    def owns_resource(self, owner_id: Optional[str], business_id: Optional[str]) -> bool:
        if not owner_id and not business_id:
            return False
        if owner_id and owner_id in self.owner_ids:
            return True
        if business_id and business_id in self.business_ids:
            return True
        return False


@dataclass
class ResourceAttributes:
    """What is being accessed."""

    resource_type: str
    resource_id: Optional[str] = None
    owner_id: Optional[str] = None
    business_id: Optional[str] = None
    sensitivity_level: int = 0  # 0 = public, 1 = internal, 2 = confidential, 3 = restricted


@dataclass
class EnvironmentAttributes:
    """Context of the request."""

    ip_address: str
    location: Optional[str] = None
    timezone: str = "UTC"
    hour: int = 0
    day_of_week: int = 0  # Monday=0
    user_agent: Optional[str] = None

    @classmethod
    def from_request(cls, request, timezone_name: str = "UTC") -> "EnvironmentAttributes":
        tz = ZoneInfo(timezone_name)
        now = datetime.now(tz)
        ip = request.headers.get("x-forwarded-for", "")
        if ip and "," in ip:
            ip = ip.split(",")[0].strip()
        if not ip and getattr(request, "client", None):
            ip = request.client.host or ""
        ua = request.headers.get("user-agent")
        return cls(
            ip_address=ip or "",
            user_agent=ua,
            timezone=timezone_name,
            hour=now.hour,
            day_of_week=now.weekday(),
        )

    @classmethod
    def default(cls) -> "EnvironmentAttributes":
        now = datetime.utcnow()
        return cls(ip_address="", timezone="UTC", hour=now.hour, day_of_week=now.weekday())

