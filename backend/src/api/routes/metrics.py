"""Prometheus metrics endpoint."""
from fastapi import APIRouter, Response

from src.monitoring.metrics import get_metrics, get_metrics_content_type

router = APIRouter(prefix="/metrics", tags=["monitoring"])


@router.get("")
def metrics_endpoint():
    """Prometheus metrics endpoint."""
    return Response(
        content=get_metrics(),
        media_type=get_metrics_content_type(),
    )
