"""Base accounting connector: retry, rate limiting, HTTP, OAuth2 refresh."""
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import httpx

from src.config.settings import settings
from src.infrastructure.logging import get_logger

from .models import ExternalContact, ExternalInvoice, ExternalPayment
from .token_store import TokenStore

logger = get_logger(__name__)

TOKEN_EXPIRY_BUFFER = 60


def _retry_request(
    fn,
    retries: int = None,
    backoff: float = 1.0,
) -> httpx.Response:
    mx = retries or getattr(settings, "accounting_retry_max", 3)
    delay = backoff
    last: Optional[Exception] = None
    for i in range(mx + 1):
        try:
            r = fn()
            if r.status_code == 429:
                ra = r.headers.get("Retry-After")
                wait = int(ra) if ra and ra.isdigit() else delay
                logger.warning("rate limited, retry after", seconds=wait)
                time.sleep(wait)
                last = httpx.HTTPStatusError("429 Rate limited", request=r.request, response=r)
                continue
            if 500 <= r.status_code < 600 and i < mx:
                logger.warning("server error, retrying", status=r.status_code, attempt=i + 1)
                time.sleep(delay)
                delay *= 2
                last = httpx.HTTPStatusError(f"{r.status_code}", request=r.request, response=r)
                continue
            return r
        except (httpx.ConnectError, httpx.ReadTimeout) as e:
            last = e
            if i < mx:
                logger.warning("request failed, retrying", error=str(e), attempt=i + 1)
                time.sleep(delay)
                delay *= 2
            else:
                raise
    if last:
        raise last
    raise RuntimeError("retry loop ended without result")


class BaseAccountingConnector(ABC):
    """Base with HTTP, retry, rate limiting. Subclasses implement OAuth and entity fetch."""

    provider: str = ""

    def __init__(
        self,
        request_timeout: int = None,
        rate_limit_delay: float = None,
    ):
        self._timeout = request_timeout or getattr(settings, "accounting_request_timeout", 30)
        self._rate_delay = rate_limit_delay or getattr(settings, "accounting_rate_limit_delay", 1.0)
        self._last_request_at: float = 0

    def _rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self._rate_delay:
            time.sleep(self._rate_delay - elapsed)
        self._last_request_at = time.monotonic()

    def _request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Any = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        self._rate_limit()
        req_headers = dict(headers or {})

        def do() -> httpx.Response:
            with httpx.Client(timeout=self._timeout) as c:
                return c.request(method, url, headers=req_headers, json=json, params=params)

        return _retry_request(do)

    @abstractmethod
    def fetch_contacts(self, modified_after: Optional[datetime] = None) -> List[ExternalContact]:
        pass

    @abstractmethod
    def fetch_invoices(self, modified_after: Optional[datetime] = None) -> List[ExternalInvoice]:
        pass

    @abstractmethod
    def fetch_payments(self, modified_after: Optional[datetime] = None) -> List[ExternalPayment]:
        pass


class OAuth2AccountingConnector(BaseAccountingConnector):
    """Adds OAuth2 token refresh. Subclass must set token_url and implement _refresh_token_request."""

    def __init__(
        self,
        token_store: TokenStore,
        tenant_id: Optional[str] = None,
        request_timeout: int = None,
        rate_limit_delay: float = None,
    ):
        super().__init__(request_timeout=request_timeout, rate_limit_delay=rate_limit_delay)
        self._store = token_store
        self._tenant_id = tenant_id

    @property
    @abstractmethod
    def token_url(self) -> str: ...

    @abstractmethod
    def _refresh_token_request(self, refresh_token: str) -> Dict[str, Any]: ...

    def _ensure_token(self) -> str:
        data = self._store.get(self.provider, self._tenant_id)
        if not data:
            raise ValueError(f"no token for {self.provider}. complete OAuth flow first.")
        now = datetime.now(timezone.utc).timestamp()
        exp = data.get("expires_at") or 0
        exp_ts = exp if isinstance(exp, (int, float)) else (getattr(exp, "timestamp", lambda: 0)() or 0)
        if exp_ts <= now + TOKEN_EXPIRY_BUFFER:
            ref = data.get("refresh_token")
            if not ref:
                raise ValueError("refresh_token missing; re-authenticate")
            out = self._refresh_token_request(ref)
            access = out.get("access_token")
            if not access:
                raise ValueError("refresh response missing access_token")
            new = {
                "access_token": access,
                "refresh_token": out.get("refresh_token") or ref,
                "expires_in": int(out.get("expires_in", 1800)),
            }
            new["expires_at"] = (now + timedelta(seconds=new["expires_in"])).timestamp()
            self._store.set(self.provider, new, self._tenant_id)
            return access
        return data["access_token"]

    def _oauth_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Any = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        tok = self._ensure_token()
        h = dict(headers or {})
        h["Authorization"] = f"Bearer {tok}"
        return self._request(method, url, headers=h, json=json, params=params)
