"""Helpers for node-level permission filters in Cypher."""
from __future__ import annotations

from typing import Dict, List, Tuple

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.security.abac import SubjectAttributes, Action


def build_node_where_fragments(
    action: "Action",
    subject: "SubjectAttributes",
    node_alias: str = "n",
    *,
    sensitivity_property: str = "sensitivity_level",
    owner_property: str = "owner_id",
    business_property: str = "business_id",
) -> Tuple[str, Dict]:
    """
    Build Cypher WHERE fragments and parameters enforcing node-level permissions.

    Returns (cypher_snippet, params) where cypher_snippet is either "" or:
      "AND (...)" suitable to append to an existing WHERE clause.
    """
    from src.security.abac import Action  # Import here to avoid circular import
    
    clauses: List[str] = []
    params: Dict = {}

    role = (subject.role or "").lower()

    # Admins: no node filter.
    if role == "admin":
        return "", {}

    # Analysts: non-sensitive only.
    if role == "analyst":
        clauses.append(f"{node_alias}.{sensitivity_property} <= $perm_sensitivity_max")
        params["perm_sensitivity_max"] = 1

    # Owners: restrict to owned business/resources.
    if subject.owner_ids:
        clauses.append(f"{node_alias}.{owner_property} IN $perm_owner_ids")
        params["perm_owner_ids"] = subject.owner_ids
    if subject.business_ids:
        clauses.append(f"{node_alias}.{business_property} IN $perm_business_ids")
        params["perm_business_ids"] = subject.business_ids

    # Default for non-admin/auditor: if no ownership or sensitivity predicates, at least bound sensitivity for reads.
    if not clauses and action == Action.READ:
        clauses.append(f"coalesce({node_alias}.{sensitivity_property}, 0) <= 1")

    if not clauses:
        return "", {}

    return " AND (" + " AND ".join(clauses) + ")", params

