"""Address parsing and geocoding stub."""
import re
from typing import Any, Dict, Optional, Tuple


def parse_address(text: Optional[str]) -> Dict[str, Optional[str]]:
    """
    Simple heuristic parsing into street, city, region, country, postal.
    Splits on comma or newline; last non-empty segment often country; digits-only can be postal.
    """
    out: Dict[str, Optional[str]] = {"street": None, "city": None, "region": None, "country": None, "postal": None}
    if not text or not str(text).strip():
        return out
    parts = [p.strip() for p in re.split(r"[\n,;]", str(text)) if p.strip()]
    if not parts:
        return out
    for i, p in enumerate(parts):
        if p.isdigit() and len(p) <= 10:
            out["postal"] = p
        elif i == len(parts) - 1 and len(p) >= 2 and p.upper() == p:
            out["country"] = p
        elif i == 0:
            out["street"] = p
        elif i == 1:
            out["city"] = p
        elif i == 2 and out["region"] is None:
            out["region"] = p
    if out["street"] is None and parts:
        out["street"] = parts[0]
    return out


def geocode(
    street: Optional[str] = None,
    city: Optional[str] = None,
    country: Optional[str] = None,
) -> Optional[Tuple[float, float]]:
    """
    Stub. Returns (lat, lon) or None. Replace with Google/Nominatim/etc. in production.
    """
    return None
