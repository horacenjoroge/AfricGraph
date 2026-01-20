"""Normalizer for accounting (ExternalContact, ExternalInvoice, ExternalPayment -> Canonical*)."""
from typing import List

from src.integrations.accounting.models import ExternalContact, ExternalInvoice, ExternalPayment

from ..utils.phone import normalize_phone
from .base import BaseNormalizer
from .canonical import CanonicalContact, CanonicalInvoice, CanonicalPayment


class AccountingNormalizer(BaseNormalizer):
    def normalize_contact(self, c: ExternalContact) -> CanonicalContact:
        phone = None
        if getattr(c, "raw", {}):
            for k in ("phone", "Phone", "mobile", "Mobile", "Fax"):
                v = c.raw.get(k) if isinstance(c.raw, dict) else None
                if v:
                    phone = normalize_phone(str(v))
                    break
        return CanonicalContact(
            source_id=f"{c.provider}:{c.external_id}",
            source_provider=c.provider,
            name=(c.name or "").strip(),
            email=getattr(c, "email", None),
            phone=phone,
            address=None,
            address_raw=None,
            updated_at=getattr(c, "updated_at", None),
            raw=getattr(c, "raw", {}) or {},
        )

    def normalize_invoice(self, i: ExternalInvoice) -> CanonicalInvoice:
        amt_orig = i.amount
        ccy_orig = (i.currency or "USD").upper()
        amt = self._converter.convert(amt_orig, ccy_orig, self._target_currency)
        return CanonicalInvoice(
            source_id=f"{i.provider}:{i.external_id}",
            source_provider=i.provider,
            number=i.number or "",
            amount=amt,
            currency=self._target_currency,
            amount_original=amt_orig,
            currency_original=ccy_orig,
            issue_date=i.issue_date,
            status=(i.status or "").upper(),
            due_date=i.due_date,
            contact_source_id=f"{i.provider}:{i.contact_external_id}" if i.contact_external_id else None,
            updated_at=getattr(i, "updated_at", None),
            raw=getattr(i, "raw", {}) or {},
        )

    def normalize_payment(self, p: ExternalPayment) -> CanonicalPayment:
        amt_orig = p.amount
        ccy_orig = (p.currency or "USD").upper()
        amt = self._converter.convert(amt_orig, ccy_orig, self._target_currency)
        inv_src = f"{p.provider}:{p.invoice_external_id}" if p.invoice_external_id else None
        return CanonicalPayment(
            source_id=f"{p.provider}:{p.external_id}",
            source_provider=p.provider,
            date=p.date,
            amount=amt,
            currency=self._target_currency,
            amount_original=amt_orig,
            currency_original=ccy_orig,
            invoice_source_id=inv_src,
            reference=p.reference,
            updated_at=getattr(p, "updated_at", None),
            raw=getattr(p, "raw", {}) or {},
        )

    def normalize_contacts(self, items: List[ExternalContact]) -> List[CanonicalContact]:
        return [self.normalize_contact(c) for c in items]

    def normalize_invoices(self, items: List[ExternalInvoice]) -> List[CanonicalInvoice]:
        return [self.normalize_invoice(i) for i in items]

    def normalize_payments(self, items: List[ExternalPayment]) -> List[CanonicalPayment]:
        return [self.normalize_payment(p) for p in items]
