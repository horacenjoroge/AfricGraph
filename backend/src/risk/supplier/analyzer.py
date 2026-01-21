"""High-level supplier risk analysis for a business."""
from __future__ import annotations

from typing import Dict, List

from src.infrastructure.logging import get_logger

from .concentration import compute_supplier_concentration
from .dependency_graph import build_supplier_dependency_graph
from .health import classify_supplier_health, suggest_alternative_suppliers
from .late_payments import compute_late_payment_stats
from .shared_directors import find_shared_directors

logger = get_logger(__name__)


def analyze_supplier_risk(business_id: str) -> Dict[str, object]:
    """
    Analyze supplier-related risks for a business.

    Returns a JSON-serializable structure including:
      - concentration metrics
      - shared director hits
      - late payment stats + health labels
      - alternative supplier suggestions
      - a small dependency graph for visualization
    """
    concentration = compute_supplier_concentration(business_id)
    shared_directors = find_shared_directors(business_id)
    late_stats = compute_late_payment_stats(business_id)
    health = classify_supplier_health(late_stats)
    alternatives = suggest_alternative_suppliers(business_id)
    graph = build_supplier_dependency_graph(business_id)

    return {
        "business_id": business_id,
        "concentration": concentration,
        "shared_directors": shared_directors,
        "late_payments": late_stats,
        "supplier_health": health,
        "alternative_suppliers": alternatives,
        "dependency_graph": graph,
    }

