"""Entity resolution: same entity across sources via fuzzy matching on names/phones."""
from typing import Dict, List, Optional, Sequence

from ..normalizers.canonical import CanonicalContact
from ..utils.fuzzy_match import similarity


def _get_name(c: CanonicalContact) -> str:
    return (c.name or "").strip().lower()


def _get_phone(c: CanonicalContact) -> Optional[str]:
    return c.phone


def resolve_entities(
    contacts: Sequence[CanonicalContact],
    name_threshold: float = 0.85,
    phone_match_override: bool = True,
) -> List[CanonicalContact]:
    """
    Sets resolved_entity_id on each contact. Contacts in the same cluster get the same id.
    Uses fuzzy name similarity; exact phone match forces same cluster.
    """
    if not contacts:
        return []

    # Copy to avoid mutating inputs; we'll assign resolved_entity_id.
    out: List[CanonicalContact] = []
    for c in contacts:
        out.append(
            CanonicalContact(
                source_id=c.source_id,
                source_provider=c.source_provider,
                name=c.name,
                email=c.email,
                phone=c.phone,
                phone_raw=c.phone_raw,
                address=c.address,
                address_raw=c.address_raw,
                resolved_entity_id=None,
                updated_at=c.updated_at,
                raw=dict(c.raw) if getattr(c, "raw", None) else {},
            )
        )

    # Union-find: parent[i] = parent index or -1.
    n = len(out)
    parent: List[int] = [-1] * n

    def find(i: int) -> int:
        if parent[i] < 0:
            return i
        parent[i] = find(parent[i])
        return parent[i]

    def union(i: int, j: int) -> None:
        pi, pj = find(i), find(j)
        if pi == pj:
            return
        if parent[pi] <= parent[pj]:
            parent[pi] += parent[pj]
            parent[pj] = pi
        else:
            parent[pj] += parent[pi]
            parent[pi] = pj

    for i in range(n):
        for j in range(i + 1, n):
            a, b = out[i], out[j]
            same = False
            pa, pb = _get_phone(a), _get_phone(b)
            if pa and pb and pa == pb and phone_match_override:
                same = True
            if not same:
                s = similarity(_get_name(a), _get_name(b))
                if s >= name_threshold:
                    same = True
            if same:
                union(i, j)

    # Assign cluster id
    roots: Dict[int, str] = {}
    next_id = 0
    for i in range(n):
        r = find(i)
        if r not in roots:
            roots[r] = f"resolved:{next_id}"
            next_id += 1
        out[i].resolved_entity_id = roots[r]
    return out
