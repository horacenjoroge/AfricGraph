"""Xero API connector (OAuth2)."""
from datetime import date, datetime
from typing import Any, Dict, List, Optional
import httpx

from src.config.settings import settings

from .base import OAuth2AccountingConnector
from .models import ExternalContact, ExternalInvoice, ExternalPayment
from .token_store import TokenStore

XERO_API = "https://api.xero.com/api.xro/2.0"
XERO_TOKEN = "https://identity.xero.com/connect/token"


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except Exception:
        return None


class XeroConnector(OAuth2AccountingConnector):
    provider = "xero"

    def __init__(
        self,
        token_store: TokenStore,
        tenant_id: str,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(token_store=token_store, tenant_id=tenant_id, **kwargs)
        self._client_id = client_id or settings.xero_client_id
        self._client_secret = client_secret or settings.xero_client_secret

    @property
    def token_url(self) -> str:
        return XERO_TOKEN

    def _refresh_token_request(self, refresh_token: str) -> Dict[str, Any]:
        with httpx.Client() as c:
            r = c.post(
                XERO_TOKEN,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            r.raise_for_status()
            return r.json()

    def _headers(self) -> Dict[str, str]:
        return {"xero-tenant-id": self._tenant_id or ""}

    def fetch_contacts(self, modified_after: Optional[datetime] = None) -> List[ExternalContact]:
        url = f"{XERO_API}/Contacts"
        params: Dict[str, str] = {}
        headers = self._headers()
        if modified_after:
            headers["If-Modified-Since"] = modified_after.strftime("%a, %d %b %Y %H:%M:%S GMT")
        r = self._oauth_request("GET", url, headers=headers, params=params or None)
        r.raise_for_status()
        data = r.json()
        out: List[ExternalContact] = []
        for c in data.get("Contacts") or []:
            out.append(
                ExternalContact(
                    external_id=str(c.get("ContactID", "")),
                    name=str(c.get("Name", "")),
                    provider=self.provider,
                    email=c.get("EmailAddress"),
                    updated_at=_parse_dt(c.get("UpdatedDateUTC")),
                    raw=dict(c),
                )
            )
        return out

    def fetch_invoices(self, modified_after: Optional[datetime] = None) -> List[ExternalInvoice]:
        url = f"{XERO_API}/Invoices"
        params: Dict[str, str] = {}
        if modified_after:
            params["where"] = f"UpdatedDateUtc>=DateTime({modified_after.year},{modified_after.month},{modified_after.day})"
        r = self._oauth_request("GET", url, headers=self._headers(), params=params or None)
        r.raise_for_status()
        data = r.json()
        out: List[ExternalInvoice] = []
        for i in data.get("Invoices") or []:
            amt = float(i.get("Total") or i.get("AmountDue") or i.get("SubTotal") or 0)
            dt = _parse_date(i.get("Date"))
            if not dt:
                continue
            out.append(
                ExternalInvoice(
                    external_id=str(i.get("InvoiceID", "")),
                    number=str(i.get("InvoiceNumber", "")),
                    amount=amt,
                    currency=str(i.get("CurrencyCode", "USD")),
                    issue_date=dt,
                    status=str(i.get("Status", "")),
                    provider=self.provider,
                    contact_external_id=str(i.get("Contact", {}).get("ContactID", "")) if i.get("Contact") else None,
                    due_date=_parse_date(i.get("DueDate")),
                    updated_at=_parse_dt(i.get("UpdatedDateUTC")),
                    raw=dict(i),
                )
            )
        return out

    def fetch_payments(self, modified_after: Optional[datetime] = None) -> List[ExternalPayment]:
        url = f"{XERO_API}/Payments"
        params: Dict[str, str] = {}
        if modified_after:
            params["where"] = f"UpdatedDateUtc>=DateTime({modified_after.year},{modified_after.month},{modified_after.day})"
        r = self._oauth_request("GET", url, headers=self._headers(), params=params or None)
        r.raise_for_status()
        data = r.json()
        out: List[ExternalPayment] = []
        for p in data.get("Payments") or []:
            amt = float(p.get("Amount", 0))
            dt = _parse_date(p.get("Date"))
            if not dt:
                continue
            inv = p.get("Invoice") or {}
            cc = p.get("CurrencyCode") or inv.get("CurrencyCode") or "USD"
            out.append(
                ExternalPayment(
                    external_id=str(p.get("PaymentID", "")),
                    amount=amt,
                    currency=str(cc),
                    date=dt,
                    provider=self.provider,
                    invoice_external_id=str(inv.get("InvoiceID", "")) if inv else None,
                    reference=p.get("Reference"),
                    updated_at=_parse_dt(p.get("UpdatedDateUTC")),
                    raw=dict(p),
                )
            )
        return out
