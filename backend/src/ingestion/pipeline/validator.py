"""Data validation for canonical models before graph write."""
from datetime import date, datetime
from typing import Any, List, Optional

from src.ingestion.normalizers.canonical import (
    CanonicalContact,
    CanonicalInvoice,
    CanonicalPayment,
    CanonicalTransaction,
)


def _err(f: str, msg: str) -> str:
    return f"{f}: {msg}"


def validate_canonical_transaction(t: CanonicalTransaction) -> List[str]:
    errs: List[str] = []
    if not (getattr(t, "source_id", None) or "").strip():
        errs.append(_err("source_id", "required"))
    if not hasattr(t, "date") or t.date is None:
        errs.append(_err("date", "required"))
    if not hasattr(t, "amount") or (t.amount is not None and float(t.amount) <= 0):
        errs.append(_err("amount", "must be positive"))
    if not (getattr(t, "currency", None) or "").strip():
        errs.append(_err("currency", "required"))
    if not (getattr(t, "type", None) or "").strip():
        errs.append(_err("type", "required"))
    return errs


def validate_canonical_contact(c: CanonicalContact) -> List[str]:
    errs: List[str] = []
    if not (getattr(c, "source_id", None) or "").strip():
        errs.append(_err("source_id", "required"))
    if not (getattr(c, "name", None) or "").strip():
        errs.append(_err("name", "required"))
    return errs


def validate_canonical_invoice(i: CanonicalInvoice) -> List[str]:
    errs: List[str] = []
    if not (getattr(i, "source_id", None) or "").strip():
        errs.append(_err("source_id", "required"))
    if not (getattr(i, "number", None) or "").strip():
        errs.append(_err("number", "required"))
    if not hasattr(i, "amount") or (i.amount is not None and float(i.amount) < 0):
        errs.append(_err("amount", "must be >= 0"))
    if not hasattr(i, "issue_date") or i.issue_date is None:
        errs.append(_err("issue_date", "required"))
    if not (getattr(i, "status", None) or "").strip():
        errs.append(_err("status", "required"))
    return errs


def validate_canonical_payment(p: CanonicalPayment) -> List[str]:
    errs: List[str] = []
    if not (getattr(p, "source_id", None) or "").strip():
        errs.append(_err("source_id", "required"))
    if not hasattr(p, "date") or p.date is None:
        errs.append(_err("date", "required"))
    if not hasattr(p, "amount") or (p.amount is not None and float(p.amount) <= 0):
        errs.append(_err("amount", "must be positive"))
    if not (getattr(p, "currency", None) or "").strip():
        errs.append(_err("currency", "required"))
    return errs
