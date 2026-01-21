"""Cash flow trend and seasonality analysis."""
from __future__ import annotations

from typing import List

from .models import MonthlyCashflow


def detect_negative_trend(series: List[MonthlyCashflow]) -> bool:
    """Simple trend: compare average of first half vs last half of series."""
    if len(series) < 4:
        return False
    nets = [m.net for m in series]
    mid = len(nets) // 2
    first_avg = sum(nets[:mid]) / max(1, mid)
    last_avg = sum(nets[mid:]) / max(1, len(nets) - mid)
    return last_avg < first_avg * 0.8  # drop > 20%


def detect_seasonality(series: List[MonthlyCashflow]) -> bool:
    """
    Very simple seasonal pattern detection:
      - Checks variance of month-of-year averages; high variance suggests seasonality.
    """
    if len(series) < 12:
        return False
    by_month = {}
    for m in series:
        key = m.month.month  # 1-12
        by_month.setdefault(key, []).append(m.net)
    avgs = [sum(vals) / len(vals) for vals in by_month.values() if vals]
    if len(avgs) < 2:
        return False
    overall = sum(avgs) / len(avgs)
    if overall == 0:
        return False
    var = sum((a - overall) ** 2 for a in avgs) / len(avgs)
    # Heuristic: large variance relative to mean -> seasonality.
    return var > abs(overall) ** 2

