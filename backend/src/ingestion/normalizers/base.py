"""Base normalizer interface."""
from abc import ABC
from typing import Optional

from src.config.settings import settings

from ..utils.currency import CurrencyConverter


class BaseNormalizer(ABC):
    def __init__(
        self,
        target_currency: Optional[str] = None,
        currency_converter: Optional[CurrencyConverter] = None,
    ):
        self._target_currency = (target_currency or getattr(settings, "normalization_target_currency", "USD")).upper()
        self._converter = currency_converter or CurrencyConverter(target=self._target_currency)
