"""Duplicate detection: fuzzy name (Levenshtein), phone, address similarity, composite score."""
from typing import Any, Dict, Optional

from src.ingestion.utils.address import parse_address
from src.ingestion.utils.fuzzy_match import similarity as _fuzzy_similarity
from src.ingestion.utils.phone import normalize_phone


def name_similarity(a: Optional[str], b: Optional[str]) -> float:
    """Levenshtein-based similarity; 1.0 identical, 0.0 no match."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return _fuzzy_similarity(str(a).strip(), str(b).strip())


def phone_match(phone_a: Optional[str], phone_b: Optional[str]) -> bool:
    """True if both normalize to the same non-empty string."""
    na = normalize_phone(phone_a)
    nb = normalize_phone(phone_b)
    if not na or not nb:
        return False
    return na == nb


def address_similarity(
    addr_a: Optional[str],
    addr_b: Optional[str],
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    Weighted similarity from parsed components: country (exact), city, street.
    Falls back to string similarity on raw if parsing yields little.
    """
    w = weights or {"country": 0.5, "city": 0.3, "street": 0.2}
    if not addr_a and not addr_b:
        return 1.0
    if not addr_a or not addr_b:
        return 0.0
    sa = str(addr_a).strip()
    sb = str(addr_b).strip()
    if not sa or not sb:
        return 0.0
    pa = parse_address(sa)
    pb = parse_address(sb)
    score = 0.0
    ca, cb = (pa.get("country") or "").strip().upper(), (pb.get("country") or "").strip().upper()
    if ca and cb:
        score += w.get("country", 0.5) * (1.0 if ca == cb else 0.0)
    cita, citb = (pa.get("city") or "").strip(), (pb.get("city") or "").strip()
    if cita or citb:
        score += w.get("city", 0.3) * _fuzzy_similarity(cita, citb)
    stra, strb = (pa.get("street") or "").strip(), (pb.get("street") or "").strip()
    if stra or strb:
        score += w.get("street", 0.2) * _fuzzy_similarity(stra, strb)
    if score == 0.0 and (sa or sb):
        return _fuzzy_similarity(sa, sb)
    return min(1.0, score)


def composite_similarity(
    name_a: Optional[str],
    name_b: Optional[str],
    phone_a: Optional[str] = None,
    phone_b: Optional[str] = None,
    addr_a: Optional[str] = None,
    addr_b: Optional[str] = None,
    weights: Optional[Dict[str, float]] = None,
) -> tuple:
    """
    Combined score and reasons. Weights: name, phone, address (default 0.5, 0.35, 0.15).
    Phone: 1.0 if match, 0.0 if either missing or no match.
    """
    w = weights or {"name": 0.5, "phone": 0.35, "address": 0.15}
    reasons: Dict[str, Any] = {}
    ns = name_similarity(name_a, name_b)
    reasons["name"] = round(ns, 4)
    ph = 1.0 if phone_match(phone_a, phone_b) else 0.0
    reasons["phone"] = 1 if ph else 0
    as_ = address_similarity(addr_a, addr_b)
    reasons["address"] = round(as_, 4)
    have_ph = (phone_a and str(phone_a).strip()) and (phone_b and str(phone_b).strip())
    have_addr = (addr_a and str(addr_a).strip()) and (addr_b and str(addr_b).strip())
    total_w = w["name"]
    score = w["name"] * ns
    if have_ph:
        total_w += w["phone"]
        score += w["phone"] * ph
    if have_addr:
        total_w += w["address"]
        score += w["address"] * as_
    if total_w > 0:
        score = score / total_w
    return (round(min(1.0, score), 4), reasons)
