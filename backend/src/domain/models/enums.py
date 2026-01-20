"""Enum types for entity status and classification fields."""
from enum import Enum


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    SENT = "sent"
    PAID = "paid"
    PARTIAL = "partial"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class LoanStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    REPAID = "repaid"
    DEFAULTED = "defaulted"
    CANCELLED = "cancelled"


class AssetType(str, Enum):
    EQUIPMENT = "equipment"
    PROPERTY = "property"
    INVENTORY = "inventory"
    VEHICLE = "vehicle"
    INTANGIBLE = "intangible"
    OTHER = "other"


class TransactionType(str, Enum):
    CREDIT = "credit"
    DEBIT = "debit"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    REFUND = "refund"
    OTHER = "other"
