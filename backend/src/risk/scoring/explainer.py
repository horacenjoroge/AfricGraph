"""Risk explanation generator."""
from __future__ import annotations

from typing import List

from .models import RiskScoreResult


def build_explanation(result: RiskScoreResult) -> str:
    """Generate a human-readable explanation from factor scores."""
    parts: List[str] = []
    f = result.factors

    def fmt(name: str, label: str) -> None:
        if name in f:
            parts.append(f"{label}: {f[name].score:.1f}/100")

    fmt("payment_behavior", "Payment behavior")
    fmt("supplier_concentration", "Supplier concentration")
    fmt("ownership_complexity", "Ownership structure")
    fmt("cashflow_health", "Cash flow health")
    fmt("network_exposure", "Network exposure")

    summary = f"Composite risk score {result.total_score:.1f}/100."
    if parts:
        summary += " Factors -> " + "; ".join(parts) + "."
    return summary

