"""M-Pesa (Safaricom) statement CSV parser."""
from ..models import RawRow
from .base import BaseParser, _find_column


class MpesaParser(BaseParser):
    """Parser for M-Pesa CSV: Receipt No, Completion Time, Details, Transaction Status, Paid In, Withdrawn, Balance."""

    provider = "mpesa"

    def _row_to_raw(self, row: dict, row_index: int) -> RawRow:
        receipt_no = _find_column(row, "Receipt No", "Receipt No.", "Receipt", "Transaction ID", "Receipt Number") or None
        completion_time = _find_column(row, "Completion Time", "Date", "Completion Time ", "Time") or None
        details = _find_column(row, "Details", "Description", "Narration", "Particulars") or None
        status = _find_column(row, "Transaction Status", "Status", "Transaction Status ") or None
        paid_in = _find_column(row, "Paid In", "Credit", "Amount Received", "Deposit") or None
        withdrawn = _find_column(row, "Withdrawn", "Debit", "Amount Sent", "Withdrawal") or None
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
