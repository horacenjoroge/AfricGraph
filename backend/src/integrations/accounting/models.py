"""Provider-agnostic sync models for invoices, payments, contacts."""
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, Optional


class ConflictResolution(str, Enum):
    REMOTE_WINS = "remote_wins"
    LOCAL_WINS = "local_wins"
    NEWEST_WINS = "newest_wins"
    MANUAL = "manual"


class ExternalContact:
    """Contact/customer from an accounting provider."""

    def __init__(
        self,
        external_id: str,
        name: str,
        provider: str,
        email: Optional[str] = None,
        updated_at: Optional[datetime] = None,
        raw: Optional[Dict[str, Any]] = None,
    ):
        self.external_id = external_id
        self.name = name
        self.provider = provider
        self.email = email
        self.updated_at = updated_at
        self.raw = raw or {}


class ExternalInvoice:
    """Invoice from an accounting provider."""

    def __init__(
        self,
        external_id: str,
        number: str,
        amount: float,
        currency: str,
        issue_date: date,
        status: str,
        provider: str,
        contact_external_id: Optional[str] = None,
        due_date: Optional[date] = None,
        updated_at: Optional[datetime] = None,
        raw: Optional[Dict[str, Any]] = None,
    ):
        self.external_id = external_id
        self.number = number
        self.amount = amount
        self.currency = currency.upper()
        self.issue_date = issue_date
        self.status = status
        self.provider = provider
        self.contact_external_id = contact_external_id
        self.due_date = due_date
        self.updated_at = updated_at
        self.raw = raw or {}


class ExternalPayment:
    """Payment from an accounting provider."""

    def __init__(
        self,
        external_id: str,
        amount: float,
        currency: str,
        date: date,
        provider: str,
        invoice_external_id: Optional[str] = None,
        reference: Optional[str] = None,
        updated_at: Optional[datetime] = None,
        raw: Optional[Dict[str, Any]] = None,
    ):
        self.external_id = external_id
        self.amount = amount
        self.currency = currency.upper()
        self.date = date
        self.provider = provider
        self.invoice_external_id = invoice_external_id
        self.reference = reference
        self.updated_at = updated_at
        self.raw = raw or {}
