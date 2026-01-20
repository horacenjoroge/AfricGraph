"""Phone number normalization (E.164-like)."""
import re
from typing import Optional

# Common African country codes: Kenya 254, Uganda 256, Tanzania 255, Ghana 233, Nigeria 234, etc.
_DEFAULT_CC = "254"
_PREFIX = {"0": _DEFAULT_CC, "254": "254", "256": "256", "255": "255", "233": "233", "234": "234"}


def normalize_phone(s: Optional[str], default_country_code: str = "254") -> Optional[str]:
    """
    Normalize to digits with country code. Strips spaces, dashes, parens.
    If number starts with 0, replaces with default_country_code.
    Returns None for empty or non-phone-like strings (e.g. too short).
    """
    if not s or not isinstance(s, str):
        return None
    d = re.sub(r"[\s\-\(\)\.]", "", s)
    d = re.sub(r"^\+", "", d)
    if not d.isdigit():
        return None
    if len(d) < 9:
        return None
    if d.startswith("0") and len(d) >= 9:
        d = default_country_code + d[1:]
    if len(d) == 9 and d[0] in "67":
        d = default_country_code + d
    if len(d) < 10:
        return None
    return d
