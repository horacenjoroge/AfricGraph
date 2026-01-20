"""Models for mobile money connector."""
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, Optional


class TransactionType(str, Enum):
    PAYMENT_IN = "payment_in"
    PAYMENT_OUT = "payment_out"
    MERCHANT = "merchant"
    WITHDRAWAL = "withdrawal"


@dataclass
class RawRow:
    """Row as emitted by a CSV parser, before classification and normalization."""

    receipt_no: Optional[str] = None
    completion_time: Optional[str] = None
    details: Optional[str] = None
    status: Optional[str] = None
    paid_in: Optional[str] = None
    withdrawn: Optional[str] = None
    balance: Optional[str] = None
    provider: str = ""
    row_index: int = 0
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedTransaction:
    """Fully processed transaction: classified, counterparty extracted, amount normalized, validated."""

    date: date
    amount: float
    currency: str
    type: TransactionType
    description: str
    counterparty: Optional[str] = None
    provider: str = ""
    provider_txn_id: Optional[str] = None
    balance_after: Optional[float] = None
    content_hash: Optional[str] = None
    raw_row_index: int = 0
