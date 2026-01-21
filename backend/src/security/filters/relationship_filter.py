"""Helpers for relationship-level permission filters in Cypher."""
from __future__ import annotations

from typing import Dict, List, Tuple

from src.security.abac import SubjectAttributes, Action


def build_relationship_where_fragments(
    action: Action,
    subject: SubjectAttributes,
    rel_alias: str = "r",
    *,
    sensitivity_property: str = "sensitivity_level",
) -> Tuple[str, Dict]:
    """
    Build Cypher WHERE fragments and parameters for relationship visibility.

    Returns (cypher_snippet, params) where snippet is "" or "AND (...)".
    For now we mirror node sensitivity semantics on relationships.
    """
    clauses: List[str] = []
    params: Dict = {}

    role = (subject.role or "").lower()

    # Admins / auditors see all relationships.
    if role in ("admin", "auditor"):
        return "", {}

    # Analysts and regular users don't see highly sensitive relationships.
    if action == Action.READ:
        clauses.append(f"coalesce({rel_alias}.{sensitivity_property}, 0) <= 1")

    if not clauses:
        return "", {}

    return " AND (" + " AND ".join(clauses) + ")", params

