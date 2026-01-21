"""Cash flow forecasting over the next 3-6 months."""
from __future__ import annotations

from typing import List

from .models import CashflowForecast, MonthlyCashflow


def _linear_forecast(series: List[MonthlyCashflow], horizon_months: int) -> List[MonthlyCashflow]:
    """Very simple linear forecast based on net cashflow trend."""
    if not series:
        return []
    nets = [m.net for m in series]
    n = len(nets)
    # Fit line y = a*x + b on indices 0..n-1 (least squares).
    xs = list(range(n))
    sum_x = sum(xs)
    sum_y = sum(nets)
    sum_xx = sum(x * x for x in xs)
    sum_xy = sum(x * y for x, y in zip(xs, nets))
    denom = n * sum_xx - sum_x * sum_x
    if denom == 0:
        a = 0.0
        b = nets[-1]
    else:
        a = (n * sum_xy - sum_x * sum_y) / denom
        b = (sum_y - a * sum_x) / n

    last_month = series[-1].month
    forecast: List[MonthlyCashflow] = []
    for i in range(1, horizon_months + 1):
        idx = n - 1 + i
        net = a * idx + b
        # Approximate inflow/outflow split from last observed month.
        last = series[-1]
        ratio = 0.0
        if last.net != 0:
            ratio = last.inflow / last.net if last.net > 0 else last.outflow / -last.net
        inflow = net * ratio if net > 0 else 0.0
        outflow = -net if net < 0 else 0.0
        # Advance month (naive: add 30 days per month).
        month = last_month + i * (last_month.replace(day=28) - last_month.replace(day=1))
        forecast.append(MonthlyCashflow(month=month, inflow=inflow, outflow=outflow, net=net))
    return forecast


def forecast_cashflow(business_id: str, series: List[MonthlyCashflow], horizon_months: int = 6) -> CashflowForecast:
    """Produce a 3–6 month cashflow forecast based on historical monthly series."""
    horizon = max(3, min(6, horizon_months))
    projected = _linear_forecast(series, horizon)
    return CashflowForecast(
        business_id=business_id,
        horizon_months=horizon,
        projected_months=projected,
    )

