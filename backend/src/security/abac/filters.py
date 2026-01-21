"""Query-level permission filtering helpers."""
from __future__ import annotations

from typing import Dict, List

from .attributes import ResourceAttributes, SubjectAttributes
from .policies import Action


def build_filter_conditions(
    action: Action,
    subject: SubjectAttributes,
    resource_type: str,
    *,
    sensitivity_field: str = "sensitivity_level",
    owner_field: str = "owner_id",
    business_field: str = "business_id",
) -> Dict[str, List[dict]]:
    """
    Build generic filter predicates that can be applied to queries.
    Returns dict with "must" predicates; caller can adapt to SQL/Cypher/ES.
    """
    preds: List[dict] = []

    # Admin sees everything
    if subject.role.lower() == "admin":
        return {"must": preds}

    # Analysts limited to non-sensitive reads
    if subject.role.lower() == "analyst":
        preds.append({"lte": {sensitivity_field: 1}})

    # Owners limited to their resources
    owner_ids = subject.owner_ids or []
    biz_ids = subject.business_ids or []
    if owner_ids:
        preds.append({"in": {owner_field: owner_ids}})
    if biz_ids:
        preds.append({"in": {business_field: biz_ids}})

    # Default: if no ownership predicates and not admin/auditor, keep non-sensitive bound
    if not preds and action == Action.READ:
        preds.append({"lte": {sensitivity_field: 1}})

    return {"must": preds}


def apply_resource_defaults(resource_type: str, resource_id: str | None, sensitivity_level: int | None = None) -> ResourceAttributes:
    """Helper to quickly create a ResourceAttributes with defaults."""
    return ResourceAttributes(
        resource_type=resource_type,
        resource_id=resource_id,
        sensitivity_level=sensitivity_level or 0,
    )

