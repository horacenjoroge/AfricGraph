"""JWT token generation and validation."""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt

from src.config.settings import settings

ALG = settings.jwt_algorithm
SECRET = settings.jwt_secret_key
ACCESS_EXP = timedelta(hours=settings.jwt_expiration_hours)
REFRESH_EXP = timedelta(days=settings.jwt_refresh_expiration_days)

SUB = "sub"
TYPE = "type"
ACCESS = "access"
REFRESH = "refresh"
EXP = "exp"
ROLE = "role"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _exp_sec(d: timedelta) -> int:
    return int(d.total_seconds())


def create_access_token(sub: str, role: str) -> tuple[str, int]:
    """Returns (token, expires_in_seconds)."""
    exp = _now() + ACCESS_EXP
    payload = {SUB: sub, TYPE: ACCESS, EXP: exp, ROLE: role}
    token = jwt.encode(payload, SECRET, algorithm=ALG)
    return token, _exp_sec(ACCESS_EXP)


def create_refresh_token(sub: str) -> str:
    payload = {SUB: sub, TYPE: REFRESH, EXP: _now() + REFRESH_EXP}
    return jwt.encode(payload, SECRET, algorithm=ALG)


def decode_token(token: str) -> Optional[dict[str, Any]]:
    try:
        return jwt.decode(token, SECRET, algorithms=[ALG])
    except JWTError:
        return None


def validate_access_token(token: str) -> Optional[dict[str, Any]]:
    data = decode_token(token)
    if not data or data.get(TYPE) != ACCESS or not data.get(SUB):
        return None
    return data


def validate_refresh_token(token: str) -> Optional[str]:
    data = decode_token(token)
    if not data or data.get(TYPE) != REFRESH:
        return None
    return data.get(SUB)
