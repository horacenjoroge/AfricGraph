"""Amount normalization: parse strings, handle commas and decimals, determine in/out."""
import re
from typing import Optional, Tuple


def _parse_number(s: Optional[str]) -> Optional[float]:
    if s is None or not str(s).strip():
        return None
    t = str(s).strip().replace(",", "")
    # Remove currency symbols and extra spaces
    t = re.sub(r"[\s\xa0]", "", t)
    t = re.sub(r"^[A-Z]{3}\s*", "", t, flags=re.I)
    t = re.sub(r"^[KUG]?\s*", "", t, flags=re.I)
    if not t or t in ("-", "."):
        return None
    try:
        return float(t)
    except ValueError:
        return None


def normalize_amount(paid_in: Optional[str], withdrawn: Optional[str]) -> Tuple[float, bool]:
    """
    Returns (amount, is_in). amount is positive; is_in True for money in, False for out.
    If both present, prefer paid_in. If neither, return (0.0, True).
    """
    pin = _parse_number(paid_in)
    w = _parse_number(withdrawn)
    if pin is not None and pin > 0:
        return (pin, True)
    if w is not None and w > 0:
        return (w, False)
    if pin is not None and pin != 0:
        return (abs(pin), pin > 0)
    if w is not None and w != 0:
        return (abs(w), w < 0)
    return (0.0, True)
