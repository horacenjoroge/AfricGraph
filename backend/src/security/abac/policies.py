"""ABAC policies for AfricGraph."""
from __future__ import annotations

from enum import Enum
from typing import List, Optional, Tuple

from .attributes import EnvironmentAttributes, ResourceAttributes, SubjectAttributes


class Action(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


def _business_hours_ok(env: EnvironmentAttributes, start: int, end: int, weekdays_only: bool = True) -> bool:
    if weekdays_only and env.day_of_week > 4:  # 0-4 are Mon-Fri
        return False
    return start <= env.hour < end


def _ip_allowed(env: EnvironmentAttributes, allowed_ips: List[str]) -> bool:
    if not allowed_ips:
        return True
    return env.ip_address in allowed_ips


def evaluate_policies(
    action: Action,
    subject: SubjectAttributes,
    resource: ResourceAttributes,
    env: EnvironmentAttributes,
    *,
    business_hours: Tuple[int, int],
    allowed_ips: List[str],
) -> Tuple[bool, str, str]:
    """
    Returns (allowed, policy_name, reason).
    Policy precedence: admin -> time/ip -> auditor/analyst -> ownership -> sensitivity -> default deny.
    """
    start, end = business_hours

    # Admins see/do everything regardless of time or IP.
    if subject.role.lower() == "admin":
        return True, "admin_allow_all", "admin role"

    # Time/IP controls apply to non-admins.
    if not _business_hours_ok(env, start, end):
        return False, "time_window_block", "outside business hours"
    if not _ip_allowed(env, allowed_ips):
        return False, "ip_restricted", f"ip {env.ip_address} not allowed"

    # Auditors: can read everything, cannot modify.
    if subject.role.lower() == "auditor":
        if action == Action.READ:
            return True, "auditor_read", "auditor read-only"
        return False, "auditor_no_write", "auditor cannot modify"

    # Analysts: can read non-sensitive only, cannot modify.
    if subject.role.lower() == "analyst":
        if action == Action.READ and (resource.sensitivity_level or 0) <= 1:
            return True, "analyst_non_sensitive", "analyst read non-sensitive"
        return False, "analyst_restricted", "analyst limited to non-sensitive read"

    # Owners (business or direct owner id) can read/write their resources.
    if subject.owns_resource(resource.owner_id, resource.business_id):
        return True, "owner_access", "owner of resource"

    # Generic sensitivity rule: high sensitivity requires clearance.
    if (resource.sensitivity_level or 0) > subject.clearance_level:
        return False, "insufficient_clearance", "clearance below sensitivity"

    # Default: allow read of non-sensitive, deny write.
    if action == Action.READ and (resource.sensitivity_level or 0) <= 1:
        return True, "default_low_sensitivity", "low sensitivity read"

    return False, "default_deny", "no matching allow rule"

