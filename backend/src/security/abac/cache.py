"""Simple in-memory permission cache with TTL."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class PermissionCache:
    """TTL cache for permission decisions."""

    def __init__(self, ttl_seconds: int = 300, max_entries: int = 5000) -> None:
        self.ttl = ttl_seconds
        self.max_entries = max_entries
        self._store: dict[str, CacheEntry] = {}

    def _now(self) -> float:
        return time.time()

    def _purge(self) -> None:
        now = self._now()
        stale_keys = [k for k, v in self._store.items() if v.expires_at <= now]
        for k in stale_keys:
            self._store.pop(k, None)
        # If too large, drop oldest-ish entries (not LRU but bounded)
        if len(self._store) > self.max_entries:
            for k in list(self._store.keys())[: len(self._store) - self.max_entries]:
                self._store.pop(k, None)

    def get(self, key: str) -> Optional[Any]:
        self._purge()
        entry = self._store.get(key)
        if not entry or entry.expires_at <= self._now():
            return None
        return entry.value

    def set(self, key: str, value: Any) -> None:
        self._purge()
        self._store[key] = CacheEntry(value=value, expires_at=self._now() + self.ttl)

    def invalidate(self, key_prefix: Optional[str] = None) -> None:
        if key_prefix is None:
            self._store.clear()
            return
        for k in list(self._store.keys()):
            if k.startswith(key_prefix):
                self._store.pop(k, None)

    def invalidate_subject(self, subject_id: str) -> None:
        """Drop all cached decisions for a subject (used when role/attrs change)."""
        self.invalidate(f"sub:{subject_id}:")

