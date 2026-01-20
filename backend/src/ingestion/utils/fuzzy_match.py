"""Fuzzy matching for names and addresses."""
from typing import Optional, Sequence


def levenshtein(a: str, b: str) -> int:
    if not a:
        return len(b)
    if not b:
        return len(a)
    a, b = a.lower(), b.lower()
    n, m = len(a), len(b)
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        curr = [i]
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            curr.append(min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[m]


def similarity(a: str, b: str) -> float:
    """Returns 1.0 for identical, 0.0 for no match. Uses Levenshtein."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    d = levenshtein(a, b)
    return 1.0 - (d / max(len(a), len(b)))


def best_match(
    value: str,
    candidates: Sequence[str],
    threshold: float = 0.8,
) -> Optional[tuple[str, float]]:
    """Returns (best_candidate, score) or None if no candidate meets threshold."""
    if not value or not candidates:
        return None
    best: Optional[tuple[str, float]] = None
    for c in candidates:
        s = similarity(value, c)
        if s >= threshold and (best is None or s > best[1]):
            best = (c, s)
    return best
