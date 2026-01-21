"""Entity deduplication: detection, candidates, merge, unmerge, merge history."""
from .candidates import find_candidates
from .detection import address_similarity, composite_similarity, name_similarity, phone_match
from .merge import merge_nodes, unmerge
from .merge_history import ensure_merge_history_table, get_merge_history, get_merge_record, insert_merge_record, mark_undone

__all__ = [
    "name_similarity",
    "phone_match",
    "address_similarity",
    "composite_similarity",
    "find_candidates",
    "merge_nodes",
    "unmerge",
    "ensure_merge_history_table",
    "get_merge_history",
    "get_merge_record",
    "insert_merge_record",
    "mark_undone",
]
