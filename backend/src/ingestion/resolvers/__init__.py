"""Entity resolution and merge strategies."""
from .entity_resolver import resolve_entities
from .merge import MergeStrategy, merge_contacts

__all__ = ["resolve_entities", "MergeStrategy", "merge_contacts"]
