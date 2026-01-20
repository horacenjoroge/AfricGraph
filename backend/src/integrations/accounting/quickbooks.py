"""QuickBooks API connector (OAuth2)."""
import base64
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import httpx

from src.config.settings import settings

from .base import OAuth2AccountingConnector
from .models import ExternalContact, ExternalInvoice, ExternalPayment
from .token_store import TokenStore

QB_TOKEN = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
QB_SANDBOX = "https://sandbox-quickbooks.api.intuit.com"
QB_PROD = "https://quickbooks.api.intuit.com"


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


class QuickBooksConnector(OAuth2AccountingConnector):
    provider = "quickbooks"

    def __init__(
        self,
        token_store: TokenStore,
        tenant_id: str,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        env: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(token_store=token_store, tenant_id=tenant_id, **kwargs)
        self._client_id = client_id or settings.quickbooks_client_id
        self._client_secret = client_secret or settings.quickbooks_client_secret
        self._base = QB_SANDBOX if (env or settings.quickbooks_environment) == "sandbox" else QB_PROD

    @property
    def token_url(self) -> str:
        return QB_TOKEN

    def _refresh_token_request(self, refresh_token: str) -> Dict[str, Any]:
        basic = base64.b64encode(f"{self._client_id}:{self._client_secret}".encode()).decode()
        with httpx.Client() as c:
            r = c.post(
                QB_TOKEN,
                data={"grant_type": "refresh_token", "refresh_token": refresh_token},
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {basic}",
                },
            )
            r.raise_for_status()
            return r.json()

    def _query_entity(self, entity: str, where: Optional[str] = None) -> List[Dict[str, Any]]:
        q = f"select * from {entity}"
        if where:
            q += f" where {where}"
        url = f"{self._base}/v3/company/{self._tenant_id}/query"
        r = self._oauth_request("GET", url, params={"query": q})
        r.raise_for_status()
        data = r.json()
        resp = data.get("QueryResponse") or {}
        return resp.get(entity, resp.get(entity.lower(), []))

    def fetch_contacts(self, modified_after: Optional[datetime] = None) -> List[ExternalContact]:
        where = None
        if modified_after:
            where = f"MetaData.LastUpdatedTime >= '{modified_after.strftime('%Y-%m-%dT%H:%M:%S')}'"
        rows = self._query_entity("Customer", where)
        out: List[ExternalContact] = []
        for c in rows:
            out.append(
                ExternalContact(
                    external_id=str(c.get("Id", "")),
                    name=str(c.get("DisplayName", c.get("FullyQualifiedName", ""))),
                    provider=self.provider,
                    email=c.get("PrimaryEmailAddr", {}).get("Address") if isinstance(c.get("PrimaryEmailAddr"), dict) else None,
                    updated_at=_parse_dt(c.get("MetaData", {}).get("LastUpdatedTime") if isinstance(c.get("MetaData"), dict) else None),
                    raw=dict(c),
                )
            )
        return out

    def fetch_invoices(self, modified_after: Optional[datetime] = None) -> List[ExternalInvoice]:
        where = None
        if modified_after:
            where = f"MetaData.LastUpdatedTime >= '{modified_after.strftime('%Y-%m-%dT%H:%M:%S')}'"
        rows = self._query_entity("Invoice", where)
        out: List[ExternalInvoice] = []
        for i in rows:
            amt = float(i.get("Total", i.get("Balance", 0)))
            dt = _parse_date(i.get("TxnDate"))
            if not dt:
                continue
            cust = i.get("CustomerRef") or {}
            out.append(
                ExternalInvoice(
                    external_id=str(i.get("Id", "")),
                    number=str(i.get("DocNumber", i.get("Id", ""))),
                    amount=amt,
                    currency=str(i.get("CurrencyRef", {}).get("value", "USD") if isinstance(i.get("CurrencyRef"), dict) else "USD"),
                    issue_date=dt,
                    status=str(i.get("Balance", 0) == 0 and "PAID" or "AUTHORISED"),
                    provider=self.provider,
                    contact_external_id=str(cust.get("value", "")) if cust else None,
                    due_date=_parse_date(i.get("DueDate")),
                    updated_at=_parse_dt(i.get("MetaData", {}).get("LastUpdatedTime") if isinstance(i.get("MetaData"), dict) else None),
                    raw=dict(i),
                )
            )
        return out

    def fetch_payments(self, modified_after: Optional[datetime] = None) -> List[ExternalPayment]:
        where = None
        if modified_after:
            where = f"MetaData.LastUpdatedTime >= '{modified_after.strftime('%Y-%m-%dT%H:%M:%S')}'"
        rows = self._query_entity("Payment", where)
        out: List[ExternalPayment] = []
        for p in rows:
            amt = float(p.get("TotalAmt", 0))
            dt = _parse_date(p.get("TxnDate"))
            if not dt:
                continue
            inv = p.get("Line", [{}])[0].get("LinkedTxn") if isinstance(p.get("Line"), list) and p.get("Line") else None
            inv_id = None
            if isinstance(inv, list) and inv:
                inv_id = inv[0].get("TxnId") if isinstance(inv[0], dict) else None
            elif isinstance(inv, dict):
                inv_id = inv.get("TxnId")
            curr = "USD"
            if isinstance(p.get("CurrencyRef"), dict):
                curr = p["CurrencyRef"].get("value", "USD")
            out.append(
                ExternalPayment(
                    external_id=str(p.get("Id", "")),
                    amount=amt,
                    currency=str(curr),
                    date=dt,
                    provider=self.provider,
                    invoice_external_id=str(inv_id) if inv_id else None,
                    reference=p.get("PaymentRefNum") or p.get("PrivateNote"),
                    updated_at=_parse_dt(p.get("MetaData", {}).get("LastUpdatedTime") if isinstance(p.get("MetaData"), dict) else None),
                    raw=dict(p),
                )
            )
        return out
