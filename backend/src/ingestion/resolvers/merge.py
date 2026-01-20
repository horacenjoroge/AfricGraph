"""Merge strategies for conflicting data from multiple sources."""
from enum import Enum
from typing import List, Optional, Sequence, Tuple

from src.config.settings import settings

from ..normalizers.canonical import CanonicalContact


class MergeStrategy(str, Enum):
    KEEP_FIRST = "keep_first"
    KEEP_NEWEST = "keep_newest"
    AUTHORITATIVE_SOURCE = "authoritative_source"
    MANUAL = "manual"


def _updated_ts(c: CanonicalContact) -> float:
    u = c.updated_at
    if u is None:
        return 0.0
    return u.timestamp() if hasattr(u, "timestamp") else 0.0


def merge_contacts(
    contacts: Sequence[CanonicalContact],
    strategy: MergeStrategy = MergeStrategy.KEEP_NEWEST,
    authoritative_order: Optional[List[str]] = None,
) -> Tuple[CanonicalContact, List[CanonicalContact]]:
    """
    Merge contacts with the same resolved_entity_id. Returns (merged, conflicts_for_manual).
    For MANUAL, merged is the first and conflicts_for_manual lists the rest.
    """
    if not contacts:
        raise ValueError("merge_contacts requires at least one contact")
    order = authoritative_order or getattr(settings, "authoritative_sources_order", None) or []

    if strategy == MergeStrategy.KEEP_FIRST:
        return (contacts[0], [])

    if strategy == MergeStrategy.KEEP_NEWEST:
        best = max(contacts, key=_updated_ts)
        return (best, [])

    if strategy == MergeStrategy.AUTHORITATIVE_SOURCE:
        for src in order:
            for c in contacts:
                if (c.source_provider or "").lower() == (src or "").lower():
                    return (c, [])
        return (max(contacts, key=_updated_ts), [])

    # MANUAL: return first as merged, rest as conflicts for manual resolution
    return (contacts[0], list(contacts[1:]))
