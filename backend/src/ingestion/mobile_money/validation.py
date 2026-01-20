"""Data quality validation for normalized transactions."""
from datetime import date
from typing import List, Optional

from dateutil.parser import parse as dateutil_parse

from .models import NormalizedTransaction, TransactionType


def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s or not str(s).strip():
        return None
    try:
        dt = dateutil_parse(str(s).strip(), dayfirst=True)
        return dt.date() if hasattr(dt, "date") else date(dt.year, dt.month, dt.day)
    except Exception:
        return None


def parse_completion_time(s: Optional[str]) -> Optional[date]:
    """Parse completion_time string (multiple formats) to date."""
    return _parse_date(s)


def validate(t: NormalizedTransaction) -> List[str]:
    """Returns list of validation error messages. Empty if valid."""
    errs: List[str] = []
    if t.amount <= 0:
        errs.append("amount must be positive")
    if t.type not in (TransactionType.PAYMENT_IN, TransactionType.PAYMENT_OUT, TransactionType.MERCHANT, TransactionType.WITHDRAWAL):
        errs.append("invalid type")
    if not t.currency or len(t.currency) != 3 or not t.currency.isalpha():
        errs.append("currency must be 3-letter code")
    return errs
