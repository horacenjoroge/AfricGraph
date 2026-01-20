"""Duplicate detection via content hash."""
import hashlib
from datetime import date
from typing import Optional, Set


def content_hash(
    provider: str,
    provider_txn_id: Optional[str],
    txn_date: date,
    amount: float,
    description: str,
) -> str:
    """Stable hash for deduplication. Include provider, id or date+amount+description."""
    parts = [provider, provider_txn_id or "", str(txn_date), f"{amount:.2f}", (description or "").strip()]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def filter_duplicates(
    hashes: list[str], seen: Optional[Set[str]] = None
) -> tuple[list[str], set[str]]:
    """
    Returns (unique_hashes, combined_seen). unique_hashes are those not in seen.
    combined_seen = seen | set(unique_hashes).
    """
    s = set(seen) if seen is not None else set()
    out = [h for h in hashes if h not in s]
    s = s | set(out)
    return (out, s)
