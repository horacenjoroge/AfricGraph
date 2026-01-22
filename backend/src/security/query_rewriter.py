"""Permission-aware Cypher query rewriting utilities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from src.security.abac import Action, SubjectAttributes

from src.security.filters.node_filter import build_node_where_fragments
from src.security.filters.relationship_filter import build_relationship_where_fragments


@dataclass
class RewrittenQuery:
    cypher: str
    params: Dict


def _append_where(original: str, extra_where: str) -> str:
    """
    Append an "AND (...)" fragment to a Cypher query.
    If there is no WHERE, we try to inject one after MATCH <alias>.
    This is intentionally conservative and used only for our own templates.
    """
    if not extra_where:
        return original

    # If there is already a WHERE, just append.
    lower = original.lower()
    if " where " in lower:
        # Assume extra_where already starts with " AND ...".
        return original + extra_where

    # Otherwise, inject WHERE after the first MATCH ... <alias>.
    # This is sufficient for our simple templates (e.g. MATCH (n:Label)...).
    idx = lower.find("match ")
    if idx == -1:
        # Fallback: just append WHERE at the end.
        return original + " WHERE 1=1" + extra_where
    # Find end of MATCH clause line.
    end_idx = original.find("\n", idx)
    if end_idx == -1:
        end_idx = len(original)
    before = original[:end_idx]
    after = original[end_idx:]
    return before + " WHERE 1=1" + extra_where + after


def rewrite_node_query_with_permissions(
    cypher: str,
    params: Optional[Dict],
    *,
    action: "Action",
    subject: "SubjectAttributes",
    node_alias: str = "n",
) -> RewrittenQuery:
    """Apply node-level permission filters to a Cypher query that returns nodes."""
    from src.security.abac import Action, SubjectAttributes  # Import here to avoid circular import
    params = dict(params or {})
    frag, p = build_node_where_fragments(action, subject, node_alias=node_alias)
    if not frag:
        return RewrittenQuery(cypher=cypher, params=params)
    rewritten = _append_where(cypher, frag)
    params.update(p)
    return RewrittenQuery(cypher=rewritten, params=params)


def rewrite_traversal_with_permissions(
    cypher: str,
    params: Optional[Dict],
    *,
    action: "Action",
    subject: "SubjectAttributes",
    node_alias: str = "n",
    rel_alias: str = "r",
) -> RewrittenQuery:
    """
    Apply node and relationship-level filters to traversal-style queries.
    Assumes aliases `n` for nodes and `r` for relationships in WITH/RETURN.
    """
    from src.security.abac import Action, SubjectAttributes  # Import here to avoid circular import
    params = dict(params or {})
    node_frag, node_p = build_node_where_fragments(action, subject, node_alias=node_alias)
    rel_frag, rel_p = build_relationship_where_fragments(action, subject, rel_alias=rel_alias)
    combined = ""
    if node_frag:
        combined += node_frag
    if rel_frag:
        combined += rel_frag
    if not combined:
        return RewrittenQuery(cypher=cypher, params=params)
    rewritten = _append_where(cypher, combined)
    params.update(node_p)
    params.update(rel_p)
    return RewrittenQuery(cypher=rewritten, params=params)

