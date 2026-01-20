"""Odoo API connector (XML-RPC, username/password)."""
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from xmlrpc import client as xmlrpc_client

from src.config.settings import settings

from .base import BaseAccountingConnector
from .models import ExternalContact, ExternalInvoice, ExternalPayment


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
    except Exception:
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None


def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except Exception:
        return None


class OdooConnector(BaseAccountingConnector):
    provider = "odoo"

    def __init__(
        self,
        url: Optional[str] = None,
        db: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._url = (url or settings.odoo_url).rstrip("/")
        self._db = db or settings.odoo_db
        self._username = username or settings.odoo_username
        self._password = password or settings.odoo_password
        self._uid: Optional[int] = None

    def _proxy(self, path: str) -> xmlrpc_client.ServerProxy:
        return xmlrpc_client.ServerProxy(f"{self._url}{path}", allow_none=True)

    def _ensure_uid(self) -> int:
        if self._uid is not None:
            return self._uid
        common = self._proxy("/xmlrpc/2/common")
        self._uid = common.authenticate(self._db, self._username, self._password, {})
        if not self._uid:
            raise ValueError("Odoo authentication failed")
        return self._uid

    def _call(self, model: str, method: str, args: List, kwargs: Optional[Dict] = None) -> Any:
        import time
        from xmlrpc.client import Fault

        uid = self._ensure_uid()
        obj = self._proxy("/xmlrpc/2/object")
        last: Optional[Exception] = None
        delay = 1.0
        for attempt in range(4):
            self._rate_limit()
            try:
                return obj.execute_kw(self._db, uid, self._password, model, method, args, kwargs or {})
            except (OSError, ConnectionError, TimeoutError) as e:
                last = e
                if attempt < 3:
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise
            except Fault as f:
                if f.faultCode >= 500 and attempt < 3:
                    last = f
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise
        if last:
            raise last
        raise RuntimeError("retry loop ended")

    def _search_read(
        self,
        model: str,
        domain: Optional[List] = None,
        fields: Optional[List[str]] = None,
        limit: int = 10000,
    ) -> List[Dict]:
        dom = domain or []
        f = fields or []
        return self._call(model, "search_read", [dom], {"fields": f, "limit": limit})

    def fetch_contacts(self, modified_after: Optional[datetime] = None) -> List[ExternalContact]:
        domain: List = []
        if modified_after:
            domain.append(("write_date", ">=", modified_after.strftime("%Y-%m-%d %H:%M:%S")))
        rows = self._search_read("res.partner", domain, ["id", "name", "email", "write_date"])
        out: List[ExternalContact] = []
        for r in rows:
            out.append(
                ExternalContact(
                    external_id=str(r.get("id", "")),
                    name=str(r.get("name", "")),
                    provider=self.provider,
                    email=r.get("email"),
                    updated_at=_parse_dt(r.get("write_date")),
                    raw=dict(r),
                )
            )
        return out

    def fetch_invoices(self, modified_after: Optional[datetime] = None) -> List[ExternalInvoice]:
        domain: List = [("move_type", "in", ["out_invoice", "out_refund"])]
        if modified_after:
            domain.append(("write_date", ">=", modified_after.strftime("%Y-%m-%d %H:%M:%S")))
        rows = self._search_read(
            "account.move",
            domain,
            ["id", "name", "amount_total", "currency_id", "invoice_date", "state", "partner_id", "invoice_date_due", "write_date"],
        )
        out: List[ExternalInvoice] = []
        for r in rows:
            dt = _parse_date(r.get("invoice_date"))
            if not dt:
                continue
            partner = r.get("partner_id")
            pid = str(partner[0]) if isinstance(partner, (list, tuple)) and partner else None
            # currency_id can be [id, 'USD']
            curr = "USD"
            if isinstance(r.get("currency_id"), (list, tuple)) and len(r["currency_id"]) > 1:
                curr = str(r["currency_id"][1])
            out.append(
                ExternalInvoice(
                    external_id=str(r.get("id", "")),
                    number=str(r.get("name", "")),
                    amount=float(r.get("amount_total", 0)),
                    currency=curr,
                    issue_date=dt,
                    status=str(r.get("state", "draft")),
                    provider=self.provider,
                    contact_external_id=pid,
                    due_date=_parse_date(r.get("invoice_date_due")) if r.get("invoice_date_due") else None,
                    updated_at=_parse_dt(r.get("write_date")),
                    raw=dict(r),
                )
            )
        return out

    def fetch_payments(self, modified_after: Optional[datetime] = None) -> List[ExternalPayment]:
        domain: List = []
        if modified_after:
            domain.append(("write_date", ">=", modified_after.strftime("%Y-%m-%d %H:%M:%S")))
        try:
            rows = self._search_read(
                "account.payment",
                domain,
                ["id", "amount", "currency_id", "date", "reconciled_invoice_ids", "ref", "write_date"],
            )
        except Exception:
            rows = []
        out: List[ExternalPayment] = []
        for r in rows:
            dt = _parse_date(r.get("date"))
            if not dt:
                continue
            inv = r.get("reconciled_invoice_ids") or []
            inv_id = str(inv[0]) if inv else None
            curr = "USD"
            if isinstance(r.get("currency_id"), (list, tuple)) and len(r.get("currency_id", [])) > 1:
                curr = str(r["currency_id"][1])
            out.append(
                ExternalPayment(
                    external_id=str(r.get("id", "")),
                    amount=float(r.get("amount", 0)),
                    currency=curr,
                    date=dt,
                    provider=self.provider,
                    invoice_external_id=inv_id,
                    reference=r.get("ref"),
                    updated_at=_parse_dt(r.get("write_date")),
                    raw=dict(r),
                )
            )
        return out
