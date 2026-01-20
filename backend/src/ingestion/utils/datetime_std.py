"""Date/time standardization to date and UTC datetime."""
from datetime import date, datetime, timezone
from typing import Optional

from dateutil.parser import parse as dateutil_parse


def to_date(s: Optional[str]) -> Optional[date]:
    if not s or not str(s).strip():
        return None
    try:
        dt = dateutil_parse(str(s).strip(), dayfirst=True)
        return dt.date() if hasattr(dt, "date") else date(dt.year, dt.month, dt.day)
    except Exception:
        return None


def to_datetime_utc(s: Optional[str]) -> Optional[datetime]:
    if not s or not str(s).strip():
        return None
    try:
        dt = dateutil_parse(str(s).strip(), dayfirst=True)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None
