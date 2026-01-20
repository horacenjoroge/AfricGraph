"""Counterparty extraction from transaction descriptions."""
import re
from typing import Optional


# "from X", "to X", "sent to X", "received from X", "pay bill X Y", "buy goods X Y"
_FROM = re.compile(r"\b(?:received\s+)?from\s+([A-Za-z0-9\s\.\-]+?)(?:\s+on|\s*$|,|\d{4})", re.I)
_TO = re.compile(r"\b(?:sent\s+)?to\s+([A-Za-z0-9\s\.\-]+?)(?:\s+on|\s*$|,|\d{4})", re.I)
_PAYBILL = re.compile(r"\bpay\s*bill\s+(\d+)\s+([A-Za-z0-9\s\.\-]*)", re.I)
_BUY_GOODS = re.compile(r"\b(?:buy\s*goods|lipa)\s*(\d+)\s*([A-Za-z0-9\s\.\-]*)", re.I)
_PHONE = re.compile(r"\b(254\d{9}|07\d{8}|01\d{8}|256\d{9}|0\d{8,9})\b")


def extract_counterparty(description: Optional[str]) -> Optional[str]:
    """Extract counterparty from description. Returns name, paybill+account, till, or phone."""
    if not description or not str(description).strip():
        return None
    text = str(description).strip()

    for pat in [_FROM, _TO, _PAYBILL, _BUY_GOODS]:
        m = pat.search(text)
        if m:
            parts = [str(m.group(i)).strip() for i in range(1, (m.lastindex or 0) + 1) if m.group(i)]
            part = " ".join(parts)
            if part and len(part) > 1:
                return part.strip()[:200]

    pm = _PHONE.search(text)
    if pm:
        return pm.group(1)
    return None
