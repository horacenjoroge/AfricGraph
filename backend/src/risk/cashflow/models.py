"""Models for cash flow health and forecasts."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List


@dataclass
class MonthlyCashflow:
    month: date
    inflow: float
    outflow: float
    net: float


@dataclass
class CashHealthSummary:
    business_id: str
    health_score: float  # 0-100
    burn_rate: float     # negative net per month (absolute value)
    runway_months: float
    has_negative_trend: bool
    series: List[MonthlyCashflow]


@dataclass
class CashflowForecast:
    business_id: str
    horizon_months: int
    projected_months: List[MonthlyCashflow]

