"""Attribute-Based Access Control engine."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.config.settings import settings
from src.infrastructure.audit import audit_logger
from src.infrastructure.logging import get_logger

from .attributes import EnvironmentAttributes, ResourceAttributes, SubjectAttributes
from .cache import PermissionCache
from .policies import Action, evaluate_policies

logger = get_logger(__name__)


@dataclass
class Decision:
    allowed: bool
    policy: str
    reason: str

    def to_dict(self) -> dict:
        return {"allowed": self.allowed, "policy": self.policy, "reason": self.reason}


class AbacEngine:
    """Evaluate ABAC policies with caching and auditing."""

    def __init__(
        self,
        *,
        cache: Optional[PermissionCache] = None,
        business_hours_start: int | None = None,
        business_hours_end: int | None = None,
        allowed_ips: Optional[list[str]] = None,
    ) -> None:
        self.cache = cache or PermissionCache()
        self.business_hours = (
            business_hours_start if business_hours_start is not None else settings.abac_business_hours_start,
            business_hours_end if business_hours_end is not None else settings.abac_business_hours_end,
        )
        self.allowed_ips = allowed_ips if allowed_ips is not None else list(settings.abac_allowed_ips or [])

    def _cache_key(
        self,
        action: Action,
        subject: SubjectAttributes,
        resource: ResourceAttributes,
        env: EnvironmentAttributes,
    ) -> str:
        return (
            f"sub:{subject.user_id}:{subject.role}:act:{action.value}:"
            f"res:{resource.resource_type}:{resource.resource_id}:{resource.sensitivity_level}:ip:{env.ip_address}"
        )

    def authorize(
        self,
        action: Action,
        subject: SubjectAttributes,
        resource: ResourceAttributes,
        env: Optional[EnvironmentAttributes] = None,
        *,
        audit: bool = True,
    ) -> Decision:
        env = env or EnvironmentAttributes.default()
        key = self._cache_key(action, subject, resource, env)
        cached = self.cache.get(key)
        if cached:
            return cached

        allowed, policy_name, reason = evaluate_policies(
            action,
            subject,
            resource,
            env,
            business_hours=self.business_hours,
            allowed_ips=self.allowed_ips,
        )
        decision = Decision(allowed=allowed, policy=policy_name, reason=reason)
        self.cache.set(key, decision)

        if audit:
            try:
                audit_logger.log_permission(
                    granted=decision.allowed,
                    actor_id=subject.user_id,
                    resource_type=resource.resource_type,
                    resource_id=resource.resource_id,
                    reason=f"{policy_name}: {reason}",
                    extra={
                        "role": subject.role,
                        "business_ids": subject.business_ids,
                        "clearance_level": subject.clearance_level,
                        "sensitivity_level": resource.sensitivity_level,
                    },
                    ip_address=env.ip_address,
                )
            except Exception:
                logger.exception("Failed to log permission decision")

        return decision

    def clear_cache(self) -> None:
        self.cache.invalidate()

    def clear_subject(self, subject_id: str) -> None:
        self.cache.invalidate_subject(subject_id)


# Shared engine instance
abac_engine = AbacEngine()

