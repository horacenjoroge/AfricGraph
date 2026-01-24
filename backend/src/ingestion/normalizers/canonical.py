"""Canonical (standardized) models after normalization."""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, Optional


@dataclass
class CanonicalContact:
    source_id: str
    source_provider: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    phone_raw: Optional[str] = None
    address: Optional[Dict[str, Optional[str]]] = None
    address_raw: Optional[str] = None
    resolved_entity_id: Optional[str] = None
    updated_at: Optional[datetime] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonicalTransaction:
    source_id: str
    source_provider: str
    date: date
    amount: float
    currency: str
    amount_original: float
    currency_original: str
    type: str
    description: str
    counterparty: Optional[str] = None
    counterparty_raw: Optional[str] = None
    counterparty_phone: Optional[str] = None
    resolved_counterparty_entity_id: Optional[str] = None
    balance_after: Optional[float] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonicalInvoice:
    source_id: str
    source_provider: str
    number: str
    amount: float
    currency: str
    amount_original: float
    currency_original: str
    issue_date: date
    status: str
    due_date: Optional[date] = None
    contact_source_id: Optional[str] = None
    resolved_contact_entity_id: Optional[str] = None
    updated_at: Optional[datetime] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonicalPayment:
    source_id: str
    source_provider: str
    date: date
    amount: float
    currency: str
    amount_original: float
    currency_original: str
    invoice_source_id: Optional[str] = None
    reference: Optional[str] = None
    resolved_invoice_entity_id: Optional[str] = None
    updated_at: Optional[datetime] = None
    raw: Dict[str, Any] = field(default_factory=dict)
