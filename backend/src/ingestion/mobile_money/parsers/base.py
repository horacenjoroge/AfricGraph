"""Base CSV parser for mobile money statements."""
import csv
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, Optional, Tuple, Union

from src.infrastructure.logging import get_logger

from ..models import RawRow

logger = get_logger(__name__)


def _norm_key(s: str) -> str:
    return s.strip().lower().replace(" ", "_").replace(".", "")


def _find_column(row: dict, *candidates: str) -> str:
    keys = {_norm_key(k): k for k in row}
    for c in candidates:
        n = _norm_key(c)
        if n in keys:
            return row[keys[n]]
    return ""


class BaseParser(ABC):
    """Abstract parser. Reads CSV and yields RawRow. Handles corrupted rows by skipping and reporting."""

    provider: str = ""

    def __init__(self, default_currency: str = "KES"):
        self.default_currency = default_currency

    def _read_rows(
        self, path: Union[str, Path]
    ) -> Iterator[Tuple[int, dict]]:
        p = Path(path)
        with p.open("r", encoding="utf-8", errors="replace") as f:
            try:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if not any(v and str(v).strip() for v in row.values()):
                        continue
                    yield i + 2, row
            except csv.Error as e:
                logger.warning("CSV read error", path=str(p), error=str(e))
                raise

    @abstractmethod
    def _row_to_raw(self, row: dict, row_index: int) -> RawRow:
        pass

    def parse(
        self, path: Union[str, Path]
    ) -> Iterator[Tuple[RawRow, Optional[str]]]:
        """Yields (RawRow, error). error is None on success. On row parse error, yields (RawRow with raw dict, str)."""
        for row_index, row in self._read_rows(path):
            try:
                r = self._row_to_raw(row, row_index)
                r.provider = self.provider
                yield r, None
            except Exception as e:
                logger.debug("Row parse error", row_index=row_index, error=str(e))
                yield RawRow(provider=self.provider, row_index=row_index, raw=dict(row)), str(e)
