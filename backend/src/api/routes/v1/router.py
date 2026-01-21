"""API v1 router combining all v1 endpoints."""
from fastapi import APIRouter

from . import audit, businesses, relationships

# Import existing routers that should be under v1
from ...routes import ingestion, risk, fraud, workflows

v1_router = APIRouter(prefix="/api/v1")

# Include all v1 endpoints
v1_router.include_router(businesses.router)
v1_router.include_router(ingestion.router, prefix="/ingest")
v1_router.include_router(risk.router, prefix="/risk")
v1_router.include_router(fraud.router, prefix="/fraud")
v1_router.include_router(workflows.router, prefix="/workflows")
v1_router.include_router(audit.router)
v1_router.include_router(relationships.router)
