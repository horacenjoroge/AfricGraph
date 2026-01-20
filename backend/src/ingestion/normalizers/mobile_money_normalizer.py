"""Normalizer for mobile money (NormalizedTransaction -> CanonicalTransaction)."""
from typing import List

from ..mobile_money.models import NormalizedTransaction
from ..utils.phone import normalize_phone
from .base import BaseNormalizer
from .canonical import CanonicalTransaction


class MobileMoneyNormalizer(BaseNormalizer):
    def normalize(self, t: NormalizedTransaction) -> CanonicalTransaction:
        amt_orig = t.amount
        ccy_orig = (t.currency or "KES").upper()
        amt = self._converter.convert(amt_orig, ccy_orig, self._target_currency)

        counterparty_phone: Optional[str] = None
        if t.counterparty and any(c.isdigit() for c in t.counterparty):
            counterparty_phone = normalize_phone(t.counterparty)

        return CanonicalTransaction(
            source_id=f"{t.provider}:{t.provider_txn_id or t.raw_row_index}",
            source_provider=t.provider,
            date=t.date,
            amount=amt,
            currency=self._target_currency,
            amount_original=amt_orig,
            currency_original=ccy_orig,
            type=t.type.value if hasattr(t.type, "value") else str(t.type),
            description=t.description or "",
            counterparty=t.counterparty,
            counterparty_raw=t.counterparty,
            counterparty_phone=counterparty_phone,
            raw={},
        )

    def normalize_many(self, items: List[NormalizedTransaction]) -> List[CanonicalTransaction]:
        return [self.normalize(t) for t in items]
