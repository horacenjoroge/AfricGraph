"""Transaction classifier: payment_in, payment_out, merchant, withdrawal from description and amount direction."""
import re
from typing import Optional

from .models import RawRow, TransactionType


# Patterns (case-insensitive). Order matters: more specific first.
_WITHDRAWAL = re.compile(
    r"\b(atm|agent|withdraw|withdrawal|cash\s*out|send\s*to\s*agent|til\s*withdraw)\b",
    re.I,
)
_MERCHANT = re.compile(
    r"\b(pay\s*bill|buy\s*goods|lipa|merchant|pos|till|pay\s*merchant|goods\s*&\s*services)\b",
    re.I,
)
_PAYMENT_OUT = re.compile(
    r"\b(sent|send\s*money|sent\s*to|transfer\s*to|paid\s*to|withdrawn)\b",
    re.I,
)
_PAYMENT_IN = re.compile(
    r"\b(received|from|deposit|paid\s*in|credit|moved\s*from\s*bank|gifts)\b",
    re.I,
)


def classify(row: RawRow, is_in: bool) -> TransactionType:
    """Classify from details and whether amount is in (True) or out (False)."""
    text = (row.details or "") + " " + (row.status or "")
    if not text.strip():
        return TransactionType.PAYMENT_IN if is_in else TransactionType.PAYMENT_OUT

    if _WITHDRAWAL.search(text):
        return TransactionType.WITHDRAWAL
    if _MERCHANT.search(text):
        return TransactionType.MERCHANT
    if is_in and _PAYMENT_IN.search(text):
        return TransactionType.PAYMENT_IN
    if not is_in and _PAYMENT_OUT.search(text):
        return TransactionType.PAYMENT_OUT

    return TransactionType.PAYMENT_IN if is_in else TransactionType.PAYMENT_OUT
