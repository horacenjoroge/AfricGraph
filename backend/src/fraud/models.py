"""Models for fraud alerts and patterns."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FraudPatternHit:
    pattern: str
    description: str
    business_id: Optional[str]
    score_contribution: float
    context: Dict[str, Any]


@dataclass
class FraudAlert:
    id: Optional[int]
    business_id: str
    pattern: str
    severity: AlertSeverity
    score: float
    description: str
    created_at: datetime
    is_false_positive: bool = False
    status: str = "open"  # open|in_review|closed
    metadata: Optional[Dict[str, Any]] = None

