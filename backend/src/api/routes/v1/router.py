"""API v1 router combining all v1 endpoints."""
from fastapi import APIRouter

from . import audit, businesses, relationships

# Import existing routers that should be under v1
from ...routes import anomaly, cache, ingestion, risk, fraud, workflows, ml, search, graph

v1_router = APIRouter(prefix="/api/v1")

# Include all v1 endpoints
v1_router.include_router(businesses.router)
# Note: ingestion router has prefix="/ingestion", but task requires /ingest
# We'll include it with override prefix
v1_router.include_router(ingestion.router, prefix="/ingest")
v1_router.include_router(risk.router)
v1_router.include_router(fraud.router)
v1_router.include_router(workflows.router)
v1_router.include_router(audit.router)
v1_router.include_router(relationships.router)
v1_router.include_router(ml.router)
v1_router.include_router(anomaly.router)
v1_router.include_router(cache.router)
v1_router.include_router(search.router)
# Include graph router under v1 - graph router already has /graph prefix
# This will make it /api/v1/graph/...
from ...routes.graph import router as graph_router
v1_router.include_router(graph_router)