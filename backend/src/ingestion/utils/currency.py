"""Currency conversion. In-memory rate table; replace with API in production."""
from typing import Dict, Optional

# Base rates to USD (as of placeholder; update or load from config/API).
_DEFAULT_RATES: Dict[str, float] = {
    "USD": 1.0,
    "KES": 0.0077,
    "UGX": 0.00027,
    "TZS": 0.00039,
    "GHS": 0.065,
    "NGN": 0.00062,
    "ZAR": 0.055,
    "EUR": 1.08,
    "GBP": 1.27,
}


class CurrencyConverter:
    def __init__(self, rates: Optional[Dict[str, float]] = None, target: str = "USD"):
        self._rates = dict(rates or _DEFAULT_RATES)
        self._target = target.upper()

    def convert(self, amount: float, from_currency: str, to_currency: Optional[str] = None) -> float:
        to = (to_currency or self._target).upper()
        fr = from_currency.upper() if from_currency else "USD"
        if fr == to:
            return amount
        r_from = self._rates.get(fr)
        r_to = self._rates.get(to)
        if r_from is None or r_to is None:
            return amount
        return amount * r_to / r_from
