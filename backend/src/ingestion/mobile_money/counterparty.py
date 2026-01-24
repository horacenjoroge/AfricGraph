"""Counterparty extraction from transaction descriptions."""
import re
from typing import Optional, Tuple


# Patterns for extracting counterparty with direction
_FUNDS_RECEIVED_FROM = re.compile(r"funds\s+received\s+from\s+(\d{10,12})\s*[-–]\s*([A-Za-z\s\.\-]+?)(?:\s+completed|\s+unknown|\s*$)", re.I)
_FUNDS_SENT_TO = re.compile(r"funds\s+sent\s+to\s+(\d{10,12})\s*[-–]\s*([A-Za-z\s\.\-]+?)(?:\s+completed|\s+unknown|\s*$)", re.I)
_TO_PATTERN = re.compile(r"\bto\s+(\d{10,12})\s*[-–]\s*([A-Za-z\s\.\-]+?)(?:\s+completed|\s+unknown|\s*$)", re.I)
_FROM_PATTERN = re.compile(r"\bfrom\s+(\d{10,12})\s*[-–]\s*([A-Za-z\s\.\-]+?)(?:\s+completed|\s+unknown|\s*$)", re.I)
_PAYBILL = re.compile(r"\bpay\s*bill\s+(\d+)\s+([A-Za-z0-9\s\.\-]*)", re.I)
_BUY_GOODS = re.compile(r"\b(?:buy\s*goods|lipa)\s*(\d+)\s*([A-Za-z0-9\s\.\-]*)", re.I)
_PHONE = re.compile(r"\b(254\d{9}|07\d{8}|01\d{8}|256\d{9}|0\d{8,9})\b")
# Pattern for "phone - name" format (most common)
_PHONE_NAME = re.compile(r"(\d{10,12})\s*[-–]\s*([A-Za-z\s\.\-]+?)(?:\s+completed|\s+unknown|\s*$)", re.I)

# Legacy patterns for backward compatibility
_FROM = re.compile(r"\b(?:received\s+)?from\s+([A-Za-z0-9\s\.\-]+?)(?:\s+on|\s*$|,|\d{4})", re.I)
_TO = re.compile(r"\b(?:sent\s+)?to\s+([A-Za-z0-9\s\.\-]+?)(?:\s+on|\s*$|,|\d{4})", re.I)


def extract_counterparty(description: Optional[str]) -> Optional[str]:
    """Extract counterparty from description. Returns name, paybill+account, till, or phone."""
    if not description or not str(description).strip():
        return None
    text = str(description).strip()

    # Try specific patterns first (phone-name format)
    for pat in [_FUNDS_RECEIVED_FROM, _FUNDS_SENT_TO, _TO_PATTERN, _FROM_PATTERN]:
        m = pat.search(text)
        if m:
            # For phone-name patterns, return the name
            if len(m.groups()) >= 2 and m.group(2):
                name = m.group(2).strip()
                if name and len(name) > 1:
                    return name[:200]

    # Try legacy patterns
    for pat in [_PAYBILL, _BUY_GOODS, _FROM, _TO]:
        m = pat.search(text)
        if m:
            parts = [str(m.group(i)).strip() for i in range(1, (m.lastindex or 0) + 1) if m.group(i)]
            part = " ".join(parts)
            if part and len(part) > 1:
                return part.strip()[:200]

    # Try phone-name pattern
    pm = _PHONE_NAME.search(text)
    if pm and pm.group(2):
        return pm.group(2).strip()[:200]

    # Fallback to phone only
    pm = _PHONE.search(text)
    if pm:
        return pm.group(1)
    return None


def extract_counterparty_with_phone(description: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract counterparty name, phone, and direction from description.
    Returns (name, phone, direction) where direction is 'from' or 'to' or None.
    """
    if not description or not str(description).strip():
        return None, None, None
    
    text = str(description).strip()
    direction = None
    phone = None
    name = None
    
    # Check for "Funds received from" pattern
    m = _FUNDS_RECEIVED_FROM.search(text)
    if m:
        direction = "from"
        phone = m.group(1)
        name = m.group(2).strip() if m.group(2) else None
        return name, phone, direction
    
    # Check for "Funds sent to" pattern
    m = _FUNDS_SENT_TO.search(text)
    if m:
        direction = "to"
        phone = m.group(1)
        name = m.group(2).strip() if m.group(2) else None
        return name, phone, direction
    
    # Check for generic "to phone - name" pattern
    m = _TO_PATTERN.search(text)
    if m:
        direction = "to"
        phone = m.group(1)
        name = m.group(2).strip() if m.group(2) else None
        return name, phone, direction
    
    # Check for generic "from phone - name" pattern
    m = _FROM_PATTERN.search(text)
    if m:
        direction = "from"
        phone = m.group(1)
        name = m.group(2).strip() if m.group(2) else None
        return name, phone, direction
    
    # Try generic phone-name pattern
    m = _PHONE_NAME.search(text)
    if m:
        phone = m.group(1)
        name = m.group(2).strip() if m.group(2) else None
        # Try to infer direction from text
        if "received" in text.lower() or "from" in text.lower():
            direction = "from"
        elif "sent" in text.lower() or "to" in text.lower():
            direction = "to"
        return name, phone, direction
    
    # Fallback: try to extract phone only
    pm = _PHONE.search(text)
    if pm:
        phone = pm.group(1)
        # Try to infer direction
        if "received" in text.lower() or "from" in text.lower():
            direction = "from"
        elif "sent" in text.lower() or "to" in text.lower():
            direction = "to"
        return None, phone, direction
    
    return None, None, None
