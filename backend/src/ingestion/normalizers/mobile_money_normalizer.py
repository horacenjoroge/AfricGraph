"""Normalizer for mobile money (NormalizedTransaction -> CanonicalTransaction)."""
from typing import List, Optional

from ..mobile_money.models import NormalizedTransaction
from ..mobile_money.counterparty import extract_counterparty_with_phone
from ..utils.phone import normalize_phone
from .base import BaseNormalizer
from .canonical import CanonicalTransaction


class MobileMoneyNormalizer(BaseNormalizer):
    def normalize(self, t: NormalizedTransaction) -> CanonicalTransaction:
        amt_orig = t.amount
        ccy_orig = (t.currency or "KES").upper()
        # Keep original currency and amount - don't convert to USD
        amt = amt_orig

        # Enhanced counterparty extraction
        counterparty_name, counterparty_phone_raw, direction = extract_counterparty_with_phone(t.description)
        
        # Use extracted values or fall back to existing counterparty
        final_name = counterparty_name or t.counterparty
        final_phone = None
        if counterparty_phone_raw:
            final_phone = normalize_phone(counterparty_phone_raw)
        elif t.counterparty and any(c.isdigit() for c in t.counterparty):
            final_phone = normalize_phone(t.counterparty)

        return CanonicalTransaction(
            source_id=f"{t.provider}:{t.provider_txn_id or t.raw_row_index}",
            source_provider=t.provider,
            date=t.date,
            amount=amt,  # Keep original amount
            currency=ccy_orig,  # Keep original currency (KES)
            amount_original=amt_orig,
            currency_original=ccy_orig,
            type=t.type.value if hasattr(t.type, "value") else str(t.type),
            description=t.description or "",
            counterparty=final_name,
            counterparty_raw=t.counterparty,
            counterparty_phone=final_phone,
            balance_after=t.balance_after,  # Pass through balance_after
            raw={"direction": direction},  # Store direction
        )

    def normalize_many(self, items: List[NormalizedTransaction]) -> List[CanonicalTransaction]:
        return [self.normalize(t) for t in items]
