# pyright: reportMissingImports=false
"""FastAPI application entry point."""
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.config.settings import settings
from src.infrastructure.logging import configure_logging, get_logger
from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.cache.redis_client import redis_client
from src.infrastructure.queue.rabbitmq_client import rabbitmq_client
from src.infrastructure.search.elasticsearch_client import elasticsearch_client
from src.infrastructure.audit import audit_logger
from src.infrastructure.audit.middleware import AuditMiddleware
from fastapi.exceptions import RequestValidationError

from src.api.routes import alerts, auth, backup, deduplication, graph, metrics, temporal, tenancy, tenancy
from src.api.routes.v1.router import v1_router
from src.graphql.router import graphql_router
from src.monitoring.middleware import MetricsMiddleware
from src.monitoring.system import system_metrics_collector
from src.api.utils.errors import (
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from src.api.utils.rate_limit import RateLimitMiddleware
from src.alerts.engine import initialize_rules
from src.alerts.persistence import ensure_alerts_table
from src.auth.service import ensure_users_table
from src.deduplication.merge_history import ensure_merge_history_table
from src.ingestion.pipeline.job_store import ensure_ingestion_jobs_table
from src.security.abac import PermissionContextMiddleware
from src.tenancy.middleware import TenantMiddleware

# Configure logging
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""
    # Startup
    logger.info("Starting AfricGraph application")
    try:
        neo4j_client.connect()
        postgres_client.connect()
        redis_client.connect()
        rabbitmq_client.connect()
        elasticsearch_client.connect()
        audit_logger.ensure_audit_table()
        ensure_users_table()
        ensure_ingestion_jobs_table()
        ensure_merge_history_table()
        ensure_alerts_table()
        initialize_rules()
        
        # Start system metrics collection
        system_metrics_collector.start()
        
        logger.info("All services connected successfully")
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AfricGraph application")
    
    # Stop system metrics collection
    system_metrics_collector.stop()
    
    neo4j_client.close()
    postgres_client.close()
    redis_client.close()
    rabbitmq_client.close()
    elasticsearch_client.close()
    logger.info("All services disconnected")


# Create FastAPI app with OpenAPI configuration
app = FastAPI(
    title="AfricGraph API",
    description="Ontology-Driven Decision Platform for SMEs",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# Add tenant middleware (before other middleware to set context)
app.add_middleware(TenantMiddleware)

# Add metrics middleware (before other middleware to capture all requests)
app.add_middleware(MetricsMiddleware)

# Add security and audit middleware
app.add_middleware(PermissionContextMiddleware)
app.add_middleware(AuditMiddleware)

# Register error handlers
from fastapi import HTTPException

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include v1 API router (comprehensive REST API)
app.include_router(v1_router)

# Include GraphQL router
app.include_router(graphql_router, prefix="/graphql")

# Include metrics endpoint (Prometheus)
app.include_router(metrics.router)

# Include legacy/unversioned routers (for backward compatibility)
app.include_router(auth.router)
app.include_router(deduplication.router)
app.include_router(alerts.router)
app.include_router(graph.router)
app.include_router(backup.router)
app.include_router(temporal.router)
app.include_router(tenancy.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AfricGraph API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for all services."""
    return {
        "status": "healthy",
        "services": {
            "neo4j": neo4j_client.health_check(),
            "postgres": postgres_client.health_check(),
            "redis": redis_client.health_check(),
            "rabbitmq": rabbitmq_client.health_check(),
            "elasticsearch": elasticsearch_client.health_check(),
        }
    }
