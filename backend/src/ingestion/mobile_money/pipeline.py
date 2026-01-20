"""Pipeline: parse CSV -> classify -> counterparty -> amount -> validate -> dedup."""
from pathlib import Path
from typing import List, Optional, Set, Tuple, Union

from .amount import normalize_amount
from .classifier import classify
from .counterparty import extract_counterparty
from .duplicate import content_hash, filter_duplicates
from .models import NormalizedTransaction, RawRow, TransactionType
from .parsers.airtel import AirtelParser
from .parsers.mpesa import MpesaParser
from .validation import parse_completion_time, validate


def _parse_balance(s: Optional[str]) -> Optional[float]:
    if not s or not str(s).strip():
        return None
    t = str(s).strip().replace(",", "")
    try:
        return float(t)
    except ValueError:
        return None


_PARSERS = {"mpesa": MpesaParser, "airtel": AirtelParser}


def run(
    path: Union[str, Path],
    provider: str,
    default_currency: str = "KES",
    seen_hashes: Optional[Set[str]] = None,
) -> Tuple[List[NormalizedTransaction], List[dict]]:
    """
    Returns (valid_normalized, invalid). invalid entries: {row_index, errors: [...]}.
    seen_hashes: optional set of content hashes to treat as duplicates (e.g. from DB); updated with new hashes.
    """
    P = _PARSERS.get(provider.lower())
    if not P:
        raise ValueError(f"unknown provider: {provider}. supported: mpesa, airtel")
    parser = P(default_currency=default_currency)

    valid: List[NormalizedTransaction] = []
    invalid: List[dict] = []
    file_seen: Set[str] = set(seen_hashes) if seen_hashes is not None else set()

    for raw, parse_err in parser.parse(path):
        if parse_err:
            invalid.append({"row_index": raw.row_index, "errors": [parse_err]})
            continue

        dt = parse_completion_time(raw.completion_time)
        if dt is None and raw.completion_time:
            invalid.append({"row_index": raw.row_index, "errors": ["invalid date format"]})
            continue
        if dt is None:
            invalid.append({"row_index": raw.row_index, "errors": ["missing date"]})
            continue

        amount, is_in = normalize_amount(raw.paid_in, raw.withdrawn)
        txn_type = classify(raw, is_in)
        desc = (raw.details or "").strip()
        cp = extract_counterparty(raw.details)
        balance = _parse_balance(raw.balance)

        h = content_hash(
            provider=parser.provider,
            provider_txn_id=raw.receipt_no,
            txn_date=dt,
            amount=amount,
            description=desc,
        )
        uniq, file_seen = filter_duplicates([h], file_seen)
        if not uniq:
            continue

        nt = NormalizedTransaction(
            date=dt,
            amount=amount,
            currency=parser.default_currency,
            type=txn_type,
            description=desc or "(no description)",
            counterparty=cp,
            provider=parser.provider,
            provider_txn_id=raw.receipt_no,
            balance_after=balance,
            content_hash=h,
            raw_row_index=raw.row_index,
        )
        verrs = validate(nt)
        if verrs:
            invalid.append({"row_index": raw.row_index, "errors": verrs})
            continue
        valid.append(nt)

    if seen_hashes is not None:
        seen_hashes.update(file_seen)
    return (valid, invalid)
