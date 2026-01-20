"""OAuth token storage. In-memory implementation; replace with Redis/DB for production."""
from typing import Any, Dict, Optional, Protocol


class TokenStore(Protocol):
    def get(self, provider: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]: ...
    def set(self, provider: str, tokens: Dict[str, Any], tenant_id: Optional[str] = None) -> None: ...


class InMemoryTokenStore:
    def __init__(self) -> None:
        self._data: Dict[str, Dict[str, Any]] = {}

    def _key(self, provider: str, tenant_id: Optional[str]) -> str:
        return f"{provider}:{tenant_id or 'default'}"

    def get(self, provider: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        return self._data.get(self._key(provider, tenant_id))

    def set(self, provider: str, tokens: Dict[str, Any], tenant_id: Optional[str] = None) -> None:
        self._data[self._key(provider, tenant_id)] = dict(tokens)


_default_token_store: Optional[InMemoryTokenStore] = None


def get_default_token_store() -> InMemoryTokenStore:
    global _default_token_store
    if _default_token_store is None:
        _default_token_store = InMemoryTokenStore()
    return _default_token_store
