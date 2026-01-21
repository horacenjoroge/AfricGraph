"""Data models for risk scoring."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class FactorScore:
    name: str
    score: float  # 0-100
    details: Dict


@dataclass
class RiskScoreResult:
    business_id: str
    total_score: float  # 0-100
    factors: Dict[str, FactorScore]
    generated_at: datetime
    explanation: str

