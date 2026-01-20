"""Airtel Money statement CSV parser."""
from ..models import RawRow
from .base import BaseParser, _find_column


class AirtelParser(BaseParser):
    """Parser for Airtel Money CSV: Date, Description, Credit, Debit, Balance, Reference."""

    provider = "airtel"

    def _row_to_raw(self, row: dict, row_index: int) -> RawRow:
        receipt_no = _find_column(row, "Reference", "Ref", "Transaction ID", "Receipt No", "Receipt Number") or None
        completion_time = _find_column(row, "Date", "Transaction Date", "Completion Time", "DateTime", "Time") or None
        details = _find_column(row, "Description", "Details", "Narration", "Particulars", "Transaction Type") or None
        status = _find_column(row, "Status", "Transaction Status") or None
        paid_in = _find_column(row, "Credit", "Amount In", "Paid In", "Deposit", "Received") or None
        withdrawn = _find_column(row, "Debit", "Amount Out", "Withdrawn", "Withdrawal", "Sent") or None
        balance = _find_column(row, "Balance", "Running Balance", "Account Balance") or None

        return RawRow(
            receipt_no=receipt_no if receipt_no else None,
            completion_time=completion_time if completion_time else None,
            details=details if details else None,
            status=status if status else None,
            paid_in=paid_in if paid_in else None,
            withdrawn=withdrawn if withdrawn else None,
            balance=balance if balance else None,
            provider=self.provider,
            row_index=row_index,
            raw=dict(row),
        )
